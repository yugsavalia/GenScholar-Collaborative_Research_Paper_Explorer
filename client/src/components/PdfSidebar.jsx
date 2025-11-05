import { useState } from 'react';
import MainChat from './MainChat';
import ThreadPanel from './ThreadPanel';
import ChatbotPanel from './ChatbotPanel';

export default function PdfSidebar({ workspaceId, pdfId, selectedAnnotation }) {
  const [activeTab, setActiveTab] = useState('main');

  return (
    <div className="w-[360px] bg-[#1E1E1E] border-l border-[#2A2A2A] flex flex-col h-full">
      <div className="sidebar-tabs flex border-b border-[#2A2A2A]">
        <button
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'main'
              ? 'text-[#4FC3F7] border-b-2 border-[#4FC3F7]'
              : 'text-[#BDBDBD] hover:text-[#E0E0E0]'
          }`}
          onClick={() => setActiveTab('main')}
          data-testid="button-tab-main"
        >
          Main Chat
        </button>
        <button
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'threads'
              ? 'text-[#4FC3F7] border-b-2 border-[#4FC3F7]'
              : 'text-[#BDBDBD] hover:text-[#E0E0E0]'
          }`}
          onClick={() => setActiveTab('threads')}
          data-testid="button-tab-threads"
        >
          Threaded Discussions
        </button>
        <button
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'bot'
              ? 'text-[#4FC3F7] border-b-2 border-[#4FC3F7]'
              : 'text-[#BDBDBD] hover:text-[#E0E0E0]'
          }`}
          onClick={() => setActiveTab('bot')}
          data-testid="button-tab-bot"
        >
          AI ChatBot
        </button>
      </div>
      
      <div className="sidebar-content flex-1 overflow-hidden">
        {activeTab === 'main' && <MainChat workspaceId={workspaceId} />}
        {activeTab === 'threads' && (
          <ThreadPanel 
            workspaceId={workspaceId} 
            pdfId={pdfId} 
            selectedAnnotation={selectedAnnotation}
          />
        )}
        {activeTab === 'bot' && <ChatbotPanel workspaceId={workspaceId} />}
      </div>
    </div>
  );
}
