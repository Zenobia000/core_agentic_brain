import { useState, useEffect } from 'react';
import { ChevronRight, ChevronDown, Hourglass } from 'lucide-react';
import { ThinkingUpdate } from '../services/api';

interface ThinkingPanelProps {
  thinkingState: ThinkingUpdate | null;
}

export function ThinkingPanel({ thinkingState }: ThinkingPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (thinkingState?.steps && thinkingState.steps.length > 0) {
      setIsExpanded(true);
    }
  }, [thinkingState]);

  if (!thinkingState) {
    return null;
  }

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
        <span className="text-[#00ff00] text-glow">THINKING</span>
        <span className="ml-auto text-[#00ff00] opacity-60 text-glow">
          {thinkingState.summary}
        </span>
        <Hourglass className="ml-2 h-3 w-3 animate-pulse text-[#00ff00]" />
      </button>

      {isExpanded && thinkingState.steps && (
        <div className="px-4 pb-4 pl-12 space-y-1">
          {thinkingState.steps.map((step, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <span className="text-[#00ff00] text-glow">
                {idx === thinkingState.steps!.length - 1 ? '└──' : '├──'}
              </span>
              <span className="text-[#00ff00] text-glow">{step}</span>
              {idx === thinkingState.steps!.length - 1 && (
                <Hourglass className="ml-2 h-3 w-3 animate-pulse text-[#00ff00]" />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
