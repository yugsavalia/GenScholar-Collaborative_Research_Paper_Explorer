import { createContext, useContext, useState, useEffect } from 'react';
import { storage } from '../utils/storage';
import { STORAGE_KEYS } from '../utils/constants';
import { generateId } from '../utils/ids';

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const [workspaces, setWorkspaces] = useState([]);

  useEffect(() => {
    const savedWorkspaces = storage.get(STORAGE_KEYS.WORKSPACES) || [];
    setWorkspaces(savedWorkspaces);
  }, []);

  const createWorkspace = (name, description) => {
    const newWorkspace = {
      id: generateId(),
      name,
      description,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    const updated = [...workspaces, newWorkspace];
    setWorkspaces(updated);
    storage.set(STORAGE_KEYS.WORKSPACES, updated);
    return newWorkspace;
  };

  const deleteWorkspace = (id) => {
    const updated = workspaces.filter(w => w.id !== id);
    setWorkspaces(updated);
    storage.set(STORAGE_KEYS.WORKSPACES, updated);
  };

  const getPdfs = (workspaceId) => {
    return storage.get(STORAGE_KEYS.PDFS(workspaceId)) || [];
  };

  const addPdf = (workspaceId, name, url) => {
    const newPdf = {
      id: generateId(),
      name,
      url,
      uploadedAt: new Date().toISOString()
    };
    const pdfs = getPdfs(workspaceId);
    const updated = [...pdfs, newPdf];
    storage.set(STORAGE_KEYS.PDFS(workspaceId), updated);
    return newPdf;
  };

  const value = {
    workspaces,
    createWorkspace,
    deleteWorkspace,
    getPdfs,
    addPdf
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
