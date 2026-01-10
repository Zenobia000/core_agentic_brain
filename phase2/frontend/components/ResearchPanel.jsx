import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

/**
 * Deep Research 研究報告生成組件
 * 支援主題研究、進度追蹤、報告下載
 */
export default function ResearchPanel({ selectedDocs }) {
  const [topic, setTopic] = useState('');
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState(null);
  const [polling, setPolling] = useState(false);
  const [history, setHistory] = useState([]);
  const pollIntervalRef = useRef(null);

  // 輪詢研究任務狀態
  useEffect(() => {
    if (polling && taskId) {
      pollIntervalRef.current = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:8001/research/${taskId}`);
          const data = await res.json();
          setStatus(data);
          
          if (data.status === 'completed' || data.status === 'failed') {
            setPolling(false);
            clearInterval(pollIntervalRef.current);
            
            // 添加到歷史
            if (data.status === 'completed' && data.report) {
              setHistory(prev => [{
                taskId,
                title: data.report.title,
                createdAt: data.report.generated_at,
                report: data.report
              }, ...prev]);
            }
          }
        } catch (err) {
          console.error('Failed to poll status:', err);
        }
      }, 1500);
    }
    
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [polling, taskId]);

  // 開始研究
  const startResearch = async () => {
    if (!topic.trim()) return;
    
    try {
      const res = await fetch('http://localhost:8001/research/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: topic.trim(),
          documents: selectedDocs.length > 0 ? selectedDocs : null
        })
      });
      
      if (!res.ok) throw new Error('Failed to start research');
      
      const data = await res.json();
      setTaskId(data.task_id);
      setPolling(true);
      setStatus({ status: 'running', progress: 0, steps: [] });
    } catch (err) {
      console.error('Failed to start research:', err);
      alert('啟動研究失敗，請確認後端服務正常運行');
    }
  };

  // 下載報告
  const downloadReport = (report, format = 'md') => {
    if (!report) return;
    
    let content, mimeType, extension;
    
    if (format === 'md') {
      content = `# ${report.title}\n\n${report.content}\n\n---\n\n## 引用來源\n\n${
        report.sources?.map(s => `- ${s.source} (p.${s.page})`).join('\n') || '無'
      }\n\n_報告生成時間：${new Date(report.generated_at).toLocaleString()}_`;
      mimeType = 'text/markdown';
      extension = 'md';
    } else if (format === 'html') {
      content = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${report.title}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; line-height: 1.6; }
    h1, h2, h3 { color: #1a1a1a; }
    .sources { background: #f5f5f5; padding: 1rem; border-radius: 8px; margin-top: 2rem; }
    .meta { color: #666; font-size: 0.875rem; margin-top: 2rem; }
  </style>
</head>
<body>
  <h1>${report.title}</h1>
  ${report.content.replace(/\n/g, '<br>')}
  <div class="sources">
    <h3>引用來源</h3>
    <ul>${report.sources?.map(s => `<li>${s.source} (p.${s.page})</li>`).join('') || '<li>無</li>'}</ul>
  </div>
  <p class="meta">報告生成時間：${new Date(report.generated_at).toLocaleString()}</p>
</body>
</html>`;
      mimeType = 'text/html';
      extension = 'html';
    }
    
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research_${topic.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')}.${extension}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // 重新開始
  const resetResearch = () => {
    setTaskId(null);
    setStatus(null);
    setPolling(false);
    setTopic('');
  };

  // 載入歷史報告
  const loadHistoryReport = (item) => {
    setStatus({
      status: 'completed',
      progress: 100,
      report: item.report,
      steps: []
    });
    setTopic(item.title.replace('研究報告：', ''));
  };

  return (
    <div className="h-full flex gap-6">
      {/* 左側：歷史記錄 */}
      <div className="w-64 flex-shrink-0">
        <div className="bg-white rounded-lg shadow p-4 h-full">
          <h3 className="font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <span>📋</span>
            <span>研究歷史</span>
          </h3>
          
          {history.length === 0 ? (
            <div className="text-center text-gray-400 py-8">
              <div className="text-3xl mb-2">📝</div>
              <p className="text-sm">尚無研究記錄</p>
            </div>
          ) : (
            <div className="space-y-2">
              {history.map((item) => (
                <div
                  key={item.taskId}
                  onClick={() => loadHistoryReport(item)}
                  className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-blue-50 transition-colors"
                >
                  <p className="text-sm font-medium text-gray-800 truncate">
                    {item.title}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(item.createdAt).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 右側：主面板 */}
      <div className="flex-1 bg-white rounded-lg shadow p-6 flex flex-col">
        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
          <span>🔬</span>
          <span>Deep Research</span>
        </h2>
        
        {/* 輸入區 */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            研究主題
          </label>
          <div className="flex gap-3">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !polling && startResearch()}
              placeholder="例如：Transformer 架構的核心創新是什麼？"
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={polling}
            />
            <button
              onClick={startResearch}
              disabled={polling || !topic.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {polling ? (
                <span className="flex items-center gap-2">
                  <span className="animate-spin">⏳</span>
                  研究中
                </span>
              ) : (
                '開始研究'
              )}
            </button>
            {status?.status === 'completed' && (
              <button
                onClick={resetResearch}
                className="px-4 py-3 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors"
              >
                新研究
              </button>
            )}
          </div>
          
          {/* 文件篩選提示 */}
          {selectedDocs.length > 0 && (
            <p className="text-xs text-gray-500 mt-2 flex items-center gap-1">
              <span>📂</span>
              <span>將在 {selectedDocs.length} 個選中的文件中進行研究</span>
            </p>
          )}
        </div>

        {/* 進度顯示 */}
        {status && status.status !== 'completed' && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span className="font-medium">研究進度</span>
              <span>{Math.round(status.progress)}%</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500 ease-out"
                style={{ width: `${status.progress}%` }}
              />
            </div>
            
            {/* 步驟列表 */}
            <div className="space-y-2">
              {status.steps?.map((step, i) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  <span className="flex-shrink-0 mt-0.5">
                    {step.status === 'running' ? (
                      <span className="inline-block animate-spin">⏳</span>
                    ) : step.status === 'done' ? (
                      '✅'
                    ) : (
                      '❌'
                    )}
                  </span>
                  <div>
                    <span className={step.status === 'running' ? 'text-blue-600 font-medium' : 'text-gray-600'}>
                      {step.step}
                    </span>
                    {step.result && (
                      <span className="text-gray-400 ml-2">- {step.result}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 錯誤顯示 */}
        {status?.status === 'failed' && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600 font-medium">❌ 研究失敗</p>
            <p className="text-red-500 text-sm mt-1">{status.error}</p>
            <button
              onClick={resetResearch}
              className="mt-3 px-4 py-2 bg-red-100 text-red-600 rounded hover:bg-red-200 text-sm"
            >
              重新開始
            </button>
          </div>
        )}

        {/* 報告顯示 */}
        {status?.report && (
          <div className="flex-1 flex flex-col min-h-0">
            {/* 報告頭部 */}
            <div className="flex justify-between items-center mb-4 pb-4 border-b">
              <div>
                <h3 className="text-lg font-semibold text-gray-800">
                  📄 {status.report.title}
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                  生成於 {new Date(status.report.generated_at).toLocaleString()}
                  {' • '}
                  {status.report.findings_count} 個發現
                  {' • '}
                  {status.report.sources?.length || 0} 個來源
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => downloadReport(status.report, 'md')}
                  className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 text-sm font-medium transition-colors"
                >
                  📥 Markdown
                </button>
                <button
                  onClick={() => downloadReport(status.report, 'html')}
                  className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 text-sm font-medium transition-colors"
                >
                  📥 HTML
                </button>
              </div>
            </div>
            
            {/* 報告內容 */}
            <div className="flex-1 overflow-y-auto">
              <div className="prose prose-sm max-w-none bg-gray-50 p-6 rounded-lg">
                <ReactMarkdown
                  components={{
                    h1: ({ children }) => <h1 className="text-2xl font-bold text-gray-900 mb-4">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-xl font-semibold text-gray-800 mt-6 mb-3">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-lg font-medium text-gray-700 mt-4 mb-2">{children}</h3>,
                    p: ({ children }) => <p className="text-gray-600 mb-3 leading-relaxed">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1">{children}</ol>,
                    li: ({ children }) => <li className="text-gray-600">{children}</li>,
                    strong: ({ children }) => <strong className="font-semibold text-gray-800">{children}</strong>,
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-4 border-blue-400 pl-4 italic text-gray-600 my-4">
                        {children}
                      </blockquote>
                    ),
                  }}
                >
                  {status.report.content}
                </ReactMarkdown>
              </div>
              
              {/* 來源列表 */}
              <div className="mt-6 p-4 bg-gray-100 rounded-lg">
                <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <span>📚</span>
                  <span>引用來源 ({status.report.sources?.length || 0})</span>
                </h4>
                <div className="flex flex-wrap gap-2">
                  {status.report.sources?.map((source, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center px-3 py-1 bg-white rounded-full text-xs text-gray-600 border"
                    >
                      📄 {source.source}
                      <span className="ml-1 text-gray-400">p.{source.page}</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 空狀態 */}
        {!status && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center text-gray-400">
              <div className="text-6xl mb-4">🔬</div>
              <p className="text-lg">輸入主題開始深度研究</p>
              <p className="text-sm mt-2">AI 將自動分析知識庫並生成報告</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
