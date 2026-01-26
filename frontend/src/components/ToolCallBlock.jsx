import React, { useState } from 'react'
import { Wrench, ChevronDown, ChevronUp, Check, Loader2, AlertCircle } from 'lucide-react'
import clsx from 'clsx'

function ToolCallBlock({ toolCall }) {
  const [expanded, setExpanded] = useState(false)
  
  const { name, input, result, status = 'complete' } = toolCall

  const statusIcon = {
    running: <Loader2 className="w-4 h-4 animate-spin text-blue-500" />,
    complete: <Check className="w-4 h-4 text-green-500" />,
    error: <AlertCircle className="w-4 h-4 text-red-500" />
  }

  return (
    <div className="tool-call-block">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-2">
          <Wrench className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <span className="font-medium text-sm text-blue-700 dark:text-blue-300">
            {name || 'Tool Call'}
          </span>
          {statusIcon[status]}
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-blue-600" />
        ) : (
          <ChevronDown className="w-4 h-4 text-blue-600" />
        )}
      </button>

      {expanded && (
        <div className="mt-3 space-y-2 text-sm">
          {/* 輸入參數 */}
          {input && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-1">輸入:</p>
              <pre className="bg-gray-900 text-gray-100 p-2 rounded text-xs overflow-x-auto">
                {typeof input === 'string' ? input : JSON.stringify(input, null, 2)}
              </pre>
            </div>
          )}
          
          {/* 執行結果 */}
          {result && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-1">結果:</p>
              <pre className="bg-gray-900 text-gray-100 p-2 rounded text-xs overflow-x-auto max-h-40">
                {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ToolCallBlock
