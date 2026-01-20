import { Hourglass, CheckCircle, XCircle, Zap } from 'lucide-react';
import { TaskUpdate } from '../services/api';

interface HeaderProps {
  taskState: TaskUpdate | null;
}

const StatusIndicator = ({ status }: { status?: string | null }) => {
  if (!status) return <span className="text-[#00ff00]">Ready</span>;

  switch (status) {
    case 'Thinking...':
      return <span className="text-[#00ffff] animate-pulse">Thinking...</span>;
    case 'Waiting for input...':
      return <span className="text-[#ffcc00]">Waiting for input...</span>;
    case 'Completed':
      return <span className="text-[#00ff00]">✓ Completed</span>;
    case 'Error':
      return <span className="text-[#ff3333]">✗ Error</span>;
    default:
      return (
        <div className="flex items-center gap-2">
          <span className="text-[#00ff00]">Tool: {status}</span>
          <Zap className="h-4 w-4 animate-pulse text-[#00ff00]" />
        </div>
      );
  }
};

export function Header({ taskState }: HeaderProps) {
  return (
    <div className="flex items-center justify-between border-b border-[#00ff00] px-4 py-2 text-glow">
      <div className="flex-1">
        <span className="text-[#00ff00]">
          [Task] {taskState?.name || 'No active task'}
        </span>
      </div>
      <div className="flex-1 text-center">
        {taskState && (
          <span className="text-[#00ff00]">
            Phase {taskState.currentPhase}/{taskState.totalPhases} {taskState.phaseName}
          </span>
        )}
      </div>
      <div className="flex flex-1 items-center justify-end gap-2">
        <StatusIndicator status={taskState?.waitingFor} />
      </div>
    </div>
  );
}
