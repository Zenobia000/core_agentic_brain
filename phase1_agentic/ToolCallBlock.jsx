import { Search, Database, CheckCircle2, Loader2, FileSearch } from 'lucide-react';

/**
 * 工具呼叫區塊組件
 * 顯示 RAG 工具的呼叫過程和結果
 */
function ToolCallBlock({ toolName, arguments: args, result, status = 'running' }) {
  // 根據工具名稱顯示不同圖示和標題
  const getToolInfo = () => {
    switch (toolName) {
      case 'rag_search':
        return {
          icon: Search,
          title: '知識庫搜尋',
          description: args?.query || '搜尋中...'
        };
      case 'rag_search_multiple':
        return {
          icon: FileSearch,
          title: '多重搜尋',
          description: args?.queries?.join(', ') || '搜尋中...'
        };
      default:
        return {
          icon: Database,
          title: toolName,
          description: JSON.stringify(args)
        };
    }
  };

  const { icon: Icon, title, description } = getToolInfo();

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 bg-slate-900/30 border-b border-slate-700/30">
        <div className={`
          w-8 h-8 rounded-lg flex items-center justify-center
          ${status === 'running' ? 'bg-blue-500/20' : 'bg-green-500/20'}
        `}>
          <Icon className={`w-4 h-4 ${status === 'running' ? 'text-blue-400' : 'text-green-400'}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium text-slate-200">{title}</p>
            {status === 'running' ? (
              <Loader2 className="w-3 h-3 text-blue-400 animate-spin" />
            ) : (
              <CheckCircle2 className="w-3 h-3 text-green-400" />
            )}
          </div>
          <p className="text-xs text-slate-400 truncate">{description}</p>
        </div>
      </div>

      {/* Result */}
      {result && (
        <div className="px-4 py-3">
          <p className="text-xs text-slate-400 mb-1">結果</p>
          <p className="text-sm text-slate-300">{result}</p>
        </div>
      )}
    </div>
  );
}

export default ToolCallBlock;
