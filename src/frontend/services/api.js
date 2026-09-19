import axios from 'axios';

const rawApiBase = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_BASE = rawApiBase.replace(/\/+$/, '');

// 1. Axios Instance for Enterprise API and Auth Calls
export const axiosClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
});

axiosClient.interceptors.request.use(
  (config) => {
    try {
      const token = localStorage.getItem('d2_access_token');
      if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (e) {
      console.warn('[API] Could not attach token', e);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

axiosClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const url = error.config?.url || '';
      // Don't clear tokens for login/register/me — those handle auth themselves
      if (!url.includes('/api/v1/auth/login') && !url.includes('/api/v1/auth/register') && !url.includes('/api/v1/auth/me')) {
        console.warn('[API] 401 Unauthorized — clearing stored credentials.');
        try {
          localStorage.removeItem('d2_access_token');
          localStorage.removeItem('d2_user_profile');
        } catch (e) {
          // ignore
        }
        // Let React route guard handle the redirect instead of hard page reload
      }
    }
    return Promise.reject(error);
  }
);

// Client-Side In-Memory Cache & In-Flight Request Deduplication
const _clientCache = new Map();
const _inFlightRequests = new Map();
const CLIENT_CACHE_TTL_MS = 300000; // 5 minutes — matches backend Redis TTL

export function clearApiClientCache() {
  _clientCache.clear();
  _inFlightRequests.clear();
}

/**
 * Get a user-scoped cache key by prefixing the path with the current user's ID.
 * This ensures each authenticated user has isolated cache entries,
 * preventing cross-user data leakage in the same browser session.
 */
function _getUserCacheKey(path) {
  try {
    const token = localStorage.getItem('d2_access_token');
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]));
      if (payload.sub) {
        return `${payload.sub}::${path}`;
      }
    }
  } catch {
    // Token parse failure — fall through to un-scoped key
  }
  return path;
}

// 2. Dual-mode callable API function for backward-compatibility with existing pages
export async function api(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const isGet = method === 'GET';
  const cacheKey = _getUserCacheKey(path);

  // Return cached result if available and fresh
  if (isGet) {
    const cached = _clientCache.get(cacheKey);
    if (cached && Date.now() < cached.expiresAt) {
      return cached.data;
    }

    // Deduplicate in-flight concurrent requests for the same URL
    if (_inFlightRequests.has(cacheKey)) {
      return _inFlightRequests.get(cacheKey);
    }
  } else {
    // Non-GET requests (mutations) invalidate the client cache
    _clientCache.clear();
  }

  const fetchPromise = (async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 55000);

      const token = typeof localStorage !== 'undefined' ? localStorage.getItem('d2_access_token') : null;
      const headers = {
        ...(options.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      };

      const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (response.status === 401) {
        // Don't hard-redirect; let React auth route guard handle navigation
        try {
          localStorage.removeItem('d2_access_token');
          localStorage.removeItem('d2_user_profile');
        } catch (e) {
          // ignore
        }
        throw new Error('Unauthorized');
      }

      if (!response.ok) {
        const errText = await response.text().catch(() => '');
        throw new Error(`API returned ${response.status}: ${errText}`);
      }
      const data = await response.json();

      if (isGet) {
        _clientCache.set(cacheKey, {
          data,
          expiresAt: Date.now() + CLIENT_CACHE_TTL_MS,
        });
      }
      return data;
    } catch (err) {
      console.warn(`[THREATINTEL API] Fetch failed for ${path} (${err.message}). Returning zero-state dynamic fallback.`);
      return getFallbackData(path, options);
    } finally {
      if (isGet) {
        _inFlightRequests.delete(cacheKey);
      }
    }
  })();

  if (isGet) {
    _inFlightRequests.set(cacheKey, fetchPromise);
  }

  return fetchPromise;
}

// Attach Axios methods to api object
api.get = (url, config) => axiosClient.get(url, config);
api.post = (url, data, config) => axiosClient.post(url, data, config);
api.put = (url, data, config) => axiosClient.put(url, data, config);
api.delete = (url, config) => axiosClient.delete(url, config);
api.clearCache = clearApiClientCache;
api.interceptors = axiosClient.interceptors;
api.getDashboardStats = () => api('/api/v1/dashboard/stats');

