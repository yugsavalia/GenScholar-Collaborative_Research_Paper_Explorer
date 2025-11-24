import { storage } from '../utils/storage';
import { STORAGE_KEYS } from '../utils/constants';
import { apiGet, apiPost, apiDelete } from './client';

const useBackend = import.meta.env.VITE_USE_BACKEND_API === 'true';

export async function listAnnotations(workspaceId, pdfId) {
  if (!useBackend) {
    return storage.get(STORAGE_KEYS.ANNOTATIONS(workspaceId, pdfId)) || [];
  }
  // Backend endpoint is /api/annotations/?pdf_id=X (not nested)
  const res = await apiGet(`/api/annotations/?pdf_id=${pdfId}`, {
    credentials: 'include',
  });
  // DRF ViewSet returns array directly or {results: [...]}
  if (Array.isArray(res)) {
    return res;
  }
  return res?.results || res?.data?.annotations || [];
}

export async function createAnnotation(workspaceId, pdfId, payload) {
  if (!useBackend) {
    const key = STORAGE_KEYS.ANNOTATIONS(workspaceId, pdfId);
    const current = storage.get(key) || [];
    const withId = { id: (crypto?.randomUUID?.() || String(Date.now())), ...payload, created_at: new Date().toISOString() };
    storage.set(key, [...current, withId]);
    return withId;
  }
  // Backend endpoint is /api/annotations/ (not nested)
  // Need to include pdf_id in the payload
  const res = await apiPost(`/api/annotations/`, {
    ...payload,
    pdf: pdfId,
  }, {
    credentials: 'include',
  });
  // DRF ViewSet returns the created object directly (not wrapped in data)
  return res;
}

export async function deleteAnnotation(workspaceId, pdfId, id) {
  if (!useBackend) {
    const key = STORAGE_KEYS.ANNOTATIONS(workspaceId, pdfId);
    const current = storage.get(key) || [];
    storage.set(key, current.filter(a => a.id !== id));
    return { success: true };
  }
  return apiDelete(`/api/annotations/${id}/`, { credentials: 'include' });
}


