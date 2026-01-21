import { useState } from 'react';
import { ChevronRight, ChevronDown, CheckCircle, XCircle, Zap, AlertTriangle, Brain, Wrench, Eye, File, Link } from 'lucide-react';

export interface StepEvent {
  run_id: string;
  step_index: number;
  timestamp: string;
  phase: 'think' | 'act' | 'observe' | 'final' | 'error' | 'artifact';
  role: 'system' | 'agent' | 'tool' | 'user';
  message?: string;
  thinking?: string;
  tool?: {
    name: string;
    input: any;
    output?: any;
    duration_ms?: number;
    status: 'running' | 'success' | 'failed' | 'timeout';
    error?: string;
  };
  artifacts?: Array<{
    type: 'file' | 'url' | 'image' | 'text' | 'code' | 'markdown';
    path?: string;
    url?: string;
    preview?: string;
    size?: number;
    mime_type?: string;
  }>;
  error?: string;
  error_type?: string;
  metadata?: Record<string, any>;
}

interface StepEventPanelProps {
  events: StepEvent[];
  isExpanded?: boolean;
}

const PhaseIcon = ({ phase }: { phase: string }) => {
  switch (phase) {
    case 'think':
      return <Brain className="h-4 w-4 text-[#00ffff]" />;
    case 'act':
      return <Wrench className="h-4 w-4 text-[#ffcc00]" />;
    case 'observe':
      return <Eye className="h-4 w-4 text-[#00ff00]" />;
    case 'error':
      return <XCircle className="h-4 w-4 text-[#ff3333]" />;
    case 'artifact':
      return <File className="h-4 w-4 text-[#ff00ff]" />;
    default:
      return <Zap className="h-4 w-4 text-[#ffffff]" />;
  }
};

const PhaseColor = (phase: string): string => {
  switch (phase) {
    case 'think':
      return 'text-[#00ffff]';
    case 'act':
      return 'text-[#ffcc00]';
    case 'observe':
      return 'text-[#00ff00]';
    case 'error':
      return 'text-[#ff3333]';
    case 'artifact':
      return 'text-[#ff00ff]';
    case 'final':
      return 'text-[#00ff00]';
    default:
      return 'text-[#ffffff]';
  }
};

const StatusIcon = ({ status }: { status: string }) => {
  switch (status) {
    case 'running':
      return <Zap className="h-3 w-3 animate-pulse text-[#00ffff]" />;
    case 'success':
      return <CheckCircle className="h-3 w-3 text-[#00ff00]" />;
    case 'failed':
      return <XCircle className="h-3 w-3 text-[#ff3333]" />;
    case 'timeout':
      return <AlertTriangle className="h-3 w-3 text-[#ffcc00]" />;
    default:
      return null;
  }
};

