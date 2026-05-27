import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    auth_burst: {
      executor: 'constant-vus',
      vus: 20,
      duration: '30s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<750'],
    http_req_failed: ['rate<0.50'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const payload = JSON.stringify({
    email: `load-${__VU}-${__ITER}@example.com`,
    password: 'invalid-password',
  });
  const res = http.post(`${BASE_URL}/api/auth/login`, payload, {
    headers: { 'Content-Type': 'application/json' },
  });
  check(res, {
    'auth protected by 401 or 429': (r) => [401, 422, 429].includes(r.status),
  });
  sleep(0.2);
}
