import React, { useState, useRef, useEffect } from 'react'
import { Send, Loader2, User, Bot, AlertCircle, Copy, Check, FileText, ChevronRight, ChevronLeft, X } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import ProcessSteps from './ProcessSteps'
import SourceCard from './SourceCard'
import PDFViewer from './PDFViewer'
import clsx from 'clsx'

function ChatInterface({ documents = [], selectedDocs: initialSelectedDocs = [], onSelectDocs, apiBase }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [streamingContent, setStreamingContent] = useState('')
  
  // 新的步驟追蹤狀態
  const [processSteps, setProcessSteps] = useState([])
  const [currentSources, setCurrentSources] = useState([])
  
  // 文件選擇和預覽
  const [selectedDocs, setSelectedDocs] = useState(initialSelectedDocs)
  const [showPanel, setShowPanel] = useState(true)
  const [previewDoc, setPreviewDoc] = useState(null)
  const [panelWidth, setPanelWidth] = useState(320)
  const [isResizing, setIsResizing] = useState(false)
  
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const panelRef = useRef(null)

  // 同步外部選擇狀態
  useEffect(() => {
    if (onSelectDocs) {
      onSelectDocs(selectedDocs)
    }
    // 自動預覽第一個選中的文件
    if (selectedDocs.length > 0 && !previewDoc) {
      setPreviewDoc(selectedDocs[0])
    }
  }, [selectedDocs])

  // 拖曳調整寬度
  const handleMouseDown = (e) => {
    e.preventDefault()
    setIsResizing(true)
  }

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing) return
      const containerWidth = window.innerWidth
      const newWidth = containerWidth - e.clientX
      // 限制寬度範圍 200-600px
      setPanelWidth(Math.min(Math.max(newWidth, 200), 600))
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing])

  // 自動滾動到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent, processSteps])

  // 切換文件選擇
  const toggleDocSelection = (docName) => {
    setSelectedDocs(prev => {
      const isSelected = prev.includes(docName)
      if (isSelected) {
        // 取消選擇
        const newList = prev.filter(d => d !== docName)
        // 如果取消的是當前預覽的，切換到下一個
        if (previewDoc === docName) {
          setPreviewDoc(newList.length > 0 ? newList[0] : null)
        }
        return newList
      } else {
        // 新選擇 - 自動預覽
        setPreviewDoc(docName)
        return [...prev, docName]
      }
    })
  }

  // 添加步驟的輔助函數
  const addStep = (step) => {
    setProcessSteps(prev => {
      // 檢查是否需要更新現有步驟
      const existingIdx = prev.findIndex(s => s.id === step.id)
      if (existingIdx >= 0) {
        const updated = [...prev]
        updated[existingIdx] = { ...updated[existingIdx], ...step }
        return updated
      }
      return [...prev, step]
    })
  }

  // 更新最後一個步驟的狀態
  const updateLastStep = (updates) => {
    setProcessSteps(prev => {
      if (prev.length === 0) return prev
      const updated = [...prev]
      updated[updated.length - 1] = { ...updated[updated.length - 1], ...updates }
      return updated
    })
  }

  // 傳送訊息
  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setError(null)
    setIsLoading(true)
    setStreamingContent('')
    setProcessSteps([])
    setCurrentSources([])

    // 新增使用者訊息
    setMessages(prev => [...prev, { 
      role: 'user', 
      content: userMessage,
      selectedDocs: [...selectedDocs],
      timestamp: new Date()
    }])

    try {
      const response = await fetch(`${apiBase}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          session_id: 'web_session',
          selected_docs: selectedDocs.length > 0 ? selectedDocs : null
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let fullContent = ''
      let allSteps = []
      let sources = []
      let stepCounter = 0

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          
          try {
            const data = JSON.parse(line.slice(6))
            
            switch (data.type) {
              case 'thinking':
                // 分析/思考步驟 - 檢查是否是生成回答
                stepCounter++
                if (data.data?.type === 'generating') {
                  // 這是生成回答的步驟
                  addStep({
                    id: `step_${stepCounter}`,
                    type: 'generating',
                    title: '生成回答',
                    summary: data.content,
                    status: 'running',
                    autoExpand: true
                  })
                } else {
                  // 這是分析問題的步驟
                  addStep({
                    id: `step_${stepCounter}`,
                    type: 'analysis',
                    title: '分析問題',
                    summary: data.content,
                    status: 'completed',
                    autoExpand: true
                  })
                }
                break
              
              case 'plan':
              case 'planning':
                // 規劃步驟 - 後端發送 EventType.PLAN
                stepCounter++
                const planData = data.data || {}
                addStep({
                  id: `step_${stepCounter}`,
                  type: 'planning',
                  title: '規劃搜尋策略',
                  summary: planData.summary || data.content || '分解問題並規劃搜尋策略',
                  queries: planData.queries || [],
                  subSteps: planData.tasks?.map(t => ({ 
                    title: t.description || t.tool, 
                    status: 'pending' 
                  })),
                  status: 'completed',
                  autoExpand: true
                })
                break
              
              case 'tool_call':
                // 工具呼叫
                stepCounter++
                const toolName = data.content || data.tool || data.name || 'unknown'
                const toolParams = data.data?.arguments || data.params || {}
                addStep({
                  id: `step_${stepCounter}`,
                  type: 'tool_call',
                  title: getToolDisplayName(toolName),
                  summary: getToolSummary(toolName, toolParams),
                  queries: toolParams.queries || (toolParams.query ? [toolParams.query] : []),
                  status: 'running',
                  autoExpand: true
                })
                break
              
              case 'tool_result':
                // 工具結果
                updateLastStep({
                  status: 'completed',
                  results: data.data?.preview?.match(/results=(\d+)/)?.[1] || 
                           data.data?.results_count ||
                           '多個'
                })
                break
              
              case 'search_progress':
                // 搜尋進度（新事件類型）
                updateLastStep({
                  summary: data.content,
                  results: data.results_count
                })
                break
              
              case 'generating':
                // 生成回答中
                stepCounter++
                addStep({
                  id: `step_${stepCounter}`,
                  type: 'generating',
                  title: '生成回答',
                  summary: '根據搜尋結果生成回答...',
                  status: 'running'
                })
                break
              
              case 'token':
              case 'chunk':
                fullContent += data.content || data.text || ''
                setStreamingContent(fullContent)
                // 更新生成步驟
                updateLastStep({ status: 'running' })
                break
              
              case 'answer':
                fullContent = data.content || fullContent
                setStreamingContent(fullContent)
                updateLastStep({ status: 'completed' })
                break
              
              case 'source':
              case 'sources':
                const srcData = data.data?.sources || data.sources || []
                sources = srcData
                setCurrentSources(srcData)
                // 更新最後一個搜尋步驟的來源
                setProcessSteps(prev => {
                  const updated = [...prev]
                  for (let i = updated.length - 1; i >= 0; i--) {
                    if (updated[i].type === 'tool_call' || updated[i].type === 'search') {
                      updated[i] = { ...updated[i], sources: srcData }
                      break
                    }
                  }
                  return updated
                })
                break
              
              case 'error':
                addStep({
                  id: `error_${Date.now()}`,
                  type: 'error',
                  title: '發生錯誤',
                  summary: data.content || 'Unknown error',
                  status: 'error'
                })
                throw new Error(data.content || 'Unknown error')
              
              case 'done':
              case 'end':
                // 標記所有步驟為完成
                setProcessSteps(prev => prev.map(s => ({ ...s, status: 'completed' })))
                break
            }
          } catch (e) {
            if (e.message !== 'Unknown error') {
              console.warn('Parse error:', e)
            }
          }
        }
      }

      // 新增助手訊息
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: fullContent,
        steps: processSteps,
        sources,
        timestamp: new Date()
      }])

    } catch (err) {
      console.error('Chat error:', err)
      setError(err.message || '發生錯誤')
      
      // 嘗試使用同步 API
      try {
        const syncRes = await fetch(`${apiBase}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMessage,
            session_id: 'web_session',
            selected_docs: selectedDocs.length > 0 ? selectedDocs : null
          })
        })
        
        if (syncRes.ok) {
          const data = await syncRes.json()
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: data.answer,
            sources: data.sources,
            timestamp: new Date()
          }])
          setError(null)
        }
      } catch {
        // 保持原本的錯誤
      }
    } finally {
      setIsLoading(false)
      setStreamingContent('')
    }
  }

  // 工具名稱顯示轉換
  const getToolDisplayName = (tool) => {
    const names = {
      'rag_search': '搜尋知識庫',
      'rag_search_multiple': '多角度搜尋',
      'rag_ask': '知識問答',
      'web_search': '網路搜尋'
    }
    return names[tool] || tool
  }

  // 工具摘要生成
  const getToolSummary = (tool, params) => {
    if (tool === 'rag_search_multiple' && params.queries) {
      return `搜尋 ${params.queries.length} 個查詢: ${params.queries.slice(0, 2).join(', ')}...`
    }
    if (tool === 'rag_search' && params.query) {
      return `搜尋: ${params.query.slice(0, 50)}...`
    }
    return '執行中...'
  }

  // 處理按鍵
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="h-full flex relative">
      {/* 主對話區 */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* 訊息區 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
          {messages.length === 0 && !isLoading && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center text-gray-500 dark:text-gray-400">
                <Bot className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium mb-2">開始對話</h3>
                <p className="text-sm">
                  輸入問題與知識庫對話
                  {selectedDocs.length > 0 && (
                    <span className="block mt-1 text-primary-600 dark:text-primary-400">
                      已選擇 {selectedDocs.length} 個文件
                    </span>
                  )}
                </p>
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} onDocClick={setPreviewDoc} />
          ))}

          {/* 串流中的內容 */}
          {isLoading && (
            <div className="space-y-3">
              {/* 詳細步驟顯示 */}
              {processSteps.length > 0 && (
                <ProcessSteps steps={processSteps} isProcessing={true} />
              )}

              {/* 正在生成的回答 */}
              {streamingContent && (
                <div className="message-bubble message-assistant">
                  <div className="prose-chat">
                    <ReactMarkdown>{streamingContent}</ReactMarkdown>
                  </div>
                </div>
              )}

              {/* 初始載入狀態 */}
              {!streamingContent && processSteps.length === 0 && (
                <div className="message-bubble message-assistant">
                  <div className="flex items-center gap-2 text-gray-500">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>分析問題中...</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 錯誤提示 */}
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 輸入區 */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800">
          {/* 已選文件標籤 */}
          {selectedDocs.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {selectedDocs.map(doc => (
                <span 
                  key={doc}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-xs rounded-full"
                >
                  <FileText className="w-3 h-3" />
                  {doc}
                  <button 
                    onClick={() => toggleDocSelection(doc)}
                    className="hover:text-primary-900 dark:hover:text-primary-100"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
          
          <div className="flex gap-3">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="輸入問題... (Enter 傳送, Shift+Enter 換行)"
              className="flex-1 resize-none rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              rows={1}
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className={clsx(
                'px-4 py-3 rounded-xl font-medium transition-colors',
                input.trim() && !isLoading
                  ? 'bg-primary-600 hover:bg-primary-700 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
              )}
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* 右側面板切換按鈕 */}
      <button
        onClick={() => setShowPanel(!showPanel)}
        className={clsx(
          'absolute top-1/2 -translate-y-1/2 z-10 p-1 bg-gray-200 dark:bg-gray-700 rounded-l-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors',
        )}
        style={{ right: showPanel ? `${panelWidth}px` : '0' }}
      >
        {showPanel ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
      </button>

      {/* 右側文件面板 */}
      {showPanel && (
        <div 
          ref={panelRef}
          className="border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex flex-col relative"
          style={{ width: `${panelWidth}px`, minWidth: `${panelWidth}px` }}
        >
          {/* 拖曳調整寬度的 handle */}
          <div
            onMouseDown={handleMouseDown}
            className={clsx(
              'absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary-500 transition-colors z-20',
              isResizing && 'bg-primary-500'
            )}
          />
          {/* 文件選擇區 */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-medium text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              選擇文件
            </h3>
            {documents.length === 0 ? (
              <p className="text-sm text-gray-500">尚無文件，請先上傳</p>
            ) : (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {documents.map(doc => (
                  <label 
                    key={doc.name}
                    className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedDocs.includes(doc.name)}
                      onChange={() => toggleDocSelection(doc.name)}
                      className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                    />
                    <span className="text-sm truncate flex-1">{doc.name}</span>
                    <button
                      onClick={(e) => {
                        e.preventDefault()
                        setPreviewDoc(doc.name)
                      }}
                      className="p-1 text-gray-400 hover:text-primary-600"
                      title="預覽"
                    >
                      <FileText className="w-4 h-4" />
                    </button>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* PDF 預覽區 */}
          <div className="flex-1 overflow-hidden flex flex-col">
            <div className="p-2 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 className="font-medium text-gray-800 dark:text-gray-200 text-sm truncate">
                {previewDoc ? `📄 ${previewDoc}` : '文件預覽'}
              </h3>
              {previewDoc && (
                <button
                  onClick={() => setPreviewDoc(null)}
                  className="p-1 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            <div className="flex-1 overflow-hidden">
              {previewDoc ? (
                <PDFViewer filename={previewDoc} apiBase={apiBase} />
              ) : (
                <div className="h-full flex items-center justify-center text-gray-400">
                  <div className="text-center">
                    <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">點擊文件預覽內容</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// 訊息氣泡組件
function MessageBubble({ message, onDocClick }) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'

  const copyContent = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={clsx('flex gap-3', isUser && 'flex-row-reverse')}>
      {/* 頭像 */}
      <div className={clsx(
        'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
        isUser 
          ? 'bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400'
          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
      )}>
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* 內容 */}
      <div className={clsx('flex flex-col gap-2 max-w-[75%]', isUser && 'items-end')}>
        {/* 使用的文件 */}
        {isUser && message.selectedDocs?.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {message.selectedDocs.map(doc => (
              <span 
                key={doc}
                onClick={() => onDocClick?.(doc)}
                className="text-xs px-2 py-0.5 bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded cursor-pointer hover:bg-primary-200"
              >
                📄 {doc}
              </span>
            ))}
          </div>
        )}
        
        {/* 處理步驟 (使用新組件) */}
        {message.steps?.length > 0 && (
          <ProcessSteps steps={message.steps} isProcessing={false} />
        )}
        
        {/* 訊息內容 */}
        <div className={clsx('message-bubble', isUser ? 'message-user' : 'message-assistant')}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose-chat">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* 來源 */}
        {message.sources?.length > 0 && (
          <div className="space-y-2 w-full">
            <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">
              來源 ({message.sources.length})
            </p>
            <div className="grid gap-2">
              {message.sources.slice(0, 3).map((src, idx) => (
                <SourceCard key={idx} source={src} onClick={() => onDocClick?.(src.file_name || src.source)} />
              ))}
            </div>
          </div>
        )}

        {/* 操作按鈕 */}
        {!isUser && (
          <div className="flex items-center gap-2">
            <button
              onClick={copyContent}
              className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded transition-colors"
              title="複製"
            >
              {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
            </button>
            <span className="text-xs text-gray-400">
              {message.timestamp?.toLocaleTimeString()}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatInterface
