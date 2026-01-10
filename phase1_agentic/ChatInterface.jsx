import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Bot, User, FileText, TrendingUp, CheckCircle2, Zap } from 'lucide-react';
import ThinkingBlock from './ThinkingBlock';
import ToolCallBlock from './ToolCallBlock';

const API_BASE_URL = 'http://localhost:8001';

function ChatInterface({ messages, setMessages, onSourceClick, isProcessing, highlightKeyword }) {
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentThinking, setCurrentThinking] = useState(null);
  const [currentToolCalls, setCurrentToolCalls] = useState([]);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentThinking, currentToolCalls]);

  // 🆕 Agentic 串流對話
  const handleAgenticChat = async (userMessage) => {
    setIsStreaming(true);
    setCurrentThinking(null);
    setCurrentToolCalls([]);

    // 加入用戶訊息
    const userMsg = { type: 'user', content: userMessage };
    setMessages(prev => [...prev, userMsg]);

    // 加入 Agent 處理中的佔位
    const agentMsg = {
      type: 'agent',
      thinking: [],
      toolCalls: [],
      answer: '',
      sources: [],
      isStreaming: true
    };
    setMessages(prev => [...prev, agentMsg]);

    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let thinkingList = [];
      let toolCallList = [];
      let finalAnswer = '';
      let sources = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              switch (data.type) {
                case 'thinking':
                  thinkingList = [...thinkingList, data.content];
                  setCurrentThinking(data.content);
                  // 更新訊息
                  setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    if (lastMsg.type === 'agent') {
                      lastMsg.thinking = thinkingList;
                    }
                    return newMessages;
                  });
                  break;

                case 'tool_call':
                  const newToolCall = {
                    name: data.content,
                    arguments: data.data?.arguments || {},
                    status: 'running',
                    result: null
                  };
                  toolCallList = [...toolCallList, newToolCall];
                  setCurrentToolCalls(toolCallList);
                  // 更新訊息
                  setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    if (lastMsg.type === 'agent') {
                      lastMsg.toolCalls = toolCallList;
                    }
                    return newMessages;
                  });
                  break;

                case 'tool_result':
                  // 更新最後一個工具的結果
                  if (toolCallList.length > 0) {
                    toolCallList[toolCallList.length - 1].status = 'done';
                    toolCallList[toolCallList.length - 1].result = data.content;
                    setCurrentToolCalls([...toolCallList]);
                    setMessages(prev => {
                      const newMessages = [...prev];
                      const lastMsg = newMessages[newMessages.length - 1];
                      if (lastMsg.type === 'agent') {
                        lastMsg.toolCalls = [...toolCallList];
                      }
                      return newMessages;
                    });
                  }
                  setCurrentThinking(null);
                  break;

                case 'answer':
                  finalAnswer = data.content;
                  setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    if (lastMsg.type === 'agent') {
                      lastMsg.answer = finalAnswer;
                    }
                    return newMessages;
                  });
                  break;

                case 'source':
                  sources = data.data?.sources || [];
                  setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    if (lastMsg.type === 'agent') {
                      lastMsg.sources = sources;
                    }
                    return newMessages;
                  });
                  break;

                case 'done':
                  setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    if (lastMsg.type === 'agent') {
                      lastMsg.isStreaming = false;
                    }
                    return newMessages;
                  });
                  break;

                case 'error':
                  setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    if (lastMsg.type === 'agent') {
                      lastMsg.error = data.content;
                      lastMsg.isStreaming = false;
                    }
                    return newMessages;
                  });
                  break;
              }
            } catch (e) {
              console.error('Parse error:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMsg = newMessages[newMessages.length - 1];
        if (lastMsg.type === 'agent') {
          lastMsg.error = '連線錯誤，請稍後再試';
          lastMsg.isStreaming = false;
        }
        return newMessages;
      });
    } finally {
      setIsStreaming(false);
      setCurrentThinking(null);
      setCurrentToolCalls([]);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isStreaming) {
      handleAgenticChat(input.trim());
      setInput('');
      inputRef.current?.focus();
    }
  };

  // 渲染 Agent 訊息（含推理過程）
  const renderAgentMessage = (message, index) => {
    return (
      <div key={index} className="flex gap-3 mb-6">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1 space-y-3">
          {/* 推理過程 */}
          {message.thinking && message.thinking.length > 0 && (
            <div className="space-y-2">
              {message.thinking.map((thought, idx) => (
                <ThinkingBlock 
                  key={idx} 
                  content={thought} 
                  isActive={message.isStreaming && idx === message.thinking.length - 1}
                />
              ))}
            </div>
          )}

          {/* 工具呼叫 */}
          {message.toolCalls && message.toolCalls.length > 0 && (
            <div className="space-y-2">
              {message.toolCalls.map((tool, idx) => (
                <ToolCallBlock
                  key={idx}
                  toolName={tool.name}
                  arguments={tool.arguments}
                  result={tool.result}
                  status={tool.status}
                />
              ))}
            </div>
          )}

          {/* 錯誤訊息 */}
          {message.error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <p className="text-red-300">{message.error}</p>
            </div>
          )}

          {/* 最終回答 */}
          {message.answer && (
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
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
                  h1: ({ children }) => <h1 className="text-lg font-bold text-white mb-2">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-base font-bold text-white mb-2">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-sm font-bold text-white mb-2">{children}</h3>,
                }}
              >
                {message.answer}
              </ReactMarkdown>
            </div>
          )}

          {/* 載入中動畫 */}
          {message.isStreaming && !message.answer && !message.error && message.thinking.length === 0 && (
            <div className="space-y-2">
              <div className="h-4 bg-slate-700/50 rounded animate-pulse w-3/4" />
              <div className="h-4 bg-slate-700/50 rounded animate-pulse w-1/2" />
            </div>
          )}

          {/* 參考來源 */}
          {message.sources && message.sources.length > 0 && !message.isStreaming && (
            <div className="space-y-2 mt-4">
              <p className="text-xs text-slate-400 font-medium uppercase tracking-wide mb-2">
                參考來源
              </p>
              {message.sources.map((source, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    // 設定高亮關鍵字（使用最後一個搜尋查詢）
                    if (message.toolCalls && message.toolCalls.length > 0) {
                      const lastSearch = message.toolCalls[message.toolCalls.length - 1];
                      if (lastSearch.arguments?.query) {
                        highlightKeyword?.(lastSearch.arguments.query);
                      }
                    }
                    onSourceClick(source.page_label);
                  }}
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
  };

  const renderMessage = (message, index) => {
    // Agent 訊息（新格式）
    if (message.type === 'agent') {
      return renderAgentMessage(message, index);
    }

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

    // 舊版 assistant 訊息（相容性）
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
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-purple-400" />
          <h2 className="text-sm font-semibold text-white">Agentic 對話助手</h2>
        </div>
        <p className="text-xs text-slate-400 mt-0.5">智能推理 · 多步搜尋 · 來源引用</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400">
            <Zap className="w-16 h-16 mb-4 opacity-50" />
            <p className="text-lg font-medium">智能助手準備就緒</p>
            <p className="text-sm mt-2 text-center max-w-md">
              上傳 PDF 後，我會自動分析您的問題、搜尋相關資料，並展示完整的推理過程。
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
            placeholder={isProcessing ? "文件處理中，請稍候..." : isStreaming ? "AI 思考中..." : "輸入您的問題..."}
            disabled={isProcessing || isStreaming}
            className={`flex-1 bg-slate-900/50 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all ${(isProcessing || isStreaming) ? 'opacity-50 cursor-not-allowed' : ''}`}
          />
          <button
            type="submit"
            disabled={!input.trim() || isProcessing || isStreaming}
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
