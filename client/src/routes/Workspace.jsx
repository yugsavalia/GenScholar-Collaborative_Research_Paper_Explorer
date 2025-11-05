import { useState, useEffect, useRef } from 'react';
import { useRoute } from 'wouter';
import { useApp } from '../context/AppContext';
import { storage } from '../utils/storage';
import { STORAGE_KEYS, ANNOTATION_TYPES } from '../utils/constants';
import { generateId } from '../utils/ids';
import Navbar from '../components/Navbar';
import PdfViewer from '../components/PdfViewer';
import PdfToolbar from '../components/PdfToolbar';
import PdfSidebar from '../components/PdfSidebar';
import Icon from '../components/Icon';
import Button from '../components/Button';

export default function Workspace() {
  const [, params] = useRoute('/workspace/:id');
  const workspaceId = params?.id;
  
  const { workspaces, getPdfs, addPdf } = useApp();
  const workspace = workspaces.find(w => w.id === workspaceId);
  
  const [pdfs, setPdfs] = useState([]);
  const [selectedPdf, setSelectedPdf] = useState(null);
  const [annotationMode, setAnnotationMode] = useState(ANNOTATION_TYPES.SELECT);
  const [selectedAnnotation, setSelectedAnnotation] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (workspaceId) {
      const workspacePdfs = getPdfs(workspaceId);
      setPdfs(workspacePdfs);
      if (workspacePdfs.length > 0 && !selectedPdf) {
        setSelectedPdf(workspacePdfs[0]);
      }
    }
  }, [workspaceId, getPdfs]);

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file || !workspaceId) return;

    const url = URL.createObjectURL(file);
    const newPdf = addPdf(workspaceId, file.name, url);
    
    const updatedPdfs = getPdfs(workspaceId);
    setPdfs(updatedPdfs);
    setSelectedPdf(newPdf);
  };

  const handleTextSelect = (selection) => {
    if (annotationMode === ANNOTATION_TYPES.SELECT) return;

    const annotation = {
      id: generateId(),
      selectionId: generateId(),
      type: annotationMode,
      pageNumber: selection.pageNumber,
      rects: selection.rects,
      text: selection.text,
      createdAt: new Date().toISOString()
    };

    const annotations = storage.get(STORAGE_KEYS.ANNOTATIONS(workspaceId, selectedPdf.id)) || [];
    const updated = [...annotations, annotation];
    storage.set(STORAGE_KEYS.ANNOTATIONS(workspaceId, selectedPdf.id), updated);
    
    setSelectedAnnotation(annotation);
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
          <div className="flex gap-2">
            <div className="w-8 h-8 rounded-full bg-[#4FC3F7] flex items-center justify-center text-white text-sm">
              A
            </div>
            <div className="w-8 h-8 rounded-full bg-[#EF5350] flex items-center justify-center text-white text-sm">
              B
            </div>
          </div>
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
            >
              <Icon name="upload" size={18} />
              Upload PDF
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
        </div>

        <div className="flex-1 flex flex-col">
          {selectedPdf ? (
            <>
              <PdfToolbar
                activeMode={annotationMode}
                onModeChange={setAnnotationMode}
              />
              <PdfViewer
                url={selectedPdf.url}
                onTextSelect={handleTextSelect}
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
        />
      </div>
    </div>
  );
}
