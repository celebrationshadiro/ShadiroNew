const DEFAULT_RETRIES = 2;
const DEFAULT_TIMEOUT_MS = 15000;

class ApiClientError extends Error {
  constructor(message, { status = null, data = null, requestId = null } = {}) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.data = data;
    this.requestId = requestId;
    this.response = { data, status };
  }
}

function buildUrl(path) {
  const envApi = process.env.REACT_APP_API_URL;
  const backend = process.env.REACT_APP_BACKEND_URL;
  let base = envApi || (backend ? `${backend.replace(/\/$/, '')}/api` : 'http://localhost:8000/api');

  if (!path) return base;
  if (path.startsWith('http://') || path.startsWith('https://')) return path;

  if (base.endsWith('/api') && path.startsWith('/api')) {
    path = path.replace(/^\/api/, '');
  }

  if (path.startsWith('/')) return `${base}${path}`;
  return `${base}/${path}`;
}

function getAccessToken() {
  return localStorage.getItem('token') || localStorage.getItem('access_token');
}

function getRefreshToken() {
  return localStorage.getItem('refresh_token');
}

function setTokens({ access_token, refresh_token }) {
  if (access_token) {
    localStorage.setItem('token', access_token);
    localStorage.setItem('access_token', access_token);
  }
  if (refresh_token) localStorage.setItem('refresh_token', refresh_token);
}

function clearTokens() {
  localStorage.removeItem('token');
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

function requestId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
  return `req_${Date.now()}_${Math.random().toString(36).slice(2)}`;
}

async function parseResponse(response) {
  const text = await response.text();
  try {
    return JSON.parse(text || '{}');
  } catch (e) {
    return text;
  }
}

function normalizeDetail(detail) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || item?.message || JSON.stringify(item))
      .join(', ');
  }
  if (detail && typeof detail === 'object') {
    return detail.msg || detail.message || JSON.stringify(detail);
  }
  return '';
}

function getErrorMessage(data, response) {
  if (data?.message) return normalizeDetail(data.message);
  if (data?.detail) return normalizeDetail(data.detail);
  if (data?.error) return normalizeDetail(data.error);
  return response.statusText || 'Request failed';
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function createAbortSignal(externalSignal, timeoutMs) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(new Error('Request timed out')), timeoutMs);

  if (externalSignal) {
    if (externalSignal.aborted) controller.abort(externalSignal.reason);
    externalSignal.addEventListener('abort', () => controller.abort(externalSignal.reason), { once: true });
  }

  return {
    signal: controller.signal,
    cleanup: () => clearTimeout(timeout),
  };
}

function prepareRequestOptions(options = {}) {
  const {
    body,
    headers: inputHeaders,
    signal,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    _skipAuthRefresh,
    ...rest
  } = options;

  const headers = { ...(inputHeaders || {}) };
  const token = getAccessToken();
  if (token && !headers.Authorization) headers.Authorization = `Bearer ${token}`;
  if (!headers['X-Request-ID']) headers['X-Request-ID'] = requestId();

  let normalizedBody = body;
  if (body && typeof body === 'object' && !(body instanceof FormData)) {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    normalizedBody = JSON.stringify(body);
  }

  const abort = createAbortSignal(signal, timeoutMs);
  return {
    fetchOptions: { ...rest, body: normalizedBody, headers, signal: abort.signal },
    cleanup: abort.cleanup,
    skipAuthRefresh: Boolean(_skipAuthRefresh),
  };
}

let refreshPromise = null;

async function refreshAccessToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;
  if (!refreshPromise) {
    refreshPromise = request('/auth/refresh', {
      method: 'POST',
      body: { refresh_token: refreshToken },
      _skipAuthRefresh: true,
    })
      .then((res) => {
        const payload = res?.data || res || {};
        setTokens(payload);
        return payload.access_token || null;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

function redirectToLogin() {
  clearTokens();
  if (typeof window === 'undefined') return;
  const isAdminPath = typeof window.location?.pathname === 'string' && window.location.pathname.startsWith('/admin');
  window.location.href = isAdminPath ? '/admin/login' : '/auth';
}

async function executeFetch(path, options) {
  const url = buildUrl(path);
  const { fetchOptions, cleanup, skipAuthRefresh } = prepareRequestOptions(options);
  try {
    const response = await fetch(url, fetchOptions);
    const data = await parseResponse(response);

    if (response.status === 401 && !skipAuthRefresh) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        return executeFetch(path, { ...options, headers: { ...(options.headers || {}), Authorization: `Bearer ${refreshed}` }, _skipAuthRefresh: true });
      }
      redirectToLogin();
    }

    if (!response.ok) {
      if (data && data.detail && typeof data.detail !== 'string') {
        data.detail_raw = data.detail;
        data.detail = normalizeDetail(data.detail);
      }
      throw new ApiClientError(getErrorMessage(data, response), {
        status: response.status,
        data,
        requestId: response.headers.get('X-Request-ID') || data?.request_id,
      });
    }

    return data;
  } finally {
    cleanup();
  }
}

async function request(path, options = {}, retries = DEFAULT_RETRIES) {
  try {
    return await executeFetch(path, options);
  } catch (err) {
    const status = err?.status ?? err?.response?.status;
    const canRetry = err.name === 'AbortError' || !status || status >= 500 || status === 429;
    if (retries > 0 && canRetry) {
      const attempt = DEFAULT_RETRIES - retries + 1;
      const retryAfter = Number(err?.response?.data?.data?.retry_after_seconds || 0) * 1000;
      const backoff = retryAfter || Math.min(2000, 300 * 2 ** attempt) + Math.floor(Math.random() * 150);
      await sleep(backoff);
      return request(path, options, retries - 1);
    }
    if (!err.response) err.response = { data: err.data || null, status: err.status || null };
    throw err;
  }
}

const apiClient = {
  get: (path, opts) => request(path, { method: 'GET', ...opts }),
  post: (path, body, opts) => request(path, { method: 'POST', body, ...opts }),
  put: (path, body, opts) => request(path, { method: 'PUT', body, ...opts }),
  patch: (path, body, opts) => request(path, { method: 'PATCH', body, ...opts }),
  del: (path, body, opts) => request(path, { method: 'DELETE', body, ...opts }),
  request,
  setTokens,
  clearTokens,
};

export { ApiClientError, clearTokens, setTokens };
export default apiClient;
