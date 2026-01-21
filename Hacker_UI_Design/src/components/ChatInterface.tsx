import { useEffect, useState, useRef } from 'react';
import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { ThinkingPanel } from './ThinkingPanel';
import { ToolsPanel } from './ToolsPanel';
import { StepEventPanel, StepEvent } from './StepEventPanel';
import { ChatMessage, ThinkingUpdate, ToolEvent } from '../services/api';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  streamBuffer: string;
  isStreaming: boolean;
  sendMessage: (message: string) => void;
  clearConversation: () => void;
  thinkingState: ThinkingUpdate | null;
  toolEvents: ToolEvent[];
  stepEvents?: StepEvent[];
  dualPanelMode?: boolean;
}

export function ChatInterface({
  messages,
  streamBuffer,
  isStreaming,
  sendMessage,
  clearConversation,
  thinkingState,
  toolEvents,
  stepEvents = [],
  dualPanelMode = false,
}: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [inputValue, setInputValue] = useState('');

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamBuffer]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isStreaming) {
      sendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const renderMessage = (msg: any, idx: number) => {
    const icons = {
      success: <CheckCircle className="h-4 w-4 text-[#00ff00]" />,
      warning: <AlertTriangle className="h-4 w-4 text-[#ffcc00]" />,
      error: <XCircle className="h-4 w-4 text-[#ff3333]" />,
    };

    const getMessageColor = () => {
      if (msg.role === 'user') return 'text-[#00ffff]';
      if (msg.role === 'system') return 'text-[#666666]';
      if (msg.role === 'feedback') {
        if (msg.content.startsWith('✓')) return 'text-[#00ff00]';
        if (msg.content.startsWith('⚠')) return 'text-[#ffcc00]';
        if (msg.content.startsWith('✗')) return 'text-[#ff3333]';
      }
      return 'text-[#00ff00]';
    };

    return (
      <div key={idx} className="flex items-start gap-2 mb-3">
        <span className={`${getMessageColor()} font-bold`}>
          {msg.role === 'assistant' ? 'MANUS' : msg.role}:
        </span>
        <div className="flex items-start gap-2 flex-1">
          {msg.role === 'feedback' && msg.content.startsWith('✓') && icons.success}
          {msg.role === 'feedback' && msg.content.startsWith('⚠') && icons.warning}
          {msg.role === 'feedback' && msg.content.startsWith('✗') && icons.error}
          <span className={getMessageColor()}>
            {msg.content}
          </span>
        </div>
      </div>
    );
  };

  // Filter messages for dual panel mode
  const finalAnswers = dualPanelMode
    ? messages.filter(msg => msg.role === 'assistant' || msg.role === 'user')
    : messages;

  return (
    <div className="flex flex-col h-full">
      {dualPanelMode ? (
        <div className="flex flex-1 overflow-hidden">
          {/* Left Panel: Final Answers */}
          <div className="flex flex-col w-[60%]">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 font-mono">
              <div className="space-y-2">
                {finalAnswers.map(renderMessage)}

                {/* Streaming Buffer */}
                {isStreaming && streamBuffer && (
                  <div className="flex items-start gap-2">
                    <span className="text-[#00ff00] font-bold">MANUS:</span>
                    <span className="text-[#00ff00]">
                      {streamBuffer}<span className="animate-pulse">█</span>
                    </span>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            </div>
          </div>

          {/* Right Panel: Thinking Chain */}
          <div className="w-[40%]">
            <StepEventPanel events={stepEvents} />
          </div>
        </div>
      ) : (
        <>
          {/* Original single panel layout */}
          <div className="flex-1 overflow-y-auto p-4 font-mono">
            <div className="space-y-2">
              {messages.map(renderMessage)}

              {/* Streaming Buffer */}
              {isStreaming && streamBuffer && (
                <div className="flex items-start gap-2">
                  <span className="text-[#00ff00] font-bold">MANUS:</span>
                  <span className="text-[#00ff00]">
                    {streamBuffer}<span className="animate-pulse">█</span>
                  </span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>

          <ThinkingPanel thinkingState={thinkingState} />
          <ToolsPanel toolEvents={toolEvents} />
        </>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-[#00ff00]">
        <div className="flex items-center gap-2">
          <span className="text-[#00ff00] text-glow">manus{'>'}</span>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={isStreaming ? "Waiting for response..." : ""}
            disabled={isStreaming}
            className="flex-1 bg-transparent text-[#00ff00] outline-none placeholder-[#006600] font-mono text-glow"
            autoFocus
          />
          <span className="text-xs text-[#006600]">
            {inputValue ? "Press Enter to send" : "Ctrl+P for commands"}
          </span>
        </div>
      </form>

      {/* Quick Actions */}
      <div className="flex gap-2 px-4 pb-2">
        <button
          onClick={clearConversation}
          className="text-xs text-[#006600] hover:text-[#00ff00] transition-colors"
        >
          [Clear]
        </button>
        <button
          onClick={() => sendMessage('/help')}
          className="text-xs text-[#006600] hover:text-[#00ff00] transition-colors"
        >
          [Help]
        </button>
        <button
          onClick={() => sendMessage('/status')}
          className="text-xs text-[#006600] hover:text-[#00ff00] transition-colors"
        >
          [Status]
        </button>
      </div>
    </div>
  );
}