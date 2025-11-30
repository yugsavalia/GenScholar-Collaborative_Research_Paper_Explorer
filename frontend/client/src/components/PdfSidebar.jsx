import { useState, useEffect } from 'react';
import MainChat from './MainChat';
import ThreadPanel from './ThreadPanel';
import ThreadedDiscussions from './ThreadedDiscussions';
import ChatbotPanel from './ChatbotPanel';

export default function PdfSidebar({ workspaceId, pdfId, selectedAnnotation, userRole, selectedThreadId, onThreadSelect }) {
  const [activeTab, setActiveTab] = useState('main');
  const isReviewer = userRole === 'REVIEWER';

  // Switch to threads tab when a thread is selected
  useEffect(() => {
    if (selectedThreadId) {
      setActiveTab('threads');
    }
  }, [selectedThreadId]);

  // Reset to main tab if reviewer tries to access restricted tabs
  useEffect(() => {
    if (isReviewer && activeTab === 'bot') {
      setActiveTab('main');
    }
  }, [isReviewer, activeTab]);

  // Ensure activeTab is not 'bot' for reviewers
  const safeActiveTab = isReviewer && activeTab === 'bot' ? 'main' : activeTab;

  const handleTabClick = (tab) => {
    if (isReviewer && tab === 'bot') {
      return; // Prevent switching to bot tab
    }
    setActiveTab(tab);
  };

  return (
    <div className="w-[360px] flex flex-col h-full min-h-0" style={{ background: 'var(--panel-color)', borderLeft: '1px solid var(--border-color)' }}>
      <div className="sidebar-tabs flex flex-shrink-0" style={{ borderBottom: '1px solid var(--border-color)' }}>
        <button
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            safeActiveTab === 'main' ? 'border-b-2' : ''
          }`}
          style={safeActiveTab === 'main' 
            ? { color: 'var(--accent-color)', borderBottomColor: 'var(--accent-color)' }
            : { color: 'var(--muted-text)' }
          }
          onMouseEnter={(e) => {
            if (safeActiveTab !== 'main') e.target.style.color = 'var(--text-color)';
          }}
          onMouseLeave={(e) => {
            if (safeActiveTab !== 'main') e.target.style.color = 'var(--muted-text)';
          }}
          onClick={() => handleTabClick('main')}
          data-testid="button-tab-main"
        >
          Main Chat
        </button>
        <button
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            safeActiveTab === 'threads' ? 'border-b-2' : ''
          }`}
          style={safeActiveTab === 'threads' 
            ? { color: 'var(--accent-color)', borderBottomColor: 'var(--accent-color)' }
            : { color: 'var(--muted-text)' }
          }
          onMouseEnter={(e) => {
            if (safeActiveTab !== 'threads') e.target.style.color = 'var(--text-color)';
          }}
          onMouseLeave={(e) => {
            if (safeActiveTab !== 'threads') e.target.style.color = 'var(--muted-text)';
          }}
          onClick={() => handleTabClick('threads')}
          data-testid="button-tab-threads"
        >
          Threaded Discussions
        </button>
        {!isReviewer && (
          <button
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              safeActiveTab === 'bot' ? 'border-b-2' : ''
            }`}
            style={safeActiveTab === 'bot' 
              ? { color: 'var(--accent-color)', borderBottomColor: 'var(--accent-color)' }
              : { color: 'var(--muted-text)' }
            }
            onMouseEnter={(e) => {
              if (safeActiveTab !== 'bot') e.target.style.color = 'var(--text-color)';
            }}
            onMouseLeave={(e) => {
              if (safeActiveTab !== 'bot') e.target.style.color = 'var(--muted-text)';
            }}
            onClick={() => handleTabClick('bot')}
            data-testid="button-tab-bot"
          >
            AI ChatBot
          </button>
        )}
      </div>
      
      <div className="sidebar-content flex-1 overflow-hidden min-h-0 flex flex-col">
        {safeActiveTab === 'main' && <MainChat workspaceId={workspaceId} />}
        {safeActiveTab === 'threads' && (
          <ThreadedDiscussions
            workspaceId={workspaceId}
            pdfId={pdfId}
            selectedThreadId={selectedThreadId}
            onThreadSelect={onThreadSelect}
          />
        )}
        {!isReviewer && safeActiveTab === 'bot' && <ChatbotPanel workspaceId={workspaceId} />}
      </div>
    </div>
  );
}
