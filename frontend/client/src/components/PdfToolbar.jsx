import Icon from './Icon';
import { ANNOTATION_TYPES } from '../utils/constants';
import ColorPicker from './ColorPicker';

export default function PdfToolbar({ activeMode, onModeChange, onUndo }) {
  const tools = [
    { name: ANNOTATION_TYPES.SELECT, icon: 'cursor', label: 'Select' },
    { name: ANNOTATION_TYPES.HIGHLIGHT, icon: 'highlight', label: 'Highlight' },
    { name: ANNOTATION_TYPES.UNDERLINE, icon: 'underline', label: 'Underline' }
  ];

  return (
    <div className="flex gap-2 px-4 py-2" style={{ background: 'var(--panel-color)', borderBottom: '1px solid var(--border-color)' }}>
      {tools.map(tool => (
        <button
          key={tool.name}
          onClick={() => onModeChange(tool.name)}
          className="px-4 py-2 rounded flex items-center gap-2 transition-colors"
          style={activeMode === tool.name
            ? { background: 'var(--accent-color)', color: '#ffffff', border: 'none' }
            : { background: 'var(--hover-bg)', color: 'var(--text-color)' }
          }
          onMouseEnter={(e) => {
            if (activeMode !== tool.name) {
              e.target.style.background = 'var(--border-color)';
            } else {
              e.target.style.background = 'var(--accent-color)';
            }
          }}
          onMouseLeave={(e) => {
            if (activeMode !== tool.name) {
              e.target.style.background = 'var(--hover-bg)';
            } else {
              e.target.style.background = 'var(--accent-color)';
            }
          }}
          data-testid={`button-tool-${tool.name}`}
        >
          <Icon name={tool.icon} size={18} style={{ color: activeMode === tool.name ? '#ffffff' : 'inherit' }} />
          <span>{tool.label}</span>
        </button>
      ))}
      <ColorPicker />
      {onUndo && (
        <button
          onClick={onUndo}
          className="px-4 py-2 rounded flex items-center gap-2 transition-colors"
          style={{ background: 'var(--hover-bg)', color: 'var(--text-color)' }}
          onMouseEnter={(e) => e.target.style.background = 'var(--border-color)'}
          onMouseLeave={(e) => e.target.style.background = 'var(--hover-bg)'}
          data-testid="button-undo-annotation"
        >
          <Icon name="undo" size={18} />
          <span>Undo Last Annotation</span>
        </button>
      )}
    </div>
  );
}
