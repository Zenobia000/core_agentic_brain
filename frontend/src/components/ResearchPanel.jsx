import { useState, useEffect, useRef } from 'react';

export default function ResearchPanel({ documents = [], apiBase = '/api' }) {
  const [topic, setTopic] = useState('');
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [activeTask, setActiveTask] = useState(null);
  const [taskHistory, setTaskHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const pollInterval = useRef(null);

  // 載入歷史任務
  useEffect(() => {
    loadTaskHistory();
    return () => {
      if (pollInterval.current) {
        clearInterval(pollInterval.current);
      }
    };
  }, []);

  const loadTaskHistory = async () => {
    try {
      const res = await fetch(`${apiBase}/research`);
      const data = await res.json();
      setTaskHistory(data.tasks || []);
    } catch (err) {
      console.error('Load task history failed:', err);
    }
  };

  const startResearch = async () => {
    if (!topic.trim()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const res = await fetch(`${apiBase}/research/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: topic.trim(),
          documents: selectedDocs.length > 0 ? selectedDocs : null
        })
      });
      
      const data = await res.json();
      const taskId = data.task_id;
      setActiveTask(taskId);
      
      // 立即加入任務到歷史（避免洗版）
      const newTask = {
        task_id: taskId,
        topic: topic.trim(),
        status: 'running',
        progress: 0,
        steps: [],
        created_at: new Date().toISOString()
      };
      setTaskHistory(prev => [newTask, ...prev.filter(t => t.task_id !== taskId)]);
      
      // 開始輪詢狀態
      pollInterval.current = setInterval(() => pollTaskStatus(taskId), 2000);
      
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  const pollTaskStatus = async (taskId) => {
    try {
      const res = await fetch(`${apiBase}/research/${taskId}`);
      const data = await res.json();
      
      // 只更新已存在的任務，不新增
      setTaskHistory(prev => {
        return prev.map(t => 
          t.task_id === taskId 
            ? { ...t, ...data }
            : t
        );
      });
      
      // 如果完成或失敗，停止輪詢
      if (data.status === 'completed' || data.status === 'failed') {
        if (pollInterval.current) {
          clearInterval(pollInterval.current);
          pollInterval.current = null;
        }
        setIsLoading(false);
        setActiveTask(null);
        setTopic('');
      }
      
    } catch (err) {
      console.error('Poll task status failed:', err);
    }
  };

  const toggleDocSelection = (docName) => {
    setSelectedDocs(prev => 
      prev.includes(docName)
        ? prev.filter(d => d !== docName)
        : [...prev, docName]
    );
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return '✅';
      case 'failed': return '❌';
      case 'running': return '🔄';
      default: return '⏳';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'running': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* 標題 */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-indigo-50">
        <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
          <span className="text-2xl">🔬</span>
          深度研究
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          自動分析主題、多輪搜尋、生成研究報告
        </p>
      </div>

      {/* 輸入區 */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="space-y-4">
          {/* 主題輸入 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              研究主題
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="例如：比較 Transformer 和 RNN 的優缺點"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              disabled={isLoading}
            />
          </div>

          {/* 文件篩選 */}
          {documents.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                限定研究文件（可選）
              </label>
              <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                {documents.map(doc => (
                  <button
                    key={doc.name}
                    onClick={() => toggleDocSelection(doc.name)}
                    className={`px-3 py-1 text-sm rounded-full transition-colors ${
                      selectedDocs.includes(doc.name)
                        ? 'bg-purple-500 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {doc.name}
                  </button>
                ))}
              </div>
              {selectedDocs.length > 0 && (
                <p className="text-xs text-gray-500 mt-1">
                  已選擇 {selectedDocs.length} 個文件
                </p>
              )}
            </div>
          )}

          {/* 啟動按鈕 */}
          <button
            onClick={startResearch}
            disabled={!topic.trim() || isLoading}
            className="w-full py-3 bg-gradient-to-r from-purple-500 to-indigo-500 text-white font-medium rounded-lg hover:from-purple-600 hover:to-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <span className="animate-spin">🔄</span>
                研究進行中...
              </>
            ) : (
              <>
                <span>🚀</span>
                開始深度研究
              </>
            )}
          </button>

          {error && (
            <div className="text-red-600 text-sm bg-red-50 p-2 rounded">
              ❌ {error}
            </div>
          )}
        </div>
      </div>

      {/* 研究任務列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {taskHistory.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <div className="text-4xl mb-2">📊</div>
            <p>尚無研究任務</p>
            <p className="text-sm">輸入主題開始深度研究</p>
          </div>
        ) : (
          taskHistory.map(task => (
            <TaskCard 
              key={task.task_id} 
              task={task}
              isActive={activeTask === task.task_id}
            />
          ))
        )}
      </div>
    </div>
  );
}

// 任務卡片元件
function TaskCard({ task, isActive }) {
  const [expanded, setExpanded] = useState(isActive);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return '✅';
      case 'failed': return '❌';
      case 'running': return '🔄';
      default: return '⏳';
    }
  };

  return (
    <div className={`bg-white rounded-lg border ${isActive ? 'border-purple-300 shadow-lg' : 'border-gray-200'} overflow-hidden`}>
      {/* 標題列 */}
      <div 
        className="p-4 cursor-pointer hover:bg-gray-50 flex items-center justify-between"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={isActive ? 'animate-spin' : ''}>{getStatusIcon(task.status)}</span>
            <h3 className="font-medium text-gray-800 truncate">{task.topic}</h3>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {task.created_at}
          </p>
        </div>
        
        {/* 進度條 */}
        {task.status === 'running' && (
          <div className="w-24 ml-4">
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 transition-all duration-300"
                style={{ width: `${task.progress}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 text-center mt-1">{task.progress}%</p>
          </div>
        )}
        
        <span className="ml-2 text-gray-400">{expanded ? '▼' : '▶'}</span>
      </div>

      {/* 展開內容 */}
      {expanded && (
        <div className="border-t border-gray-100">
          {/* 步驟列表 */}
          {task.steps && task.steps.length > 0 && (
            <div className="p-4 bg-gray-50">
              <h4 className="text-sm font-medium text-gray-700 mb-2">研究步驟</h4>
              <div className="space-y-2">
                {task.steps.map((step, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <span className={
                      step.status === 'done' ? 'text-green-500' :
                      step.status === 'running' ? 'text-blue-500 animate-pulse' :
                      step.status === 'error' ? 'text-red-500' :
                      'text-gray-400'
                    }>
                      {step.status === 'done' ? '✓' :
                       step.status === 'running' ? '●' :
                       step.status === 'error' ? '✗' : '○'}
                    </span>
                    <span className="text-gray-700">{step.step}</span>
                    {step.result && (
                      <span className="text-gray-500 text-xs">({step.result})</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 研究報告 */}
          {task.report && (
            <div className="p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">📄 研究報告</h4>
              <div className="prose prose-sm max-w-none bg-white rounded-lg p-4 border border-gray-200 max-h-96 overflow-y-auto">
                <div className="whitespace-pre-wrap text-gray-700">
                  {task.report}
                </div>
              </div>
            </div>
          )}

          {/* 來源 */}
          {task.sources_count > 0 && (
            <div className="px-4 pb-4">
              <p className="text-xs text-gray-500">
                📚 參考來源: {task.sources_count} 個文件片段
              </p>
            </div>
          )}

          {/* 錯誤訊息 */}
          {task.error && (
            <div className="p-4 bg-red-50 text-red-700 text-sm">
              ❌ 錯誤: {task.error}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
