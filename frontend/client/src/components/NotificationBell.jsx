import { useState, useEffect, useRef } from 'react';
import { getNotifications, markNotificationRead, acceptInvitation, declineInvitation, getWorkspaceMembers } from '../api/workspaces';
import { useAuth } from '../context/AuthContext';
import { useApp } from '../context/AppContext';
import Button from './Button';

export default function NotificationBell() {
  const { isAuthenticated, user } = useAuth();
  const { loadWorkspaceMembers } = useApp();
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [acceptingInvitation, setAcceptingInvitation] = useState(null);
  const [badgeHidden, setBadgeHidden] = useState(false);
  const dropdownRef = useRef(null);

  // Load notifications on mount
  useEffect(() => {
    if (!isAuthenticated) return;

    const loadNotifications = async () => {
      try {
        setLoading(true);
        const data = await getNotifications();
        setNotifications(data.notifications || []);
        const newUnreadCount = data.unread_count || 0;
        setUnreadCount(newUnreadCount);
        if (newUnreadCount > 0) {
          setBadgeHidden(false);
        }
      } catch (error) {
        console.error('Failed to load notifications:', error);
      } finally {
        setLoading(false);
      }
    };

    loadNotifications();
  }, [isAuthenticated]);

  // WebSocket connection for real-time notifications
  useEffect(() => {
    if (!isAuthenticated) return;

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${protocol}://${window.location.host}/ws/notifications/`;
    const notifSocket = new WebSocket(wsUrl);

    notifSocket.onmessage = async function (e) {
      const data = JSON.parse(e.data);
      const badge = document.getElementById("notification-badge");
      if (badge) {
        badge.style.display = "flex";
        badge.textContent = data.unread_count > 9 ? '9+' : data.unread_count;
      }
      setUnreadCount(data.unread_count || 0);
      if (data.unread_count > 0) {
        setBadgeHidden(false);
      }
      const notificationData = await getNotifications();
      setNotifications(notificationData.notifications || []);
    };

    notifSocket.onerror = function (error) {
      console.error('WebSocket error:', error);
    };

    notifSocket.onclose = function () {
      console.log('WebSocket closed');
    };

    return () => {
      notifSocket.close();
    };
  }, [isAuthenticated]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleNotificationClick = async (notification) => {
    if (!notification.is_read && notification.type !== 'INVITATION') {
      try {
        await markNotificationRead(notification.id);
        setNotifications(prev =>
          prev.map(n => n.id === notification.id ? { ...n, is_read: true } : n)
        );
        setUnreadCount(prev => {
          const newCount = Math.max(0, prev - 1);
          if (newCount === 0) {
            const badge = document.getElementById("notification-badge");
            if (badge) {
              badge.style.display = "none";
            }
          }
          return newCount;
        });
      } catch (error) {
        console.error('Failed to mark notification as read:', error);
      }
    }
  };

  const handleAcceptInvitation = async (e, notification) => {
    e.stopPropagation();
    if (!notification.invitation_id || !notification.workspace_id) return;
    
    setAcceptingInvitation(notification.id);
    
    try {
      // Accept invitation
      const memberData = await acceptInvitation(notification.invitation_id);
      
      // Refresh workspace members in AppContext to update role/permissions
      if (user?.id && loadWorkspaceMembers) {
        await loadWorkspaceMembers(notification.workspace_id, user.id);
      }
      
      // Also fetch members directly to ensure UI is updated
      try {
        const members = await getWorkspaceMembers(notification.workspace_id);
        // Trigger custom event for workspace components to refresh
        window.dispatchEvent(new CustomEvent('workspaceMemberAdded', { 
          detail: { 
            workspaceId: notification.workspace_id,
            member: memberData,
            role: memberData.role // Ensure role is included
          } 
        }));
      } catch (err) {
        console.error('Failed to refresh workspace members:', err);
      }
      
      // Remove notification and refresh list
      const data = await getNotifications();
      setNotifications(data.notifications || []);
      const newUnreadCount = data.unread_count || 0;
      setUnreadCount(newUnreadCount);
      // Show badge again if there are new unread notifications
      if (newUnreadCount > 0) {
        setBadgeHidden(false);
      }
      
    } catch (error) {
      console.error('Failed to accept invitation:', error);
      alert(error.message || 'Failed to accept invitation');
    } finally {
      setAcceptingInvitation(null);
    }
  };

  const handleDeclineInvitation = async (e, notification) => {
    e.stopPropagation();
    if (!notification.invitation_id) return;
    
    try {
      await declineInvitation(notification.invitation_id);
      // Remove notification and refresh list
      const data = await getNotifications();
      setNotifications(data.notifications || []);
      const newUnreadCount = data.unread_count || 0;
      setUnreadCount(newUnreadCount);
      // Show badge again if there are new unread notifications
      if (newUnreadCount > 0) {
        setBadgeHidden(false);
      }
    } catch (error) {
      console.error('Failed to decline invitation:', error);
      alert(error.message || 'Failed to decline invitation');
    }
  };

  if (!isAuthenticated) return null;

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={async () => {
          setIsOpen(!isOpen);
          if (unreadCount > 0) {
            setBadgeHidden(true);
            const badge = document.getElementById("notification-badge");
            if (badge) {
              badge.style.display = "none";
            }
          }
        }}
        className="relative p-2 notification-bell transition-colors"
        style={{ color: 'var(--text-color)' }}
        onMouseEnter={(e) => e.target.style.color = 'var(--accent-color)'}
        onMouseLeave={(e) => e.target.style.color = 'var(--text-color)'}
        title="Notifications"
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {unreadCount > 0 && !badgeHidden && (
          <span id="notification-badge" className="notification-badge absolute top-0 right-0 text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="notification-dropdown absolute right-0 mt-2 w-80 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
          <div className="p-4" style={{ borderBottom: '1px solid var(--border-color)' }}>
            <h3 className="text-lg font-semibold" style={{ color: 'var(--text-color)' }}>Notifications</h3>
          </div>
          
          {loading ? (
            <div className="p-4 text-center" style={{ color: 'var(--muted-text)' }}>Loading...</div>
          ) : notifications.length === 0 ? (
            <div className="p-4 text-center" style={{ color: 'var(--muted-text)' }}>No notifications</div>
          ) : (
            <div style={{ borderTop: '1px solid var(--border-color)' }}>
              {notifications.slice(0, 10).map(notification => (
                <div
                  key={notification.id}
                  className={`notification-item w-full p-4 ${
                    !notification.is_read ? 'unread' : ''
                  }`}
                  style={{ borderBottom: '1px solid var(--border-color)' }}
                >
                  <div className="flex items-start gap-2">
                    {!notification.is_read && (
                      <div className="w-2 h-2 rounded-full mt-2 flex-shrink-0" style={{ background: 'var(--accent-color)' }} />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium" style={{ color: 'var(--text-color)' }}>{notification.title}</p>
                      <p className="text-xs mt-1" style={{ color: 'var(--muted-text)' }}>{notification.message}</p>
                      {notification.workspace && (
                        <p className="text-xs mt-1" style={{ color: 'var(--accent-color)' }}>
                          {notification.workspace.name}
                        </p>
                      )}
                      {notification.invitation_role_display && (
                        <p className="text-xs mt-1 font-medium" style={{ color: 'var(--accent-color)' }}>
                          Invited as {notification.invitation_role_display}
                        </p>
                      )}
                      <p className="text-xs mt-1" style={{ color: 'var(--muted-text)' }}>
                        {new Date(notification.created_at).toLocaleDateString()}
                      </p>
                      
                      {/* Accept/Decline buttons for invitation notifications */}
                      {notification.type === 'INVITATION' && notification.invitation_id && !notification.is_read && (
                        <div className="flex gap-2 mt-3">
                          <Button
                            onClick={(e) => handleAcceptInvitation(e, notification)}
                            variant="primary"
                            className="flex-1 text-xs py-1"
                            disabled={acceptingInvitation === notification.id}
                          >
                            {acceptingInvitation === notification.id ? 'Accepting...' : 'Accept'}
                          </Button>
                          <Button
                            onClick={(e) => handleDeclineInvitation(e, notification)}
                            variant="secondary"
                            className="flex-1 text-xs py-1"
                            disabled={acceptingInvitation === notification.id}
                          >
                            Decline
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