/**
 * 0-Data Dynamic Fallbacks: strictly empty states (no fake static records)
 */
function getFallbackData(path, options = {}) {
  // Dashboard stats
  if (path.includes('/api/v1/dashboard/stats')) {
    return {
      total_alerts: 0,
      total_chains: 0,
      critical_incidents: 0,
      high_risk_incidents: 0,
      medium_risk_incidents: 0,
      low_risk_incidents: 0,
      mitre_techniques_count: 0,
      avg_risk_score: 0.0,
      noise_reduction: 0.0,
      risk_distribution: [
        { name: 'Critical', value: 0, color: '#EF4444' },
        { name: 'High', value: 0, color: '#F97316' },
        { name: 'Medium', value: 0, color: '#FBBF24' },
        { name: 'Low', value: 0, color: '#10B981' },
      ],
      mitre_frequency: [],
      timeline: [],
      recent_incidents: [],
    };
  }

  // Analytics
  if (path.includes('/api/v1/analytics/overview')) {
    return {
      total_alerts: 0,
      total_chains: 0,
      unique_sources: 0,
      unique_destinations: 0,
      attack_types: [],
      severity_breakdown: [],
      top_sources: [],
      top_targets: [],
      mitre_frequency: [],
      trend_data: [],
    };
  }

  // Chains list
  if (path.includes('/api/v1/chains') && !path.split('/')[4]) {
    return { chains: [], count: 0 };
  }

  // Single chain detail
  if (path.match(/\/api\/v1\/chains\/([^/]+)$/)) {
    return null;
  }

  // MITRE overview
  if (path.includes('/api/v1/mitre/overview')) {
    return {
      total_detected: 0,
      techniques: [],
      matrix: [],
    };
  }

  // Recommendations
  if (path.includes('/api/v1/recommendations')) {
    return { recommendations: [], total: 0 };
  }

  // Reports
  if (path.includes('/api/v1/reports')) {
    return { reports: [], total_reports: 0 };
  }

  return { success: false, data: null };
}

// Helper API methods
api.getStats = () => api('/api/v1/dashboard/stats');
api.getAnalytics = () => api('/api/v1/analytics/overview');
api.resetDatabase = () =>
  api('/api/v1/dashboard/reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
api.getChains = () => api('/api/v1/chains');
api.getChain = (id) => api(`/api/v1/chains/${id}`);
api.getMitreOverview = () => api('/api/v1/mitre/overview');
api.getRecommendations = () => api('/api/v1/recommendations');
api.getReports = () => api('/api/v1/reports');
api.getReport = (id) => api(`/api/v1/reports/${id}`);

/**
 * Upload CSV file and trigger end-to-end correlation & scoring
 */
api.uploadAndIngest = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await axiosClient.post('/api/v1/upload/ingest', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000,
    });

    clearApiClientCache();
    return response.data;
  } catch (err) {
    if (err.response?.data?.message) {
      throw new Error(err.response.data.message);
    }
    if (err.response?.data?.detail) {
      const d = err.response.data.detail;
      throw new Error(typeof d === 'string' ? d : JSON.stringify(d));
    }
    if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
      throw new Error('Upload took longer than expected. Processing continues in the background.');
    }
    if (err.message === 'Network Error' || err.message?.includes('Network Error') || err.message?.includes('Failed to fetch')) {
      throw new Error('Backend server is starting up or temporarily unreachable. Please wait 10 seconds and try again.');
    }
    throw err;
  }
};

export function listFrom(obj, candidateKeys = ['items', 'results', 'data', 'chains', 'scores']) {
  if (Array.isArray(obj)) return obj;
  if (!obj || typeof obj !== 'object') return [];
  for (const k of candidateKeys) {
    if (Array.isArray(obj[k])) return obj[k];
  }
  return [];
}

export function severity(val) {
  const s = String(val || '').toLowerCase();
  if (s.includes('crit')) return 'critical';
  if (s.includes('high')) return 'high';
  if (s.includes('med')) return 'medium';
  return 'low';
}

export const getId = (chain) => chain?.chain_id || chain?.id || chain?.chainId;

export default api;
