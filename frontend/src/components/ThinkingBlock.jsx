import React, { useState } from 'react'
import { Brain, ChevronDown, ChevronUp } from 'lucide-react'
import clsx from 'clsx'

function ThinkingBlock({ content, defaultExpanded = false }) {
  const [expanded, setExpanded] = useState(defaultExpanded)

  if (!content) return null

  // 截取前幾個字作為預覽
  const preview = content.length > 100 
    ? content.slice(0, 100) + '...' 
    : content

  return (
    <div className="thinking-block">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400">
          <Brain className="w-4 h-4" />
          <span className="font-medium text-sm">思考過程</span>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-amber-600" />
        ) : (
          <ChevronDown className="w-4 h-4 text-amber-600" />
        )}
      </button>
      
      <div className={clsx(
        'mt-2 text-sm text-amber-800 dark:text-amber-300 overflow-hidden transition-all duration-300',
        expanded ? 'max-h-96 opacity-100' : 'max-h-12 opacity-70'
      )}>
        <p className="whitespace-pre-wrap">
          {expanded ? content : preview}
        </p>
      </div>
    </div>
  )
}

export default ThinkingBlock
