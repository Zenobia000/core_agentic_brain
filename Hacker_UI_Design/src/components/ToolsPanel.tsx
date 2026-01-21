import { useState, useEffect } from 'react';
import { ChevronRight, ChevronDown, CheckCircle, XCircle, Zap } from 'lucide-react';
import { ToolEvent } from '../services/api';

interface ToolsPanelProps {
  toolEvents: ToolEvent[];
}

const StatusIcon = ({ status }: { status: string }) => {
  switch (status) {
    case 'running':
      return <Zap className="h-3 w-3 animate-pulse text-[#00ffff]" />;
    case 'success':
      return <CheckCircle className="h-3 w-3 text-[#00ff00]" />;
    case 'error':
      return <XCircle className="h-3 w-3 text-[#ff3333]" />;
    default:
      return null;
  }
};

export function ToolsPanel({ toolEvents }: ToolsPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (toolEvents.length > 0) {
      setIsExpanded(true);
    }
  }, [toolEvents]);

  if (toolEvents.length === 0) {
    return null;
  }

  const successCount = toolEvents.filter((e) => e.status === 'success').length;

  return (
    <div className="border-b border-t border-[#00ff00]">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center gap-2 px-4 py-2 text-left hover:bg-[#00ff00] hover:bg-opacity-5 transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 text-[#00ff00]" />
        ) : (
          <ChevronRight className="h-4 w-4 text-[#00ff00]" />
        )}
        <span className="text-[#00ff00] text-glow">TOOLS</span>
        <span className="ml-auto text-[#00ff00] opacity-60 text-glow">
          {toolEvents.length} calls ({successCount} success)
        </span>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-3">
          {toolEvents.map((call, idx) => (
            <div key={idx} className="pl-8">
              <div className="flex items-center gap-2">
                <span className="text-[#00ff00] opacity-60 text-glow">
                  [{new Date(call.timestamp).toLocaleTimeString()}]
                </span>
                <StatusIcon status={call.status} />
                <span className="text-[#00ff00] text-glow">
                  {call.tool}
                  {call.result && (
                    <span className="ml-2 opacity-80">→ {call.result}</span>
                  )}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
