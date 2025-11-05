export const STORAGE_KEYS = {
  AUTH: 'gs_auth',
  WORKSPACES: 'gs_workspaces',
  PDFS: (workspaceId) => `gs_pdfs::${workspaceId}`,
  ANNOTATIONS: (workspaceId, pdfId) => `gs_annotations::${workspaceId}::${pdfId}`,
  THREADS: (workspaceId, pdfId, selectionId) => `gs_threads::${workspaceId}::${pdfId}::${selectionId}`,
  BOT: (workspaceId) => `gs_bot::${workspaceId}`,
  MAIN_CHAT: (workspaceId) => `gs_mainchat::${workspaceId}`
};

export const ANNOTATION_TYPES = {
  HIGHLIGHT: 'highlight',
  UNDERLINE: 'underline',
  TEXTBOX: 'textbox',
  SELECT: 'select'
};
