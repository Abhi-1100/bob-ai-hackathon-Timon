import { create } from 'zustand';
import api from '../services/api';

const TOKEN_KEY = 'd2_access_token';
const USER_KEY = 'd2_user_profile';

const getInitialToken = () => {
  try {
    return localStorage.getItem(TOKEN_KEY) || null;
  } catch {
    return null;
  }
};

const getInitialUser = () => {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

export const useAuthStore = create((set, get) => ({
  accessToken: getInitialToken(),
  user: getInitialUser(),
  isAuthenticated: Boolean(getInitialToken()),
  loading: false,
  authError: null,

  clearError: () => set({ authError: null }),

  setUser: (user) => {
    try {
      if (user) {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
      } else {
        localStorage.removeItem(USER_KEY);
      }
    } catch (e) {
      console.warn('localStorage error', e);
    }
    set({ user });
  },

  updateProfile: (updatedFields) => {
    const current = get().user || {};
    const updatedUser = { ...current, ...updatedFields };
    try {
      localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
    } catch (e) {
      console.warn('localStorage error', e);
    }
    set({ user: updatedUser });
    return updatedUser;
  },

  setToken: (token) => {
    try {
      if (token) {
        localStorage.setItem(TOKEN_KEY, token);
      } else {
        localStorage.removeItem(TOKEN_KEY);
      }
    } catch (e) {
      console.warn('localStorage error', e);
    }
    set({ accessToken: token, isAuthenticated: Boolean(token) });
  },

  login: async ({ email, password }) => {
    set({ loading: true, authError: null });
    try {
      const response = await api.post('/api/v1/auth/login', { email, password });
      const { access_token, user } = response.data;

      localStorage.setItem(TOKEN_KEY, access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));

      set({
        accessToken: access_token,
        user,
        isAuthenticated: true,
        loading: false,
        authError: null,
      });

      return { success: true, user };
    } catch (error) {
      const msg = error.response?.data?.detail || error.message || 'Authentication failed.';
      set({ loading: false, authError: msg });
      return { success: false, error: msg };
    }
  },

  register: async ({ name, email, password, organization, role }) => {
    set({ loading: true, authError: null });
    try {
      const response = await api.post('/api/v1/auth/register', {
        name,
        email,
        password,
        organization: organization || 'Security Operations Center',
        role: role || 'SOC Analyst',
      });
      const { access_token, user } = response.data;

      localStorage.setItem(TOKEN_KEY, access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));

      set({
        accessToken: access_token,
        user,
        isAuthenticated: true,
        loading: false,
        authError: null,
      });

      return { success: true, user };
    } catch (error) {
      const msg = error.response?.data?.detail || error.message || 'Registration failed.';
      set({ loading: false, authError: msg });
      return { success: false, error: msg };
    }
  },

  forgotPassword: async (email) => {
    set({ loading: true, authError: null });
    try {
      const response = await api.post('/api/v1/auth/forgot-password', { email });
      set({ loading: false });
      return { success: true, data: response.data };
    } catch (error) {
      const msg = error.response?.data?.detail || error.message || 'Failed to dispatch reset instructions.';
      set({ loading: false, authError: msg });
      return { success: false, error: msg };
    }
  },

  resetPassword: async ({ token, newPassword }) => {
    set({ loading: true, authError: null });
    try {
      const response = await api.post('/api/v1/auth/reset-password', {
        token,
        new_password: newPassword,
      });
      set({ loading: false });
      return { success: true, data: response.data };
    } catch (error) {
      const msg = error.response?.data?.detail || error.message || 'Password reset failed.';
      set({ loading: false, authError: msg });
      return { success: false, error: msg };
    }
  },

  loginAsEvaluator: () => {
    const demoUser = {
      id: 'demo-evaluator-soc-l3',
      name: 'Hackathon Evaluator',
      email: 'evaluator@sentinelforge.mil',
      organization: 'Judge Evaluation Station',
      role: 'Chief Security Officer (Level 3 Clearance)',
    };
    const demoToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.demo-evaluator-token-2026';

    try {
      localStorage.setItem(TOKEN_KEY, demoToken);
      localStorage.setItem(USER_KEY, JSON.stringify(demoUser));
    } catch (e) {
      console.warn('localStorage error', e);
    }

    set({
      accessToken: demoToken,
      user: demoUser,
      isAuthenticated: true,
      loading: false,
      authError: null,
    });

    return demoUser;
  },

  logout: () => {
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    } catch (e) {
      console.warn('localStorage error', e);
    }
    set({
      accessToken: null,
      user: null,
      isAuthenticated: false,
      loading: false,
      authError: null,
    });
  },

  checkAuth: async () => {
    const token = get().accessToken;
    if (!token) {
      set({ isAuthenticated: false, user: null });
      return false;
    }
    try {
      const response = await api.get('/api/v1/auth/me');
      set({ user: response.data, isAuthenticated: true });
      return true;
    } catch (err) {
      // If unauthorized, clean up
      if (err.response?.status === 401) {
        get().logout();
      }
      return false;
    }
  },
}));

export default useAuthStore;
