import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { storage } from '../utils/storage';
import { STORAGE_KEYS } from '../utils/constants';
import { generateId } from '../utils/ids';
import { 
  getWorkspaces, 
  createWorkspace as apiCreateWorkspace,
  getWorkspaceMembers,
  inviteUserToWorkspace,
  updateMemberRole,
  getPendingInvitations,
  acceptInvitation,
  declineInvitation,
  getNotifications,
  markNotificationRead
} from '../api/workspaces.js';

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};

/**
 * Transform backend workspace format to frontend format
 * Backend: {id: number, name: string, created_at: string, created_by: string}
 * Frontend: {id: string, name: string, description: string, createdAt: string, updatedAt: string}
 */
function transformWorkspace(backendWorkspace) {
  return {
    id: String(backendWorkspace.id), // Convert to string for consistency
    name: backendWorkspace.name,
    description: '', // Backend doesn't have description field
    createdAt: backendWorkspace.created_at,
    updatedAt: backendWorkspace.created_at, // Use created_at as updatedAt since backend doesn't have updated_at
  };
}

export const AppProvider = ({ children }) => {
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [workspaceMembers, setWorkspaceMembers] = useState({}); // {workspaceId: [members]}
  const [currentWorkspaceRole, setCurrentWorkspaceRole] = useState({}); // {workspaceId: role}
  const [isWorkspaceCreator, setIsWorkspaceCreator] = useState({}); // {workspaceId: boolean}
  const [pendingInvitations, setPendingInvitations] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [unreadNotificationCount, setUnreadNotificationCount] = useState(0);

  // Load workspaces from API on mount
  useEffect(() => {
    const loadWorkspaces = async () => {
      try {
        const backendWorkspaces = await getWorkspaces();
        // Transform backend format to frontend format
        const transformedWorkspaces = backendWorkspaces.map(transformWorkspace);
        setWorkspaces(transformedWorkspaces);
      } catch (error) {
        console.error('Error loading workspaces:', error);
        // If there's an error, set empty array
        setWorkspaces([]);
      } finally {
        setLoading(false);
      }
    };

    loadWorkspaces();
  }, []);

  const createWorkspace = async (name, description) => {
    try {
      // API only accepts name, description is ignored for now
      const backendWorkspace = await apiCreateWorkspace(name);
      // Transform backend format to frontend format
      const newWorkspace = transformWorkspace(backendWorkspace);
      // Update local state
      setWorkspaces(prev => [...prev, newWorkspace]);
      return newWorkspace;
    } catch (error) {
      // Re-throw error so caller can handle it
      throw error;
    }
  };

  const deleteWorkspace = (id) => {
    // TODO: Implement API call for deleting workspace
    // For now, keep using localStorage (or remove from state)
    const updated = workspaces.filter(w => w.id !== id);
    setWorkspaces(updated);
    // Note: This doesn't delete from backend yet
  };

  const getPdfs = useCallback(async (workspaceId) => {
    // Fetch PDFs from API
    try {
      const { getPdfs: apiGetPdfs, getPdfUrl } = await import('../api/pdfs.js');
      const pdfs = await apiGetPdfs(workspaceId);
      // Transform backend format to frontend format and fetch blob URLs
      const transformedPdfs = await Promise.all(
        pdfs.map(async (pdf) => {
          const blobUrl = await getPdfUrl(pdf.id);
          return {
            id: String(pdf.id),
            name: pdf.title,
            url: blobUrl,
            uploadedAt: pdf.uploaded_at,
            workspaceId: String(pdf.workspace),
          };
        })
      );
      return transformedPdfs;
    } catch (error) {
      console.error('Error fetching PDFs:', error);
      return [];
    }
  }, []);

  const addPdf = useCallback(async (workspaceId, file, title) => {
    // Upload PDF to API
    try {
      const { uploadPdf, getPdfUrl } = await import('../api/pdfs.js');
      const uploadedPdf = await uploadPdf(workspaceId, file, title || file.name);
      // Get blob URL for the uploaded PDF
      const blobUrl = await getPdfUrl(uploadedPdf.id);
      return {
        id: String(uploadedPdf.id),
        name: uploadedPdf.title,
        url: blobUrl,
        uploadedAt: uploadedPdf.uploaded_at,
        workspaceId: String(uploadedPdf.workspace),
      };
    } catch (error) {
      console.error('Error uploading PDF:', error);
      throw error;
    }
  }, []);

  const loadWorkspaceMembers = useCallback(async (workspaceId, currentUserId) => {
    try {
      const members = await getWorkspaceMembers(workspaceId);
      setWorkspaceMembers(prev => ({ ...prev, [workspaceId]: members }));
      
      // Find current user's role and creator status
      if (currentUserId) {
        const currentUserMember = members.find(m => m.user.id === currentUserId);
        if (currentUserMember) {
          setCurrentWorkspaceRole(prev => ({ ...prev, [workspaceId]: currentUserMember.role }));
          setIsWorkspaceCreator(prev => ({ ...prev, [workspaceId]: currentUserMember.is_creator }));
        }
      }
      
      return members;
    } catch (error) {
      console.error('Error loading workspace members:', error);
      throw error;
    }
  }, []);

  const inviteUser = useCallback(async (workspaceId, userId, role, currentUserId) => {
    try {
      const invitation = await inviteUserToWorkspace(workspaceId, userId, role);
      // Note: No need to refresh members list since invitation is pending
      // The invited user will appear in members list only after accepting
      return invitation;
    } catch (error) {
      console.error('Error inviting user:', error);
      throw error;
    }
  }, []);

  const changeMemberRole = useCallback(async (workspaceId, memberId, role, currentUserId) => {
    try {
      const member = await updateMemberRole(workspaceId, memberId, role);
      // Refresh members list
      await loadWorkspaceMembers(workspaceId, currentUserId);
      return member;
    } catch (error) {
      console.error('Error updating member role:', error);
      throw error;
    }
  }, [loadWorkspaceMembers]);

  const loadInvitations = useCallback(async () => {
    try {
      const invitations = await getPendingInvitations();
      setPendingInvitations(invitations);
      return invitations;
    } catch (error) {
      console.error('Error loading invitations:', error);
      throw error;
    }
  }, []);

  const handleAcceptInvitation = useCallback(async (invitationId) => {
    try {
      const member = await acceptInvitation(invitationId);
      // Refresh invitations and workspaces
      await loadInvitations();
      // Reload workspaces to show the new workspace
      const backendWorkspaces = await getWorkspaces();
      const transformedWorkspaces = backendWorkspaces.map(transformWorkspace);
      setWorkspaces(transformedWorkspaces);
      return member;
    } catch (error) {
      console.error('Error accepting invitation:', error);
      throw error;
    }
  }, [loadInvitations]);

  const handleDeclineInvitation = useCallback(async (invitationId) => {
    try {
      await declineInvitation(invitationId);
      // Refresh invitations
      await loadInvitations();
    } catch (error) {
      console.error('Error declining invitation:', error);
      throw error;
    }
  }, [loadInvitations]);

  const loadNotifications = useCallback(async () => {
    try {
      const data = await getNotifications();
      setNotifications(data.notifications || []);
      setUnreadNotificationCount(data.unread_count || 0);
      return data;
    } catch (error) {
      console.error('Error loading notifications:', error);
      throw error;
    }
  }, []);

  const handleMarkNotificationRead = useCallback(async (notificationId) => {
    try {
      await markNotificationRead(notificationId);
      // Update local state
      setNotifications(prev =>
        prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      );
      setUnreadNotificationCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
      throw error;
    }
  }, []);

  const value = {
    workspaces,
    loading,
    createWorkspace,
    deleteWorkspace,
    getPdfs,
    addPdf,
    workspaceMembers,
    currentWorkspaceRole,
    isWorkspaceCreator,
    loadWorkspaceMembers,
    inviteUser,
    changeMemberRole,
    pendingInvitations,
    notifications,
    unreadNotificationCount,
    loadInvitations,
    handleAcceptInvitation,
    handleDeclineInvitation,
    loadNotifications,
    handleMarkNotificationRead
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
