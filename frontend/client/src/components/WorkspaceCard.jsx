import { useState, useRef, useEffect } from 'react';
import { Link } from 'wouter';
import { useApp } from '../context/AppContext';
import Modal from './Modal';
import Button from './Button';
import Icon from './Icon';

export default function WorkspaceCard({ workspace, isCreator }) {
  const [showMenu, setShowMenu] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const menuRef = useRef(null);
  const { deleteWorkspace } = useApp();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false);
      }
    };

    if (showMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showMenu]);

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await deleteWorkspace(workspace.id);
      setShowDeleteModal(false);
    } catch (error) {
      console.error('Error deleting workspace:', error);
      alert('Failed to delete workspace: ' + (error.message || 'Unknown error'));
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <div className="workspace-card rounded-lg p-6 transition-colors relative"
        style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)' }}
        onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--accent-color)'}
        onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border-color)'}
      >
        {isCreator && (
          <div className="absolute top-4 right-4" ref={menuRef}>
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setShowMenu(!showMenu);
              }}
              className="p-1 transition-colors"
              style={{ color: 'var(--muted-text)' }}
              onMouseEnter={(e) => e.target.style.color = 'var(--text-color)'}
              onMouseLeave={(e) => e.target.style.color = 'var(--muted-text)'}
              data-testid={`button-menu-workspace-${workspace.id}`}
            >
              <Icon name="more-vertical" size={20} />
            </button>
            {showMenu && (
              <div className="absolute top-8 right-0 rounded-lg shadow-lg z-10 min-w-[160px]"
                style={{ background: 'var(--hover-bg)', border: '1px solid var(--border-color)' }}
              >
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setShowMenu(false);
                    setShowDeleteModal(true);
                  }}
                  className="w-full text-left px-4 py-2 text-sm text-red-400 rounded-t-lg transition-colors"
                  style={{ color: '#ef4444' }}
                  onMouseEnter={(e) => e.target.style.background = 'var(--border-color)'}
                  onMouseLeave={(e) => e.target.style.background = 'transparent'}
                  data-testid={`button-delete-workspace-${workspace.id}`}
                >
                  Delete Workspace
                </button>
              </div>
            )}
          </div>
        )}
        <Link to={`/workspace/${workspace.id}`} data-testid={`card-workspace-${workspace.id}`}>
          <div className="cursor-pointer">
            <h3 className="text-xl font-semibold mb-2 pr-8" style={{ color: 'var(--text-color)' }}>{workspace.name}</h3>
            <p className="text-sm mb-4 line-clamp-2" style={{ color: 'var(--muted-text)' }}>{workspace.description}</p>
            <p className="text-xs" style={{ color: 'var(--muted-text)' }}>
              Created {new Date(workspace.createdAt).toLocaleDateString()}
            </p>
          </div>
        </Link>
      </div>

      <Modal
        isOpen={showDeleteModal}
        onClose={() => !isDeleting && setShowDeleteModal(false)}
        title="Delete Workspace"
      >
        <div className="space-y-4">
          <p style={{ color: 'var(--text-color)' }}>
            Are you sure you want to delete this workspace?
          </p>
          <p className="text-sm" style={{ color: 'var(--muted-text)' }}>
            This action cannot be undone.
          </p>
          <div className="flex gap-2 justify-end">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowDeleteModal(false)}
              disabled={isDeleting}
              data-testid="button-cancel-delete"
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="primary"
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-red-600 hover:bg-red-700"
              data-testid="button-confirm-delete"
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