const StepEventCard = ({ event }: { event: StepEvent }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Skip final events in the thinking chain
  if (event.phase === 'final') return null;

  return (
    <div className="border border-[#00ff00] border-opacity-30 rounded-lg p-3 mb-3 hover:border-opacity-60 transition-all">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <PhaseIcon phase={event.phase} />
          <span className={`font-bold ${PhaseColor(event.phase)}`}>
            Step {event.step_index}: {event.phase.toUpperCase()}
          </span>
          {event.tool && (
            <>
              <span className="text-[#666666]">•</span>
              <span className="text-[#ffcc00]">{event.tool.name}</span>
              <StatusIcon status={event.tool.status} />
            </>
          )}
        </div>
        <span className="text-[#666666] text-xs">
          {new Date(event.timestamp).toLocaleTimeString()}
        </span>
      </div>

      {/* Message */}
      {event.message && (
        <div className="mb-2 text-[#00ff00] text-sm">
          {event.message}
        </div>
      )}

      {/* Thinking (collapsed by default) */}
      {event.thinking && (
        <div className="mb-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 text-[#00ffff] text-xs hover:text-[#00ff00] transition-colors"
          >
            {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
            View thinking process
          </button>
          {isExpanded && (
            <div className="mt-2 p-2 bg-[#001100] rounded text-[#00ff00] text-sm font-mono">
              {event.thinking}
            </div>
          )}
        </div>
      )}

      {/* Tool Details */}
      {event.tool && (
        <div className="mt-2 pl-4 border-l-2 border-[#00ff00] border-opacity-30">
          {/* Tool Input */}
          {event.tool.input && Object.keys(event.tool.input).length > 0 && (
            <details className="mb-2">
              <summary className="text-[#666666] text-xs cursor-pointer hover:text-[#00ff00]">
                Input parameters
              </summary>
              <pre className="mt-1 text-xs text-[#00ffff] overflow-x-auto">
                {JSON.stringify(event.tool.input, null, 2)}
              </pre>
            </details>
          )}

          {/* Tool Output */}
          {event.tool.output && (
            <details className="mb-2">
              <summary className="text-[#666666] text-xs cursor-pointer hover:text-[#00ff00]">
                Output ({event.tool.duration_ms ? `${event.tool.duration_ms}ms` : 'N/A'})
              </summary>
              <pre className="mt-1 text-xs text-[#00ff00] overflow-x-auto max-h-40">
                {typeof event.tool.output === 'string'
                  ? event.tool.output
                  : JSON.stringify(event.tool.output, null, 2)}
              </pre>
            </details>
          )}

          {/* Tool Error */}
          {event.tool.error && (
            <div className="text-[#ff3333] text-xs">
              Error: {event.tool.error}
            </div>
          )}
        </div>
      )}

      {/* Artifacts */}
      {event.artifacts && event.artifacts.length > 0 && (
        <div className="mt-2">
          <div className="text-[#ff00ff] text-xs mb-1">Artifacts:</div>
          {event.artifacts.map((artifact, idx) => (
            <div key={idx} className="flex items-center gap-2 ml-4 mb-1">
              {artifact.type === 'file' && <File className="h-3 w-3 text-[#ff00ff]" />}
              {artifact.type === 'url' && <Link className="h-3 w-3 text-[#00ffff]" />}
              <span className="text-[#00ff00] text-xs">
                {artifact.path || artifact.url || 'Artifact'}
              </span>
              {artifact.preview && (
                <details className="inline">
                  <summary className="text-[#666666] text-xs cursor-pointer hover:text-[#00ff00]">
                    Preview
                  </summary>
                  <pre className="mt-1 text-xs text-[#00ff00] overflow-x-auto max-h-40 block">
                    {artifact.preview}
                  </pre>
                </details>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {event.error && !event.tool && (
        <div className="mt-2 p-2 bg-[#330000] rounded">
          <div className="text-[#ff3333] text-sm">
            {event.error_type && <span className="font-bold">{event.error_type}: </span>}
            {event.error}
          </div>
        </div>
      )}
    </div>
  );
};

export function StepEventPanel({ events, isExpanded = true }: StepEventPanelProps) {
  const [isPanelExpanded, setIsPanelExpanded] = useState(isExpanded);

  // Filter out final events for the thinking chain
  const thinkingEvents = events.filter(e => e.phase !== 'final');

  return (
    <div className="h-full flex flex-col border-l border-[#00ff00]">
      {/* Header */}
      <div
        className="flex items-center justify-between p-4 border-b border-[#00ff00] cursor-pointer hover:bg-[#00ff00] hover:bg-opacity-5 transition-colors"
        onClick={() => setIsPanelExpanded(!isPanelExpanded)}
      >
        <div className="flex items-center gap-2">
          {isPanelExpanded ? (
            <ChevronDown className="h-4 w-4 text-[#00ff00]" />
          ) : (
            <ChevronRight className="h-4 w-4 text-[#00ff00]" />
          )}
          <span className="text-[#00ff00] font-bold text-glow">THINKING CHAIN</span>
        </div>
        <span className="text-[#00ff00] opacity-60 text-sm">
          {thinkingEvents.length} steps
        </span>
      </div>

      {/* Events Timeline */}
      {isPanelExpanded && (
        <div className="flex-1 overflow-y-auto p-4">
          {thinkingEvents.length === 0 ? (
            <div className="text-[#666666] text-center mt-8">
              No thinking events yet...
            </div>
          ) : (
            <div className="space-y-2">
              {thinkingEvents.map((event, idx) => (
                <StepEventCard key={`${event.run_id}-${event.step_index}`} event={event} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}