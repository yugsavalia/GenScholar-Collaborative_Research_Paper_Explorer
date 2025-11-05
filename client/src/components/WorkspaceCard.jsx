import { Link } from 'wouter';

export default function WorkspaceCard({ workspace }) {
  return (
    <Link to={`/workspace/${workspace.id}`} data-testid={`card-workspace-${workspace.id}`}>
      <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-6 hover:border-[#4FC3F7] transition-colors cursor-pointer">
        <h3 className="text-xl font-semibold text-[#E0E0E0] mb-2">{workspace.name}</h3>
        <p className="text-[#BDBDBD] text-sm mb-4 line-clamp-2">{workspace.description}</p>
        <p className="text-xs text-[#BDBDBD]">
          Created {new Date(workspace.createdAt).toLocaleDateString()}
        </p>
      </div>
    </Link>
  );
}
