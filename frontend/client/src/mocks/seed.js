import { storage } from '../utils/storage';
import { STORAGE_KEYS } from '../utils/constants';
import { generateId } from '../utils/ids';

export const initializeSeedData = () => {
  const hasSeeded = storage.get('gs_seeded');
  if (hasSeeded) return;

  const workspaceId = generateId();
  const workspace = {
    id: workspaceId,
    name: 'Machine Learning Research',
    description: 'Collaborative space for ML paper reviews and discussions',
    createdAt: new Date('2024-01-15').toISOString(),
    updatedAt: new Date('2024-01-15').toISOString()
  };

  storage.set(STORAGE_KEYS.WORKSPACES, [workspace]);

  const pdfId = generateId();
  const pdf = {
    id: pdfId,
    name: 'Sample Research Paper.pdf',
    url: 'https://arxiv.org/pdf/1706.03762.pdf',
    uploadedAt: new Date('2024-01-15').toISOString()
  };

  storage.set(STORAGE_KEYS.PDFS(workspaceId), [pdf]);

  const selectionId = generateId();
  const annotations = [
    {
      id: selectionId,
      selectionId: selectionId,
      type: 'highlight',
      pageNumber: 1,
      rects: [{ x: 100, y: 200, w: 300, h: 20 }],
      text: 'Attention mechanisms have become an integral part',
      createdAt: new Date('2024-01-16').toISOString()
    }
  ];

  storage.set(STORAGE_KEYS.ANNOTATIONS(workspaceId, pdfId), annotations);

  const threadMessages = [
    {
      id: generateId(),
      author: 'other',
      content: 'This is a key finding in the paper',
      createdAt: new Date('2024-01-16T10:00:00').toISOString()
    },
    {
      id: generateId(),
      author: 'me',
      content: 'Agreed! The attention mechanism really changed the game',
      createdAt: new Date('2024-01-16T10:05:00').toISOString()
    }
  ];

  storage.set(STORAGE_KEYS.THREADS(workspaceId, pdfId, selectionId), threadMessages);

  const mainChatMessages = [
    {
      id: generateId(),
      author: 'other',
      content: 'Welcome to the workspace!',
      createdAt: new Date('2024-01-15T09:00:00').toISOString()
    },
    {
      id: generateId(),
      author: 'me',
      content: 'Thanks! Excited to collaborate',
      createdAt: new Date('2024-01-15T09:05:00').toISOString()
    }
  ];

  storage.set(STORAGE_KEYS.MAIN_CHAT(workspaceId), mainChatMessages);

  const botMessages = [
    {
      id: generateId(),
      role: 'user',
      content: 'Can you summarize this paper?',
      createdAt: new Date('2024-01-16T14:00:00').toISOString()
    },
    {
      id: generateId(),
      role: 'assistant',
      content: 'AI: This paper introduces the Transformer architecture. This is a mock response.',
      createdAt: new Date('2024-01-16T14:00:05').toISOString()
    }
  ];

  storage.set(STORAGE_KEYS.BOT(workspaceId), botMessages);

  storage.set('gs_seeded', true);
  console.log('Seed data initialized');
};
