import React, { useState } from 'react'
import { 
  Brain, 
  Search, 
  FileText, 
  CheckCircle2, 
  Loader2, 
  ChevronDown, 
  ChevronRight,
  Sparkles,
  ListTree,
  Database,
  MessageSquare,
  AlertCircle,
  BookOpen,
  Zap
} from 'lucide-react'
import clsx from 'clsx'

/**
 * 處理步驟組件 - 顯示 AI 的思考和執行過程
 * 
 * 類似 Manus/ChatGPT 的詳細步驟顯示
 */
function ProcessSteps({ steps = [], isProcessing = false }) {
  if (steps.length === 0 && !isProcessing) return null

  return (
    <div className="process-steps border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden bg-gray-50 dark:bg-gray-800/50 mb-4">
      {/* 標題 */}
      <div className="px-4 py-3 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-purple-100 dark:bg-purple-900/50 flex items-center justify-center">
            <Brain className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
          </div>
          <span className="font-medium text-sm text-gray-800 dark:text-gray-200">思考與執行過程</span>
          {isProcessing && (
            <div className="ml-auto flex items-center gap-2 text-xs text-blue-600 dark:text-blue-400">
              <Loader2 className="w-3 h-3 animate-spin" />
              <span>處理中...</span>
            </div>
          )}
        </div>
      </div>

      {/* 步驟列表 */}
      <div className="divide-y divide-gray-100 dark:divide-gray-700/50">
        {steps.map((step, index) => (
          <StepItem 
            key={step.id || index} 
            step={step} 
            stepNumber={index + 1}
            isLast={index === steps.length - 1}
            isProcessing={isProcessing && index === steps.length - 1}
          />
        ))}
      </div>
    </div>
  )
}

/**
 * 單一步驟項目
 */
