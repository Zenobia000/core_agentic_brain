import React, { useState, useEffect, useRef } from 'react';
import { Search, Play, Download, FileText, CheckCircle, Clock, AlertCircle, Sparkles } from 'lucide-react';

/**
 * Deep Research 研究報告組件 - Manus 風格
 */
export default function ResearchPanel({ selectedDocs, darkMode = true }) {
  const [topic, setTopic] = useState('');
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState(null);
  const [polling, setPolling] = useState(false);
  const pollIntervalRef = useRef(null);

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
          }
        } catch (err) {
          console.error('Poll error:', err);
        }
      }, 1500);
    }
    return () => clearInterval(pollIntervalRef.current);
  }, [polling, taskId]);

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
      
      const data = await res.json();
      setTaskId(data.task_id);
      setPolling(true);
      setStatus({ status: 'running', progress: 0, steps: [] });
    } catch (err) {
      alert('啟動失敗');
    }
  };

  const downloadReport = (format = 'md') => {
    if (!status?.report) return;
    
    const content = format === 'md'
      ? `# ${status.report.title}\n\n${status.report.content}`
      : status.report.content;
    
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research_${Date.now()}.${format}`;
    a.click();
  };

  const resetResearch = () => {
    setTaskId(null);
    setStatus(null);
    setPolling(false);
    setTopic('');
  };

  return (
    <div className="h-full flex flex-col p-6">
      {/* 標題 */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-xl flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">Deep Research</h2>
            <p className="text-sm text-white/40">AI 自動分析知識庫並生成研究報告</p>
          </div>
        </div>
      </div>

      {/* 輸入區 */}
      <div className="mb-6">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !polling && startResearch()}
              placeholder="輸入研究主題，例如：Transformer 的核心創新"
              className="w-full pl-11 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20 transition-all"
              disabled={polling}
            />
          </div>
          <button
            onClick={polling ? null : (status?.report ? resetResearch : startResearch)}
            disabled={polling || (!status?.report && !topic.trim())}
            className={`
              px-6 py-3 rounded-xl font-medium flex items-center gap-2 transition-all
              ${polling
                ? 'bg-white/5 text-white/30 cursor-not-allowed'
                : status?.report
                  ? 'bg-white/10 text-white hover:bg-white/20'
                  : 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white hover:from-violet-500 hover:to-fuchsia-500 shadow-lg shadow-violet-500/25'
              }
            `}
          >
            {polling ? (
              <>
                <Clock className="w-4 h-4 animate-spin" />
                <span>研究中</span>
              </>
            ) : status?.report ? (
              <span>新研究</span>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>開始</span>
              </>
            )}
          </button>
        </div>
        
        {selectedDocs.length > 0 && (
          <p className="mt-2 text-xs text-white/30">
            將在 {selectedDocs.length} 個選中的文件中進行研究
          </p>
        )}
      </div>

      {/* 進度區 */}
      {status && status.status !== 'completed' && (
        <div className="mb-6 p-4 bg-white/5 rounded-xl border border-white/10">
          {/* 進度條 */}
          <div className="flex items-center justify-between text-sm mb-3">
            <span className="text-white/50">研究進度</span>
            <span className="text-white font-medium">{Math.round(status.progress)}%</span>
          </div>
          <div className="h-1.5 bg-white/10 rounded-full overflow-hidden mb-4">
            <div 
              className="h-full bg-gradient-to-r from-violet-500 to-fuchsia-500 transition-all duration-500"
              style={{ width: `${status.progress}%` }}
            />
          </div>

          {/* 步驟列表 */}
          <div className="space-y-2">
            {status.steps?.map((step, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                {step.status === 'running' ? (
                  <Clock className="w-4 h-4 text-amber-400 animate-spin" />
                ) : step.status === 'done' ? (
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-400" />
                )}
                <span className={step.status === 'running' ? 'text-white' : 'text-white/50'}>
                  {step.step}
                </span>
                {step.result && (
                  <span className="text-white/30 text-xs">({step.result})</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 報告顯示 */}
      {status?.report && (
        <div className="flex-1 flex flex-col min-h-0">
          {/* 報告頭部 */}
          <div className="flex items-center justify-between mb-4 pb-4 border-b border-white/10">
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-violet-400" />
              <div>
                <h3 className="text-white font-medium">{status.report.title}</h3>
                <p className="text-xs text-white/30">
                  {new Date(status.report.generated_at).toLocaleString()} • {status.report.sources?.length || 0} 個來源
                </p>
              </div>
            </div>
            <button
              onClick={() => downloadReport('md')}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg hover:bg-emerald-500/30 transition-colors"
            >
              <Download className="w-4 h-4" />
              <span className="text-sm">下載</span>
            </button>
          </div>

          {/* 報告內容 */}
          <div className="flex-1 overflow-y-auto">
            <div className="prose prose-invert prose-sm max-w-none">
              <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                {status.report.content.split('\n').map((line, i) => {
                  if (line.startsWith('# ')) {
                    return <h1 key={i} className="text-2xl font-bold text-white mb-4">{line.slice(2)}</h1>;
                  } else if (line.startsWith('## ')) {
                    return <h2 key={i} className="text-lg font-semibold text-white mt-6 mb-3">{line.slice(3)}</h2>;
                  } else if (line.startsWith('### ')) {
                    return <h3 key={i} className="text-base font-medium text-white/90 mt-4 mb-2">{line.slice(4)}</h3>;
                  } else if (line.startsWith('- ')) {
                    return <li key={i} className="text-white/70 ml-4">{line.slice(2)}</li>;
                  } else if (line.trim()) {
                    return <p key={i} className="text-white/60 mb-3 leading-relaxed">{line}</p>;
                  }
                  return null;
                })}
              </div>
            </div>

            {/* 來源 */}
            {status.report.sources?.length > 0 && (
              <div className="mt-6 p-4 bg-white/5 rounded-xl border border-white/10">
                <h4 className="text-sm font-medium text-white/50 mb-3">引用來源</h4>
                <div className="flex flex-wrap gap-2">
                  {status.report.sources.map((s, i) => (
                    <span key={i} className="px-3 py-1 bg-white/5 rounded-full text-xs text-white/50">
                      {s.source} (p.{s.page})
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 空狀態 */}
      {!status && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-20 h-20 bg-white/5 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-10 h-10 text-white/20" />
            </div>
            <p className="text-white/30">輸入主題開始深度研究</p>
          </div>
        </div>
      )}
    </div>
  );
}
