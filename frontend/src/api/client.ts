import { APIResponse } from '../types';

const API_BASE = '/api/v1';

let accessToken: string | null = localStorage.getItem('edumeet_access_token');

export const setAccessToken = (token: string | null) => {
  accessToken = token;
  if (token) {
    localStorage.setItem('edumeet_access_token', token);
  } else {
    localStorage.removeItem('edumeet_access_token');
  }
};

export const getAccessToken = () => accessToken;

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');

  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'include', // Ensures httpOnly refresh cookie is sent
  };

  let response = await fetch(`${API_BASE}${endpoint}`, config);

  // If unauthorized (401), attempt token refresh using httpOnly cookie
  if (response.status === 401 && !endpoint.includes('/auth/')) {
    try {
      const refreshResp = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });

      if (refreshResp.ok) {
        const refreshData: APIResponse<{ access_token: string }> = await refreshResp.json();
        if (refreshData.data?.access_token) {
          setAccessToken(refreshData.data.access_token);
          headers.set('Authorization', `Bearer ${refreshData.data.access_token}`);
          // Retry initial request
          response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers,
            credentials: 'include',
          });
        }
      } else {
        // Refresh failed, clear access token
        setAccessToken(null);
      }
    } catch {
      setAccessToken(null);
    }
  }

  const json: APIResponse<T> = await response.json();

  if (!response.ok || !json.success) {
    throw new Error(json.error?.message || 'Request failed');
  }

  return json.data as T;
}
