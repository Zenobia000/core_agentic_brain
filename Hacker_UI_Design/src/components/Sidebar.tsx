import { Circle } from 'lucide-react';
import { ContextUpdate } from '../services/api';

interface SidebarProps {
  contextData: ContextUpdate | null;
  isConnected: boolean;
  todoItems: any[];
}

export function Sidebar({ contextData, isConnected, todoItems }: SidebarProps) {
  return (
    <div className="flex flex-col gap-6 p-4">
      {/* Context Block */}
      <div className="space-y-2">
        <div className="text-[#00ff00] text-glow">[CONTEXT]</div>
        <div className="space-y-1 pl-4 text-sm">
          {contextData ? (
            <>
              <div className="text-[#00ff00] text-glow">
                Tokens: {contextData.tokens[0]}/{contextData.tokens[1]} (
                {Math.round((contextData.tokens[0] / contextData.tokens[1]) * 100)}%)
              </div>
              <div className="text-[#00ff00] text-glow">Model: {contextData.model}</div>
              <div className="text-[#00ff00] text-glow">Latency: avg {contextData.latency.toFixed(2)}s</div>
            </>
          ) : (
            <div className="text-[#006600]">No context data</div>
          )}
        </div>
      </div>

      {/* Connections Block */}
      <div className="space-y-2">
        <div className="text-[#00ff00] text-glow">[CONNECTIONS]</div>
        <div className="space-y-1 pl-4 text-sm">
          <div className="flex items-center gap-2">
            <Circle className={`h-2 w-2 ${isConnected ? 'fill-[#00ff00]' : 'fill-[#ff3333]'} text-[#00ff00]`} />
            <span className="text-[#00ff00] text-glow">LLM: {isConnected ? 'connected' : 'disconnected'}</span>
          </div>
          <div className="flex items-center gap-2">
            <Circle className="h-2 w-2 fill-[#00ff00] text-[#00ff00]" />
            <span className="text-[#00ff00] text-glow">MCP: 3/3 servers</span>
          </div>
          <div className="flex items-center gap-2">
            <Circle className="h-2 w-2 fill-transparent text-[#00ff00] opacity-40" />
            <span className="text-[#00ff00] opacity-60 text-glow">LSP: disabled</span>
          </div>
        </div>
      </div>

      {/* TODO Block */}
      <div className="space-y-2">
        <div className="text-[#00ff00] text-glow">[TODO]</div>
        <div className="space-y-1 pl-4 text-sm">
          {todoItems.length > 0 ? (
            todoItems.map((item, index) => (
              <div key={index} className="flex items-center gap-2">
                <span className="text-[#00ff00] text-glow">
                  {item.status === 'completed' ? '☑' : '☐'} {index + 1}. {item.description}
                </span>
                {item.status === 'in_progress' && (
                  <span className="text-[#00ff00] text-glow">←</span>
                )}
              </div>
            ))
          ) : (
            <div className="text-[#006600]">No tasks</div>
          )}
        </div>
      </div>
    </div>
  );
}
