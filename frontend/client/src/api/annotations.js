import { storage } from '../utils/storage';
import { STORAGE_KEYS } from '../utils/constants';
import { apiGet, apiPost, apiDelete } from './client';

const useBackend = import.meta.env.VITE_USE_BACKEND_API === 'true';

export async function listAnnotations(workspaceId, pdfId) {
  if (!useBackend) {
    return storage.get(STORAGE_KEYS.ANNOTATIONS(workspaceId, pdfId)) || [];
  }
  const res = await apiGet(`/api/workspaces/${workspaceId}/pdfs/${pdfId}/annotations/`, {
    credentials: 'include',
  });
  return res?.data?.annotations || [];
}

export async function createAnnotation(workspaceId, pdfId, payload) {
  if (!useBackend) {
    const key = STORAGE_KEYS.ANNOTATIONS(workspaceId, pdfId);
    const current = storage.get(key) || [];
    const withId = { id: (crypto?.randomUUID?.() || String(Date.now())), ...payload, created_at: new Date().toISOString() };
    storage.set(key, [...current, withId]);
    return withId;
  }
  const res = await apiPost(`/api/workspaces/${workspaceId}/pdfs/${pdfId}/annotations/`, payload, {
    credentials: 'include',
  });
  return res?.data?.annotation || res?.data;
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


