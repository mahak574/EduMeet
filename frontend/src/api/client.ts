import { APIResponse } from '../types';

const API_BASE = '/api/v1';

let accessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;

export const setAccessToken = (token: string | null) => {
  accessToken = token;
};

export const getAccessToken = () => accessToken;

async function executeTokenRefresh(): Promise<string | null> {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const refreshResp = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });

      if (refreshResp.ok) {
        const refreshData: APIResponse<{ access_token: string }> = await refreshResp.json();
        const newToken = refreshData.data?.access_token || null;
        setAccessToken(newToken);
        return newToken;
      } else {
        setAccessToken(null);
        return null;
      }
    } catch {
      setAccessToken(null);
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

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

  // If unauthorized (401), attempt token refresh using single shared in-flight promise
  if (response.status === 401 && !endpoint.includes('/auth/')) {
    const newToken = await executeTokenRefresh();
    if (newToken) {
      headers.set('Authorization', `Bearer ${newToken}`);
      response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
        credentials: 'include',
      });
    }
  }

  let json: any = null;
  try {
    json = await response.json();
  } catch {
    json = null;
  }

  if (!response.ok || (json && json.success === false)) {
    const errorMsg =
      json?.detail ||
      json?.error?.message ||
      json?.message ||
      (response.status === 401
        ? 'Please log in to your account first.'
        : response.status === 403
        ? 'You do not have permission to perform this action.'
        : response.status === 404
        ? 'The requested resource was not found.'
        : `Request failed with status ${response.status}`);

    const error = new Error(errorMsg);
    (error as any).status = response.status;
    (error as any).detail = json?.detail;
    throw error;
  }

  return (json?.data !== undefined ? json.data : json) as T;
}
