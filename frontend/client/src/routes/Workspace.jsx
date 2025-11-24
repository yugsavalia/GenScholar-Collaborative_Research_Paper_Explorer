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
import Icon from '../components/Icon';
import Button from '../components/Button';
import { listAnnotations, createAnnotation, deleteAnnotation } from '../api/annotations';

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
    changeMemberRole
  } = useApp();
  const { user } = useAuth();
  const workspace = workspaces.find(w => w.id === workspaceId);
  
  const [pdfs, setPdfs] = useState([]);
  const [selectedPdf, setSelectedPdf] = useState(null);
  const [annotationMode, setAnnotationMode] = useState(ANNOTATION_TYPES.SELECT);
  const [selectedAnnotation, setSelectedAnnotation] = useState(null);
  const [annotations, setAnnotations] = useState([]);
  const [showMembersPanel, setShowMembersPanel] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
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

  // Load PDFs when workspace changes
  useEffect(() => {
    if (workspaceId) {
      const loadPdfs = async () => {
        const workspacePdfs = await getPdfs(workspaceId);
        setPdfs(workspacePdfs);
        pdfsRef.current = workspacePdfs; // Update ref for cleanup
        // Only auto-select first PDF if no PDF is currently selected
        if (workspacePdfs.length > 0 && !selectedPdf) {
          setSelectedPdf(workspacePdfs[0]);
        }
      };
      loadPdfs();
    }
  }, [workspaceId, getPdfs]); // Removed selectedPdf from dependencies to prevent reload loops

  // Update ref when PDFs change
  useEffect(() => {
    pdfsRef.current = pdfs;
  }, [pdfs]);

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
      
      // Append new PDF to existing list (newest first)
      setPdfs(prev => [newPdf, ...prev]);
      
      // Select the newly uploaded PDF
      setSelectedPdf(newPdf);
    } catch (err) {
      console.error('Failed to upload file:', err);
      alert('Failed to upload PDF: ' + (err.message || 'Unknown error'));
    } finally {
      setIsUploading(false);
    }
  };

  useEffect(() => {
    const load = async () => {
      if (!workspaceId || !selectedPdf?.id) return;
      const list = await listAnnotations(workspaceId, selectedPdf.id);
      setAnnotations(list);
    };
    load();
  }, [workspaceId, selectedPdf?.id]);

  const handleTextSelect = (selection) => {
    if (annotationMode === ANNOTATION_TYPES.SELECT) return;

    const payload = {
      type: annotationMode.toUpperCase(),
      page_number: selection.pageNumber,
      quads: selection.quads,
      selected_text: selection.text,
      color: annotationMode === ANNOTATION_TYPES.HIGHLIGHT ? '#FFFF00' : '#FFFF00'
    };
    createAnnotation(workspaceId, selectedPdf.id, payload).then((created) => {
      setSelectedAnnotation(created);
      return listAnnotations(workspaceId, selectedPdf.id).then(setAnnotations);
    });
  };
  
  const handleUndoLast = async () => {
    if (!annotations.length) return;
    const last = annotations[annotations.length - 1];
    await deleteAnnotation(workspaceId, selectedPdf.id, last.id);
    const list = await listAnnotations(workspaceId, selectedPdf.id);
    setAnnotations(list);
  };

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
      <div className="min-h-screen bg-[#121212]">
        <Navbar />
        <div className="flex items-center justify-center h-[80vh]">
          <p className="text-[#BDBDBD]">Workspace not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#121212] flex flex-col">
      <Navbar />
      
      <div className="border-b border-[#2A2A2A] bg-[#1E1E1E] px-6 py-4">
        <div className="max-w-[1400px] mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-[#E0E0E0]">{workspace.name}</h1>
          <RoleBadge
            role={currentWorkspaceRole[workspaceId]}
            isCreator={isWorkspaceCreator[workspaceId]}
            onClick={() => setShowMembersPanel(!showMembersPanel)}
          />
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-64 bg-[#1E1E1E] border-r border-[#2A2A2A] flex flex-col">
          <div className="p-4 border-b border-[#2A2A2A]">
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

          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {pdfs.map(pdf => (
              <button
                key={pdf.id}
                onClick={() => setSelectedPdf(pdf)}
                className={`w-full text-left p-3 rounded-md transition-colors ${
                  selectedPdf?.id === pdf.id
                    ? 'bg-[#4FC3F7] text-white'
                    : 'bg-[#2A2A2A] text-[#E0E0E0] hover:bg-[#3A3A3A]'
                }`}
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
            ))}
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
        </div>

        <div className="flex-1 flex flex-col">
          {selectedPdf ? (
            <>
              <PdfToolbar
                activeMode={annotationMode}
                onModeChange={setAnnotationMode}
              />
              <div className="px-4 py-2 bg-[#1E1E1E] border-b border-[#2A2A2A]">
                <button
                  onClick={handleUndoLast}
                  className="px-3 py-1 bg-[#2A2A2A] text-[#E0E0E0] rounded"
                  data-testid="button-undo-annotation"
                >
                  Undo last annotation
                </button>
              </div>
              <PdfViewer
                url={selectedPdf.url}
                onTextSelect={handleTextSelect}
                annotations={annotations}
              />
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-[#BDBDBD]">
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
        />
      </div>
    </div>
  );
}
