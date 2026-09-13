const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || body.message || `Request failed (${response.status})`);
  return body;
}

export const severity = (value = '') => String(value).toLowerCase();

export function listFrom(payload, keys = []) {
  if (Array.isArray(payload)) return payload;
  for (const key of keys) if (Array.isArray(payload?.[key])) return payload[key];
  return [];
}

export const getId = chain => chain?.chain_id || chain?.id || chain?.chainId;
