import React, { useState, useRef, useEffect } from 'react';

/**
 * 對話面板組件
 * 支援文件篩選搜尋、來源點擊、關鍵字提取
 */
export default function ChatPanel({ selectedDocs, onSourceClick }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // 自動滾動到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 提取搜尋關鍵字
  const extractKeywords = (query) => {
    // 移除常用詞，保留有意義的詞
    const stopWords = ['的', '是', '在', '有', '和', '與', '了', '也', '就', '都', '而', '及', 
                       'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                       'what', 'how', 'why', 'when', 'where', 'which', 'who'];
    
    const words = query
      .toLowerCase()
      .split(/[\s,，。？！?!]+/)
      .filter(word => word.length > 1 && !stopWords.includes(word));
    
    return [...new Set(words)].slice(0, 5);
  };

  // 發送訊息
  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    const keywords = extractKeywords(userMessage);
    
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      // 使用篩選搜尋 API
      const searchRes = await fetch('http://localhost:8001/search/filtered', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userMessage,
          filenames: selectedDocs.length > 0 ? selectedDocs : null,
          top_k: 5
        })
      });

      if (!searchRes.ok) throw new Error('Search failed');
      const searchData = await searchRes.json();

      // 生成回答
      const askRes = await fetch('http://localhost:8001/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userMessage,
          context: searchData.results.map(r => r.content).join('\n\n')
        })
      });

      if (!askRes.ok) throw new Error('Ask failed');
      const askData = await askRes.json();

      // 添加回答和來源
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: askData.answer,
        sources: searchData.results,
        keywords: keywords
      }]);

    } catch (err) {
      console.error('Error:', err);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ 抱歉，發生錯誤。請確認後端服務正常運行。',
        error: true
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  // 點擊來源
  const handleSourceClick = (source, keywords = []) => {
    if (onSourceClick) {
      onSourceClick(source.source, source.page, keywords);
    }
  };

  // 清除對話
  const clearMessages = () => {
    if (window.confirm('確定要清除所有對話嗎？')) {
      setMessages([]);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* 頂部工具列 */}
      <div className="px-4 py-3 border-b flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-gray-700">💬 對話</h3>
          {selectedDocs.length > 0 && (
            <p className="text-xs text-gray-400">
              搜尋範圍：{selectedDocs.length} 個文件
            </p>
          )}
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            className="text-xs text-gray-400 hover:text-red-500"
          >
            清除對話
          </button>
        )}
      </div>

      {/* 訊息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="h-full flex items-center justify-center text-gray-400">
            <div className="text-center">
              <div className="text-5xl mb-4">💭</div>
              <p>開始提問探索知識庫</p>
              <p className="text-sm mt-2">
                {selectedDocs.length > 0 
                  ? `將在 ${selectedDocs.length} 個選中的文件中搜尋`
                  : '將在所有文件中搜尋'
                }
              </p>
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-2xl rounded-br-sm'
                  : msg.error
                    ? 'bg-red-50 text-red-600 rounded-2xl rounded-bl-sm'
                    : 'bg-gray-100 text-gray-800 rounded-2xl rounded-bl-sm'
              } px-4 py-3`}
            >
              {/* 訊息內容 */}
              <div className="whitespace-pre-wrap">{msg.content}</div>

              {/* 來源卡片 */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-xs text-gray-500 mb-2">📚 來源</p>
                  <div className="space-y-2">
                    {msg.sources.map((source, sIdx) => (
                      <div
                        key={sIdx}
                        onClick={() => handleSourceClick(source, msg.keywords)}
                        className="flex items-start gap-2 p-2 bg-white rounded-lg border cursor-pointer hover:border-blue-300 hover:shadow-sm transition-all group"
                      >
                        <span className="text-lg">📄</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-medium text-gray-700 truncate">
                              {source.source}
                            </span>
                            <span className="text-xs text-blue-500 opacity-0 group-hover:opacity-100">
                              點擊查看 →
                            </span>
                          </div>
                          <div className="flex items-center gap-2 text-xs text-gray-400 mt-1">
                            <span>頁碼: {source.page}</span>
                            <span>•</span>
                            <span>相關度: {Math.round(source.score * 100)}%</span>
                          </div>
                          <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                            {source.content.substring(0, 100)}...
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading 指示器 */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="animate-bounce">⏳</div>
                <span className="text-gray-500">思考中...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 輸入區 */}
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder={
              selectedDocs.length > 0
                ? `在 ${selectedDocs.length} 個文件中搜尋...`
                : '輸入問題...'
            }
            className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? '⏳' : '發送'}
          </button>
        </div>
      </div>
    </div>
  );
}
