/* eslint-env jest */
jest.mock('../apiClient');

import apiClient from '../apiClient';
import * as api from '../api';

describe('api wrapper functions', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  test('vendors.getAll wraps apiClient.get and returns {data}', async () => {
    apiClient.get.mockResolvedValueOnce([{ id: 'v1', business_name: 'Test' }]);
    const res = await api.vendors.getAll({});
    expect(apiClient.get).toHaveBeenCalled();
    expect(res).toHaveProperty('data');
    expect(Array.isArray(res.data)).toBe(true);
    expect(res.data[0].business_name).toBe('Test');
  });

  test('auth.login returns data with access_token and user', async () => {
    const payload = { access_token: 'tok', user: { id: 'u1' } };
    apiClient.post.mockResolvedValueOnce(payload);
    const res = await api.auth.login({ email: 'a', password: 'b' });
    expect(apiClient.post).toHaveBeenCalledWith('/auth/login', { email: 'a', password: 'b' });
    expect(res).toHaveProperty('data');
    expect(res.data.access_token).toBe('tok');
  });
});
