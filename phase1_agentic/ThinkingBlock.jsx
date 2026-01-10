import { Brain, Search, Sparkles } from 'lucide-react';

/**
 * 推理過程區塊組件
 * 顯示 Agent 的思考過程
 */
function ThinkingBlock({ content, isActive = false }) {
  return (
    <div className={`
      flex items-start gap-3 px-4 py-3 rounded-lg border transition-all duration-300
      ${isActive 
        ? 'bg-purple-500/10 border-purple-500/30 animate-pulse' 
        : 'bg-slate-800/30 border-slate-700/30'
      }
    `}>
      <div className={`
        w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0
        ${isActive ? 'bg-purple-500/20' : 'bg-slate-700/50'}
      `}>
        <Brain className={`w-3.5 h-3.5 ${isActive ? 'text-purple-400' : 'text-slate-400'}`} />
      </div>
      <div className="flex-1 min-w-0">
        <p className={`text-sm ${isActive ? 'text-purple-300' : 'text-slate-400'}`}>
          {content}
        </p>
      </div>
      {isActive && (
        <Sparkles className="w-4 h-4 text-purple-400 animate-spin" />
      )}
    </div>
  );
}

export default ThinkingBlock;
