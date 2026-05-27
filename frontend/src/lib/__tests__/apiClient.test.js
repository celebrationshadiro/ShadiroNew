/* eslint-env jest */
import apiClient from '../apiClient';

describe('apiClient', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
    localStorage.clear();
    // ensure window.location.href is writable
    delete window.location;
    // minimal location mock
    window.location = { href: '' };
  });

  test('GET returns parsed JSON', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ hello: 'world' }),
    });

    const res = await apiClient.get('/test');
    expect(res).toEqual({ hello: 'world' });
    expect(global.fetch).toHaveBeenCalled();
  });

  test('401 clears token and redirects to /auth', async () => {
    localStorage.setItem('token', 'abc');
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      text: async () => JSON.stringify({}),
      statusText: 'Unauthorized',
    });

    await expect(apiClient.get('/private')).rejects.toThrow('Unauthorized');
    expect(localStorage.getItem('token')).toBeNull();
    expect(window.location.href).toBe('/auth');
  });

  test('retries on network error and succeeds', async () => {
    // first call rejects, second returns success
    global.fetch
      .mockRejectedValueOnce(new Error('network'))
      .mockResolvedValueOnce({ ok: true, status: 200, text: async () => JSON.stringify({ ok: true }) });

    const res = await apiClient.get('/retry');
    expect(res).toEqual({ ok: true });
    expect(global.fetch).toHaveBeenCalledTimes(2);
  });
});
