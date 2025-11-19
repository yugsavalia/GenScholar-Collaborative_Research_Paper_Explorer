import Icon from './Icon';
import { ANNOTATION_TYPES } from '../utils/constants';

export default function PdfToolbar({ activeMode, onModeChange }) {
  const tools = [
    { name: ANNOTATION_TYPES.SELECT, icon: 'cursor', label: 'Select' },
    { name: ANNOTATION_TYPES.HIGHLIGHT, icon: 'highlight', label: 'Highlight' },
    { name: ANNOTATION_TYPES.UNDERLINE, icon: 'underline', label: 'Underline' },
    { name: ANNOTATION_TYPES.TEXTBOX, icon: 'text', label: 'Text Box' }
  ];

  return (
    <div className="flex gap-2 p-4 bg-[#1E1E1E] border-b border-[#2A2A2A]">
      {tools.map(tool => (
        <button
          key={tool.name}
          onClick={() => onModeChange(tool.name)}
          className={`px-4 py-2 rounded flex items-center gap-2 transition-colors ${
            activeMode === tool.name
              ? 'bg-[#4FC3F7] text-white'
              : 'bg-[#2A2A2A] text-[#E0E0E0] hover:bg-[#3A3A3A]'
          }`}
          data-testid={`button-tool-${tool.name}`}
        >
          <Icon name={tool.icon} size={18} />
          <span>{tool.label}</span>
        </button>
      ))}
    </div>
  );
}
