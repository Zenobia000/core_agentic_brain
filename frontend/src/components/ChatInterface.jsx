import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Bot, User, FileText, TrendingUp, CheckCircle2 } from 'lucide-react';

function ChatInterface({ messages, onSendMessage, onSourceClick, isProcessing }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      onSendMessage(input.trim());
      setInput('');
      inputRef.current?.focus();
    }
  };

  const renderMessage = (message, index) => {
    if (message.type === 'system') {
      return (
        <div key={index} className="flex justify-center py-3">
          <div className="px-4 py-2 bg-green-500/10 border border-green-500/30 rounded-lg flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-400" />
            <span className="text-sm text-green-300">{message.content}</span>
          </div>
        </div>
      );
    }

    if (message.type === 'loading') {
      return (
        <div key={index} className="flex gap-3 mb-6">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1 space-y-2 mt-1">
            <div className="h-4 bg-slate-700/50 rounded animate-pulse w-3/4" />
            <div className="h-4 bg-slate-700/50 rounded animate-pulse w-1/2" />
            <div className="h-4 bg-slate-700/50 rounded animate-pulse w-2/3" />
          </div>
        </div>
      );
    }

    if (message.type === 'error') {
      return (
        <div key={index} className="flex gap-3 mb-6">
          <div className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center flex-shrink-0">
            <Bot className="w-5 h-5 text-red-400" />
          </div>
          <div className="flex-1 bg-red-500/10 border border-red-500/30 rounded-lg p-4">
            <p className="text-red-300">{message.content}</p>
          </div>
        </div>
      );
    }

    if (message.type === 'user') {
      return (
        <div key={index} className="flex gap-3 mb-6 justify-end">
          <div className="flex-1 bg-blue-600/20 border border-blue-500/30 rounded-lg p-4 max-w-[80%]">
            <p className="text-slate-100">{message.content}</p>
          </div>
          <div className="w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center flex-shrink-0">
            <User className="w-5 h-5 text-slate-300" />
          </div>
        </div>
      );
    }

    if (message.type === 'assistant') {
      return (
        <div key={index} className="flex gap-3 mb-6">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 mb-3">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                className="prose prose-invert prose-sm max-w-none"
                components={{
                  p: ({ children }) => <p className="text-slate-100 mb-3 last:mb-0">{children}</p>,
                  ul: ({ children }) => <ul className="text-slate-100 list-disc list-inside space-y-1 mb-3">{children}</ul>,
                  ol: ({ children }) => <ol className="text-slate-100 list-decimal list-inside space-y-1 mb-3">{children}</ol>,
                  li: ({ children }) => <li className="text-slate-100">{children}</li>,
                  strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
                  code: ({ children }) => <code className="bg-slate-900/50 px-1.5 py-0.5 rounded text-blue-300">{children}</code>,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>

            {/* Sources */}
            {message.sources && message.sources.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs text-slate-400 font-medium uppercase tracking-wide mb-2">
                  參考來源
                </p>
                {message.sources.map((source, idx) => (
                  <button
                    key={idx}
                    onClick={() => onSourceClick(source.page_label)}
                    className="w-full text-left bg-slate-900/30 hover:bg-slate-900/50 border border-slate-700/50 hover:border-blue-500/50 rounded-lg p-3 transition-all group"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center flex-shrink-0 group-hover:bg-blue-500/20 transition-colors">
                        <FileText className="w-4 h-4 text-blue-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="text-sm font-medium text-slate-200 truncate">
                            {source.file_name}
                          </p>
                          <span className="text-xs text-slate-500">
                            頁 {source.page_label}
                          </span>
                        </div>
                        {source.summary && (
                          <p className="text-xs text-slate-400 line-clamp-2">
                            {source.summary}
                          </p>
                        )}
                        <div className="flex items-center gap-2 mt-2">
                          <div className="flex items-center gap-1">
                            <TrendingUp className="w-3 h-3 text-green-400" />
                            <span className="text-xs text-green-400 font-medium">
                              {(source.score * 100).toFixed(0)}% 相關
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="h-full flex flex-col">
      {/* Chat Header */}
      <div className="bg-slate-900/50 px-4 py-3 border-b border-slate-700/50">
        <h2 className="text-sm font-semibold text-white">對話助手</h2>
        <p className="text-xs text-slate-400 mt-0.5">向我提問任何關於文件的問題</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400">
            <Bot className="w-16 h-16 mb-4 opacity-50" />
            <p className="text-lg font-medium">準備好回答您的問題</p>
            <p className="text-sm mt-2 text-center max-w-md">
              上傳 PDF 後，您可以詢問任何關於文件內容的問題，我會根據文件內容為您解答。
            </p>
          </div>
        ) : (
          <>
            {messages.map(renderMessage)}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-slate-700/50">
        <div className="flex gap-2">
          <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={isProcessing ? "文件處理中，請稍候..." : "輸入您的問題..."}
                disabled={isProcessing}
                className={`flex-1 bg-slate-900/50 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
            />
          <button
            type="submit"
            disabled={!input.trim() || isProcessing}
            className="px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed rounded-lg transition-all flex items-center justify-center group"
          >
            <Send className="w-5 h-5 text-white group-disabled:text-slate-500" />
          </button>
        </div>
      </form>
    </div>
  );
}

export default ChatInterface;
