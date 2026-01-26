import React from 'react'
import { FileText, ExternalLink } from 'lucide-react'

function SourceCard({ source }) {
  const { 
    document_name, 
    title, 
    content, 
    text,
    score, 
    page,
    metadata 
  } = source

  const displayTitle = title || document_name || metadata?.source || '未知來源'
  const displayContent = content || text || ''
  const displayScore = score ? (score * 100).toFixed(1) : null

  return (
    <div className="source-card">
      <div className="flex items-start gap-2">
        <FileText className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h4 className="font-medium text-sm truncate text-gray-900 dark:text-gray-100">
              {displayTitle}
            </h4>
            {displayScore && (
              <span className="text-xs px-1.5 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded">
                {displayScore}%
              </span>
            )}
          </div>
          
          {page && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              第 {page} 頁
            </p>
          )}
          
          {displayContent && (
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-1 line-clamp-2">
              {displayContent}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

export default SourceCard