function StepItem({ step, stepNumber, isLast, isProcessing }) {
  const [expanded, setExpanded] = useState(step.autoExpand !== false)
  
  const getStepIcon = () => {
    const iconClass = "w-4 h-4"
    switch (step.type) {
      case 'analysis':
        return <Brain className={clsx(iconClass, "text-purple-500")} />
      case 'planning':
        return <ListTree className={clsx(iconClass, "text-blue-500")} />
      case 'search':
      case 'tool_call':
        return <Search className={clsx(iconClass, "text-green-500")} />
      case 'generating':
        return <Sparkles className={clsx(iconClass, "text-pink-500")} />
      case 'result':
        return <FileText className={clsx(iconClass, "text-teal-500")} />
      case 'error':
        return <AlertCircle className={clsx(iconClass, "text-red-500")} />
      case 'done':
        return <CheckCircle2 className={clsx(iconClass, "text-green-500")} />
      default:
        return <Zap className={clsx(iconClass, "text-amber-500")} />
    }
  }

  const getStatusIndicator = () => {
    if (step.status === 'completed') {
      return (
        <div className="w-5 h-5 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
          <CheckCircle2 className="w-3 h-3 text-green-600 dark:text-green-400" />
        </div>
      )
    }
    if (step.status === 'running' || (isLast && isProcessing)) {
      return (
        <div className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
          <Loader2 className="w-3 h-3 animate-spin text-blue-600 dark:text-blue-400" />
        </div>
      )
    }
    if (step.status === 'error') {
      return (
        <div className="w-5 h-5 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
          <AlertCircle className="w-3 h-3 text-red-600 dark:text-red-400" />
        </div>
      )
    }
    return (
      <div className="w-5 h-5 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
        <span className="text-xs text-gray-500">{stepNumber}</span>
      </div>
    )
  }

  const hasDetails = step.details || step.queries?.length > 0 || step.results || step.subSteps?.length > 0 || step.sources?.length > 0

  return (
    <div className={clsx(
      "transition-colors",
      expanded && hasDetails && "bg-white dark:bg-gray-800/30"
    )}>
      {/* 步驟標題行 */}
      <button
        onClick={() => hasDetails && setExpanded(!expanded)}
        disabled={!hasDetails}
        className={clsx(
          "w-full px-4 py-3 flex items-start gap-3 text-left",
          hasDetails && "cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/30"
        )}
      >
        {/* 狀態指示器 */}
        <div className="flex-shrink-0 mt-0.5">
          {getStatusIndicator()}
        </div>

        {/* 內容 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            {getStepIcon()}
            <span className="font-medium text-sm text-gray-800 dark:text-gray-200">
              {step.title}
            </span>
            
            {/* 結果數量標籤 */}
            {step.results && (
              <span className="px-2 py-0.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full">
                {step.results} 個結果
              </span>
            )}
          </div>
          
          {/* 摘要 */}
          {step.summary && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
              {step.summary}
            </p>
          )}
        </div>

        {/* 展開箭頭 */}
        {hasDetails && (
          <div className="flex-shrink-0 text-gray-400 mt-0.5">
            {expanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </div>
        )}
      </button>

      {/* 展開的詳細內容 */}
      {expanded && hasDetails && (
        <div className="px-4 pb-4 ml-8 space-y-3">
          {/* 查詢列表 - 類似 ChatGPT 的搜尋顯示 */}
          {step.queries && step.queries.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs font-medium text-gray-500 dark:text-gray-400">
                <Search className="w-3 h-3" />
                <span>搜尋查詢</span>
              </div>
              <div className="space-y-1.5 pl-1">
                {step.queries.map((query, i) => (
                  <div 
                    key={i}
                    className="flex items-start gap-2 text-xs"
                  >
                    <span className="text-gray-400 mt-0.5">→</span>
                    <span className="px-2 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded border border-blue-100 dark:border-blue-800">
                      {query}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 子步驟 - 類似 Manus 的任務分解 */}
          {step.subSteps && step.subSteps.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs font-medium text-gray-500 dark:text-gray-400">
                <ListTree className="w-3 h-3" />
                <span>任務分解</span>
              </div>
              <div className="space-y-1 border-l-2 border-gray-200 dark:border-gray-600 pl-3 ml-1">
                {step.subSteps.map((subStep, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs py-1">
                    {subStep.status === 'completed' ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                    ) : subStep.status === 'running' ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-500 flex-shrink-0" />
                    ) : (
                      <div className="w-3.5 h-3.5 rounded-full border-2 border-gray-300 dark:border-gray-500 flex-shrink-0" />
                    )}
                    <span className={clsx(
                      "text-gray-600 dark:text-gray-400",
                      subStep.status === 'completed' && "text-gray-800 dark:text-gray-200"
                    )}>
                      {subStep.title}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 詳細文字 */}
          {step.details && (
            <div className="text-xs text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-900/50 rounded-lg p-3 whitespace-pre-wrap font-mono">
              {step.details}
            </div>
          )}

          {/* 來源文件 - 類似 ChatGPT 的來源顯示 */}
          {step.sources && step.sources.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs font-medium text-gray-500 dark:text-gray-400">
                <BookOpen className="w-3 h-3" />
                <span>參考來源</span>
              </div>
              <div className="grid gap-2">
                {step.sources.slice(0, 5).map((src, i) => (
                  <div 
                    key={i}
                    className="flex items-center gap-2 text-xs bg-gray-100 dark:bg-gray-700/50 rounded-lg px-3 py-2"
                  >
                    <FileText className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                    <span className="text-gray-700 dark:text-gray-300 truncate flex-1">
                      {src.file_name}
                    </span>
                    <span className="text-gray-400 text-[10px]">
                      第 {src.page_label} 頁
                    </span>
                  </div>
                ))}
                {step.sources.length > 5 && (
                  <span className="text-xs text-gray-400 pl-2">
                    +{step.sources.length - 5} 個更多來源
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ProcessSteps
