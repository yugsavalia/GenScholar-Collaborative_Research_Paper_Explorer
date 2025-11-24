import { useState, useEffect, useRef } from 'react';
import { useRoute } from 'wouter';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';
import { ANNOTATION_TYPES } from '../utils/constants';
import { generateId } from '../utils/ids';
import Navbar from '../components/Navbar';
import PdfViewer from '../components/PdfViewer';
import PdfToolbar from '../components/PdfToolbar';
import PdfSidebar from '../components/PdfSidebar';
import RoleBadge from '../components/RoleBadge';
import InviteUserPanel from '../components/InviteUserPanel';
import WorkspaceMembersPanel from '../components/WorkspaceMembersPanel';
import PinnedNotesPanel from '../components/PinnedNotesPanel';
import Icon from '../components/Icon';
import Button from '../components/Button';
import { listAnnotations, createAnnotation, deleteAnnotation } from '../api/annotations';
import { deletePdf } from '../api/pdfs';
import Modal from '../components/Modal';

export default function Workspace() {
  const [, params] = useRoute('/workspace/:id');
  const workspaceId = params?.id;
  
  const { 
    workspaces, 
    getPdfs, 
    addPdf,
    workspaceMembers,
    currentWorkspaceRole,
    isWorkspaceCreator,
    loadWorkspaceMembers,
    inviteUser,
    changeMemberRole,
    getThreads,
    createThread,
    threadsByPdf
  } = useApp();
  const { user } = useAuth();
  // Normalize workspaceId for comparison (workspace.id might be number, workspaceId from route is string)
  const workspace = workspaces.find(w => String(w.id) === String(workspaceId));
  
  const [pdfs, setPdfs] = useState([]);
  const [selectedPdf, setSelectedPdf] = useState(null);
  const [annotationMode, setAnnotationMode] = useState(ANNOTATION_TYPES.SELECT);
  const [selectedAnnotation, setSelectedAnnotation] = useState(null);
  const [annotations, setAnnotations] = useState([]);
  const [showMembersPanel, setShowMembersPanel] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedThreadId, setSelectedThreadId] = useState(null);
  const [pdfSearchQuery, setPdfSearchQuery] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [pdfToDelete, setPdfToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const fileInputRef = useRef(null);
  const pdfsRef = useRef([]); // Store PDFs in ref for cleanup

  // Load workspace members when workspaceId changes
  useEffect(() => {
    if (workspaceId && user?.id) {
      loadWorkspaceMembers(workspaceId, user.id).catch(err => {
        console.error('Failed to load workspace members:', err);
      });
    }
  }, [workspaceId, user?.id, loadWorkspaceMembers]); // loadWorkspaceMembers is now memoized

  // Listen for workspace member added event (when invitation is accepted)
  useEffect(() => {
    const handleMemberAdded = (event) => {
      if (event.detail.workspaceId === workspaceId && user?.id) {
        loadWorkspaceMembers(workspaceId, user.id).catch(err => {
          console.error('Failed to refresh workspace members:', err);
        });
      }
    };

    window.addEventListener('workspaceMemberAdded', handleMemberAdded);
    return () => window.removeEventListener('workspaceMemberAdded', handleMemberAdded);
  }, [workspaceId, user?.id, loadWorkspaceMembers]);

  // Load PDFs when workspace changes - simple, single call
  useEffect(() => {
    // Ensure workspaceId is valid before proceeding
    const normalizedWorkspaceId = workspaceId ? String(workspaceId).trim() : null;
    
    if (!normalizedWorkspaceId) {
      console.log('[Workspace] No workspaceId, clearing PDFs');
      setPdfs([]);
      pdfsRef.current = [];
      setSelectedPdf(null);
      return;
    }

    let isCancelled = false;

    const loadPdfs = async () => {
      try {
        console.log('[Workspace] Loading PDFs for workspace:', normalizedWorkspaceId);
        const workspacePdfs = await getPdfs(normalizedWorkspaceId);
        console.log('[Workspace] PDFs loaded:', workspacePdfs.length, workspacePdfs);
        
        // Don't update state if component unmounted or workspace changed
        if (isCancelled) {
          console.log('[Workspace] Load cancelled, skipping state update');
          return;
        }
        
        if (!workspacePdfs || workspacePdfs.length === 0) {
          console.warn('[Workspace] No PDFs returned from API');
        }
        
        setPdfs(workspacePdfs);
        pdfsRef.current = workspacePdfs;
        
        // Auto-select first PDF if none selected
        setSelectedPdf(prev => {
          // Only auto-select if no PDF is currently selected
          if (!prev && workspacePdfs.length > 0) {
            console.log('[Workspace] Auto-selecting first PDF:', workspacePdfs[0].id);
            return workspacePdfs[0];
          }
          return prev;
        });
      } catch (error) {
        console.error('[Workspace] Failed to load PDFs:', error);
        if (!isCancelled) {
          setPdfs([]);
          pdfsRef.current = [];
        }
      }
    };

    loadPdfs();

    return () => {
      isCancelled = true;
    };
  }, [workspaceId, getPdfs]); // Include getPdfs to ensure it's available

  // Fetch blob URL when PDF is selected (lazy loading - only when needed)
  useEffect(() => {
    if (!selectedPdf || selectedPdf.url) return; // Already has URL or no PDF selected
    
    const fetchBlobUrl = async () => {
      try {
        const { getPdfUrl } = await import('../api/pdfs.js');
        const blobUrl = await getPdfUrl(selectedPdf.id);
        // Update selected PDF with blob URL
        setSelectedPdf(prev => prev ? { ...prev, url: blobUrl } : null);
        // Also update in PDFs list
        setPdfs(prev => prev.map(pdf => 
          pdf.id === selectedPdf.id ? { ...pdf, url: blobUrl } : pdf
        ));
      } catch (error) {
        console.error('Failed to fetch PDF blob URL:', error);
      }
    };
    
    fetchBlobUrl();
  }, [selectedPdf?.id]); // Only when PDF ID changes and URL is missing

  // Cleanup blob URLs on unmount
  useEffect(() => {
    return () => {
      // Revoke all blob URLs when component unmounts to prevent memory leaks
      pdfsRef.current.forEach(pdf => {
        if (pdf.url && pdf.url.startsWith('blob:')) {
          URL.revokeObjectURL(pdf.url);
        }
      });
    };
  }, []); // Only run cleanup on unmount

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !workspaceId || isUploading) return;

    setIsUploading(true);
    // Reset file input so same file can be uploaded again if needed
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }

    try {
      // Upload PDF and get back the formatted PDF object with blob URL
      const newPdf = await addPdf(workspaceId, file, file.name);
      
      // Append new PDF to existing list (newest first) - prevent duplicates
      setPdfs(prev => {
        if (prev.some(p => p.id === newPdf.id)) return prev;
        return [newPdf, ...prev];
      });
      
      // Select the newly uploaded PDF
      setSelectedPdf(newPdf);
    } catch (err) {
      console.error('Failed to upload file:', err);
      alert('Failed to upload PDF: ' + (err.message || 'Unknown error'));
    } finally {
      setIsUploading(false);
    }
  };

  // Helper function to transform annotation from backend format to frontend format
  const transformAnnotation = (annotation) => {
    const coords = annotation.coordinates || {};
    return {
      ...annotation,
      quads: coords.quads || annotation.quads || [],
      type: coords.type || annotation.type || '',
      color: coords.color || annotation.color || '#FFEB3B',
      pageNumber: annotation.page_number || annotation.pageNumber
    };
  };

  useEffect(() => {
    const load = async () => {
      if (!workspaceId || !selectedPdf?.id) return;
      try {
        const list = await listAnnotations(workspaceId, selectedPdf.id);
        // Transform annotations from backend format to frontend format
        const transformed = list.map(transformAnnotation);
        setAnnotations(transformed);
      } catch (error) {
        console.error('Failed to load annotations:', error);
      }
    };
    load();
  }, [workspaceId, selectedPdf?.id]);

  // Load threads when PDF changes
  useEffect(() => {
    if (!workspaceId || !selectedPdf?.id) return;
    getThreads(workspaceId, selectedPdf.id).catch(err => {
      console.error('Failed to load threads:', err);
    });
  }, [workspaceId, selectedPdf?.id, getThreads]);

  const handleTextSelect = async (selection) => {
    if (annotationMode === ANNOTATION_TYPES.SELECT) return;

    const currentColor = (typeof window !== 'undefined' && window.currentAnnotationColor) || '#FFEB3B';

    const payload = {
      type: annotationMode.toUpperCase(),
      page_number: selection.pageNumber,
      quads: selection.quads,
      selected_text: selection.text,
      color: currentColor
    };
    
    try {
      const created = await createAnnotation(workspaceId, selectedPdf.id, payload);
      const transformed = transformAnnotation(created);
      setSelectedAnnotation(transformed);
      const list = await listAnnotations(workspaceId, selectedPdf.id);
      // Transform all annotations
      const transformedList = list.map(transformAnnotation);
      setAnnotations(transformedList);
    } catch (error) {
      console.error('Failed to create annotation:', error);
      alert('Failed to create annotation: ' + (error.message || 'Unknown error'));
    }
  };

  const handleStartChat = async (selectionData) => {
    if (!workspaceId || !selectedPdf?.id) return;
    
    try {
      const newThread = await createThread(workspaceId, selectedPdf.id, {
        page_number: selectionData.pageNumber,
        selection_text: selectionData.text,
        anchor_rect: selectionData.anchorRect,
        anchor_side: 'right'
      });
      
      // Open Threaded Discussions panel and select the new thread
      setSelectedThreadId(newThread.id);
    } catch (error) {
      console.error('Failed to create thread:', error);
      alert('Failed to create thread: ' + (error.message || 'Unknown error'));
    }
  };

  const handleAnchorClick = (threadId) => {
    setSelectedThreadId(threadId);
    // Switch to threads tab in sidebar (this will be handled by PdfSidebar)
  };
  
  const handleUndoLast = async () => {
    if (!annotations.length) return;
    const last = annotations[annotations.length - 1];
    await deleteAnnotation(workspaceId, selectedPdf.id, last.id);
    const list = await listAnnotations(workspaceId, selectedPdf.id);
    // Transform all annotations to ensure consistent format
    const transformedList = list.map(transformAnnotation);
    setAnnotations(transformedList);
  };

  const handleDeletePdf = async () => {
    if (!pdfToDelete) return;
    setIsDeleting(true);
    try {
      await deletePdf(pdfToDelete);
      // Remove from PDFs list
      setPdfs(prev => prev.filter(pdf => pdf.id !== pdfToDelete));
      // If deleted PDF was selected, clear selection
      if (selectedPdf?.id === pdfToDelete) {
        setSelectedPdf(null);
        setAnnotations([]);
      }
      setShowDeleteModal(false);
      setPdfToDelete(null);
    } catch (error) {
      console.error('Error deleting PDF:', error);
      alert('Failed to delete PDF: ' + (error.message || 'Unknown error'));
    } finally {
      setIsDeleting(false);
    }
  };

  const filteredPdfs = pdfs.filter(pdf => 
    pdf.name.toLowerCase().includes(pdfSearchQuery.toLowerCase())
  );

  const handleInviteSuccess = async () => {
    if (workspaceId && user?.id) {
      await loadWorkspaceMembers(workspaceId, user.id);
    }
  };

  const handleRoleUpdate = async () => {
    if (workspaceId && user?.id) {
      await loadWorkspaceMembers(workspaceId, user.id);
    }
  };

  if (!workspace) {
    return (
      <div className="min-h-screen" style={{ background: 'var(--bg-color)' }}>
        <Navbar />
        <div className="flex items-center justify-center h-[80vh]">
          <p style={{ color: 'var(--muted-text)' }}>Workspace not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden" style={{ background: 'var(--bg-color)' }}>
      <Navbar />
      
      <div className="px-6 py-4 flex-shrink-0" style={{ borderBottom: '1px solid var(--border-color)', background: 'var(--panel-color)' }}>
        <div className="max-w-[1400px] mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-color)' }}>{workspace.name}</h1>
          <RoleBadge
            role={currentWorkspaceRole[workspaceId]}
            isCreator={isWorkspaceCreator[workspaceId]}
            onClick={() => setShowMembersPanel(!showMembersPanel)}
          />
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden min-h-0">
        <div className="w-64 flex flex-col" style={{ background: 'var(--panel-color)', borderRight: '1px solid var(--border-color)' }}>
          <div className="p-4" style={{ borderBottom: '1px solid var(--border-color)' }}>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              onChange={handleFileUpload}
              className="hidden"
              data-testid="input-file-upload"
            />
            <Button
              onClick={() => fileInputRef.current?.click()}
              variant="primary"
              className="w-full flex items-center justify-center gap-2"
              data-testid="button-upload-pdf"
              disabled={isUploading}
            >
              <Icon name="upload" size={18} />
              {isUploading ? 'Uploading...' : 'Upload PDF'}
            </Button>
          </div>

          <div className="p-4" style={{ borderBottom: '1px solid var(--border-color)' }}>
            <input
              type="text"
              placeholder="Search PDFs..."
              value={pdfSearchQuery}
              onChange={(e) => setPdfSearchQuery(e.target.value)}
              className="w-full px-3 py-2 rounded-md focus:outline-none"
              style={{ 
                background: 'var(--hover-bg)', 
                border: '1px solid var(--border-color)', 
                color: 'var(--text-color)'
              }}
              data-testid="input-search-pdfs"
            />
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {filteredPdfs.map(pdf => (
              <div
                key={pdf.id}
                className={`pdf-item group w-full text-left p-3 rounded-md transition-colors ${
                  selectedPdf?.id === pdf.id ? 'active' : ''
                }`}
                style={selectedPdf?.id === pdf.id
                  ? { background: 'var(--accent-color)', color: '#fff' }
                  : { background: 'var(--hover-bg)', color: 'var(--text-color)' }
                }
                onMouseEnter={(e) => {
                  if (selectedPdf?.id !== pdf.id) e.currentTarget.style.background = 'var(--border-color)';
                }}
                onMouseLeave={(e) => {
                  if (selectedPdf?.id !== pdf.id) e.currentTarget.style.background = 'var(--hover-bg)';
                }}
                data-filename={pdf.name}
              >
                <div className="flex items-start gap-2">
                  <button
                    onClick={() => setSelectedPdf(pdf)}
                    className="flex-1 min-w-0 text-left"
                    data-testid={`button-select-pdf-${pdf.id}`}
                  >
                    <div className="flex items-start gap-2">
                      <Icon name="file" size={16} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{pdf.name}</p>
                        <p className="text-xs opacity-75 mt-1">
                          {new Date(pdf.uploadedAt).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  </button>
                  {currentWorkspaceRole[workspaceId] === 'RESEARCHER' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setPdfToDelete(pdf.id);
                        setShowDeleteModal(true);
                      }}
                      className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-600/20 rounded"
                      data-testid={`button-delete-pdf-${pdf.id}`}
                      title="Delete PDF"
                    >
                      <Icon name="trash" size={16} className="text-red-400" />
                    </button>
                  )}
                </div>
              </div>
            ))}
            {filteredPdfs.length === 0 && pdfs.length > 0 && (
              <p className="text-center text-sm py-4" style={{ color: 'var(--muted-text)' }}>No PDFs match your search</p>
            )}
          </div>

          <InviteUserPanel
            workspaceId={workspaceId}
            onInviteSuccess={handleInviteSuccess}
            currentUserRole={currentWorkspaceRole[workspaceId]}
          />

          <WorkspaceMembersPanel
            members={workspaceMembers[workspaceId] || []}
            workspaceId={workspaceId}
            isCreator={isWorkspaceCreator[workspaceId]}
            currentUserId={user?.id}
            onRoleUpdate={handleRoleUpdate}
          />

          <PinnedNotesPanel
            workspaceId={workspaceId}
            currentUserRole={currentWorkspaceRole[workspaceId]}
          />
        </div>

        <div className="flex-1 flex flex-col min-h-0">
          {selectedPdf ? (
            <>
              <PdfToolbar
                activeMode={annotationMode}
                onModeChange={setAnnotationMode}
                onUndo={handleUndoLast}
              />
              {selectedPdf.url ? (
                <PdfViewer
                  url={selectedPdf.url}
                  onTextSelect={handleTextSelect}
                  annotations={annotations}
                  threads={threadsByPdf[selectedPdf.id] || []}
                  onStartChat={handleStartChat}
                  onAnchorClick={handleAnchorClick}
                  annotationMode={annotationMode}
                />
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <p style={{ color: 'var(--muted-text)' }}>Loading PDF...</p>
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <p style={{ color: 'var(--muted-text)' }}>
                {pdfs.length === 0
                  ? 'Upload a PDF to get started'
                  : 'Select a PDF from the sidebar'}
              </p>
            </div>
          )}
        </div>

        <PdfSidebar
          workspaceId={workspaceId}
          pdfId={selectedPdf?.id}
          selectedAnnotation={selectedAnnotation}
          userRole={currentWorkspaceRole[workspaceId]}
          selectedThreadId={selectedThreadId}
          onThreadSelect={setSelectedThreadId}
        />
      </div>

      <Modal
        isOpen={showDeleteModal}
        onClose={() => !isDeleting && setShowDeleteModal(false)}
        title="Delete PDF"
      >
        <div className="space-y-4">
          <p style={{ color: 'var(--text-color)' }}>
            Are you sure you want to delete this PDF?
          </p>
          <div className="flex gap-2 justify-end">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setShowDeleteModal(false);
                setPdfToDelete(null);
              }}
              disabled={isDeleting}
              data-testid="button-cancel-delete-pdf"
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="primary"
              onClick={handleDeletePdf}
              disabled={isDeleting}
              className="bg-red-600 hover:bg-red-700"
              data-testid="button-confirm-delete-pdf"
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
