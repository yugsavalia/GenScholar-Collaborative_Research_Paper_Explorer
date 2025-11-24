import { useState, useEffect } from 'react';
import { storage } from '../utils/storage';
import { STORAGE_KEYS } from '../utils/constants';
import { generateId } from '../utils/ids';
import ThreadItem from './ThreadItem';

export default function ThreadPanel({ workspaceId, pdfId, selectedAnnotation }) {
  const [threads, setThreads] = useState([]);
  const [selectedThread, setSelectedThread] = useState(null);

  useEffect(() => {
    if (!selectedAnnotation || !pdfId) return;
    
    const key = STORAGE_KEYS.THREADS(workspaceId, pdfId, selectedAnnotation.id);
    const saved = storage.get(key) || [];
    setThreads(saved);
  }, [workspaceId, pdfId, selectedAnnotation]);

  const addMessage = (content) => {
    if (!selectedAnnotation || !pdfId) return;
    
    const newMessage = {
      id: generateId(),
      author: 'me',
      content,
      createdAt: new Date().toISOString()
    };

    const key = STORAGE_KEYS.THREADS(workspaceId, pdfId, selectedAnnotation.id);
    const updated = [...threads, newMessage];
    setThreads(updated);
    storage.set(key, updated);
  };

  if (!selectedAnnotation || !pdfId) {
    return (
      <div className="flex items-center justify-center h-full p-4">
        <p className="text-[#BDBDBD] text-center">
          Select text in the PDF to start a threaded discussion
        </p>
      </div>
    );
  }

  return (
    <div className="h-full">
      <ThreadItem 
        selectionText={selectedAnnotation.text}
        messages={threads}
        onAddMessage={addMessage}
        workspaceId={workspaceId}
      />
    </div>
  );
}
