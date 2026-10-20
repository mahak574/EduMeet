import { create } from 'zustand';
import { apiClient, setAccessToken } from '../api/client';
import { AuthTokenResponse, User } from '../types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  initAuth: () => Promise<void>;
  sendOtp: (email: string, turnstileToken: string) => Promise<void>;
  verifyOtp: (email: string, code: string) => Promise<void>;
  googleLogin: (idToken: string) => Promise<void>;
  demoLogin: () => Promise<void>;
  updateUser: (user: User) => void;
  logout: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  initAuth: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await apiClient<AuthTokenResponse>('/auth/refresh', { method: 'POST' });
      setAccessToken(res.access_token);
      set({ user: res.user, isAuthenticated: true, isLoading: false });
    } catch {
      setAccessToken(null);
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  sendOtp: async (email: string, turnstileToken: string) => {
    set({ error: null });
    await apiClient<{ message: string }>('/auth/otp/send', {
      method: 'POST',
      body: JSON.stringify({
        email,
        turnstile_token: turnstileToken,
      }),
    });
  },

  verifyOtp: async (email: string, code: string) => {
    set({ error: null });
    const res = await apiClient<AuthTokenResponse>('/auth/otp/verify', {
      method: 'POST',
      body: JSON.stringify({ email, code }),
    });
    setAccessToken(res.access_token);
    set({ user: res.user, isAuthenticated: true });
  },

  googleLogin: async (idToken: string) => {
    set({ error: null });
    const res = await apiClient<AuthTokenResponse>('/auth/google', {
      method: 'POST',
      body: JSON.stringify({ id_token: idToken }),
    });
    setAccessToken(res.access_token);
    set({ user: res.user, isAuthenticated: true });
  },

  demoLogin: async () => {
    set({ error: null, isLoading: true });
    try {
      const res = await apiClient<AuthTokenResponse>('/auth/demo-login', {
        method: 'POST',
      });
      setAccessToken(res.access_token);
      set({ user: res.user, isAuthenticated: true, isLoading: false });
    } catch (err: any) {
      set({ error: err.message || 'Demo login failed', isLoading: false });
    }
  },

  updateUser: (user: User) => {
    set({ user });
  },

  logout: async () => {
    try {
      await apiClient('/auth/logout', { method: 'POST' });
    } catch {
      // Ignore network errors during logout
    } finally {
      setAccessToken(null);
      set({ user: null, isAuthenticated: false });
    }
  },

  clearError: () => set({ error: null }),
}));
