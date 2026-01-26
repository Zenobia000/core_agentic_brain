import React, { useState } from 'react'
import { Search, Loader2, FileText, AlertCircle } from 'lucide-react'
import clsx from 'clsx'

function SearchPanel({ apiBase }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searchMode, setSearchMode] = useState('search') // 'search' | 'ask'

  const handleSearch = async () => {
    if (!query.trim()) return

    setIsLoading(true)
    setError(null)
    setResults([])

    try {
      const endpoint = searchMode === 'ask' ? '/ask' : '/search'
      const body = searchMode === 'ask' 
        ? { question: query, top_k: 5 }
        : { query, top_k: 10 }

      const res = await fetch(`${apiBase}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }

      const data = await res.json()
      
      if (searchMode === 'ask') {
        setResults([{
          type: 'answer',
          content: data.answer || data.content,
          sources: data.sources || data.results || []
        }])
      } else {
        setResults(data.results || data.documents || [])
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <div className="h-full flex flex-col p-4">
      {/* 搜尋列 */}
      <div className="space-y-4 mb-6">
        {/* 模式切換 */}
        <div className="flex gap-2">
          <button
            onClick={() => setSearchMode('search')}
            className={clsx(
              'px-4 py-2 rounded-lg font-medium transition-colors',
              searchMode === 'search'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            )}
          >
            語意搜尋
          </button>
          <button
            onClick={() => setSearchMode('ask')}
            className={clsx(
              'px-4 py-2 rounded-lg font-medium transition-colors',
              searchMode === 'ask'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            )}
          >
            問答模式
          </button>
        </div>

        {/* 搜尋框 */}
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={searchMode === 'ask' ? '輸入問題...' : '輸入搜尋關鍵字...'}
              className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={!query.trim() || isLoading}
            className={clsx(
              'px-6 py-3 rounded-xl font-medium transition-colors',
              query.trim() && !isLoading
                ? 'bg-primary-600 hover:bg-primary-700 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
            )}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              '搜尋'
            )}
          </button>
        </div>
      </div>

      {/* 錯誤訊息 */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {/* 搜尋結果 */}
      <div className="flex-1 overflow-y-auto">
        {results.length === 0 && !isLoading && (
          <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400">
            <div className="text-center">
              <Search className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p>{searchMode === 'ask' ? '輸入問題進行問答' : '輸入關鍵字進行搜尋'}</p>
            </div>
          </div>
        )}

        {results.length > 0 && (
          <div className="space-y-4">
            {results.map((result, idx) => (
              <ResultCard key={idx} result={result} mode={searchMode} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// 結果卡片組件
function ResultCard({ result, mode }) {
  if (result.type === 'answer') {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700">
        <h3 className="font-semibold text-lg mb-3 text-primary-600 dark:text-primary-400">
          回答
        </h3>
        <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
          {result.content}
        </p>
        
        {result.sources?.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <h4 className="text-sm font-medium text-gray-500 mb-2">
              參考來源 ({result.sources.length})
            </h4>
            <div className="space-y-2">
              {result.sources.map((src, idx) => (
                <div key={idx} className="text-sm p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
                  <span className="font-medium">{src.document_name || src.title || '來源 ' + (idx + 1)}</span>
                  {src.page && <span className="text-gray-500 ml-2">第 {src.page} 頁</span>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  // 搜尋結果
  const score = result.score ? (result.score * 100).toFixed(1) : null

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
          <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-1">
            <h3 className="font-medium truncate">
              {result.document_name || result.metadata?.source || '未知文件'}
            </h3>
            {score && (
              <span className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full">
                {score}% 相關
              </span>
            )}
          </div>
          
          {result.page && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
              第 {result.page} 頁
            </p>
          )}
          
          <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-3">
            {result.content || result.text || result.payload?.text || ''}
          </p>
        </div>
      </div>
    </div>
  )
}

export default SearchPanel
