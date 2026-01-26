import React, { useState, useRef } from 'react'
import { 
  FileText, 
  Upload, 
  Trash2, 
  RefreshCw, 
  Check, 
  Loader2,
  AlertCircle,
  CheckCircle,
  File,
  X
} from 'lucide-react'
import clsx from 'clsx'

function DocumentList({ documents, selectedDocs, onSelectDocs, onRefresh, apiBase }) {
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState({})
  const [deleting, setDeleting] = useState(null)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const fileInputRef = useRef(null)

  // 切換文件選擇
  const toggleDocument = (docName) => {
    if (selectedDocs.includes(docName)) {
      onSelectDocs(selectedDocs.filter(d => d !== docName))
    } else {
      onSelectDocs([...selectedDocs, docName])
    }
  }

  // 全選/取消全選
  const toggleSelectAll = () => {
    if (selectedDocs.length === documents.length) {
      onSelectDocs([])
    } else {
      onSelectDocs(documents.map(d => d.name || d.document_name))
    }
  }

  // 上傳檔案
  const handleUpload = async (e) => {
    const files = Array.from(e.target.files || [])
    if (files.length === 0) return

    setUploading(true)
    setError(null)
    setSuccess(null)

    const newProgress = {}
    files.forEach(f => newProgress[f.name] = { status: 'pending', progress: 0 })
    setUploadProgress(newProgress)

    let successCount = 0
    let failCount = 0

    for (const file of files) {
      try {
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: { status: 'uploading', progress: 30 }
        }))

        const formData = new FormData()
        formData.append('file', file)

        const res = await fetch(`${apiBase}/upload`, {
          method: 'POST',
          body: formData
        })

        if (res.ok) {
          setUploadProgress(prev => ({
            ...prev,
            [file.name]: { status: 'success', progress: 100 }
          }))
          successCount++
        } else {
          const data = await res.json().catch(() => ({}))
          throw new Error(data.detail || '上傳失敗')
        }
      } catch (err) {
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: { status: 'error', progress: 0, error: err.message }
        }))
        failCount++
      }
    }

    setUploading(false)

    if (successCount > 0) {
      setSuccess(`成功上傳 ${successCount} 個檔案`)
      onRefresh()
    }
    if (failCount > 0) {
      setError(`${failCount} 個檔案上傳失敗`)
    }

    // 清除進度
    setTimeout(() => {
      setUploadProgress({})
    }, 3000)

    // 重置 input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // 刪除文件
  const deleteDocument = async (docName) => {
    if (!confirm(`確定要刪除 "${docName}" 嗎？`)) return

    setDeleting(docName)
    setError(null)

    try {
      const res = await fetch(`${apiBase}/documents/${encodeURIComponent(docName)}`, {
        method: 'DELETE'
      })

      if (res.ok) {
        setSuccess(`已刪除 "${docName}"`)
        onSelectDocs(selectedDocs.filter(d => d !== docName))
        onRefresh()
      } else {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || '刪除失敗')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div className="h-full flex flex-col p-4">
      {/* 標題列 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold">
            文件庫 
            <span className="ml-2 text-sm font-normal text-gray-500">
              ({documents.length} 個文件)
            </span>
          </h2>
          
          {documents.length > 0 && (
            <button
              onClick={toggleSelectAll}
              className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
            >
              {selectedDocs.length === documents.length ? '取消全選' : '全選'}
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="重新整理"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
          
          <label className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg cursor-pointer transition-colors">
            <Upload className="w-4 h-4" />
            <span>上傳 PDF</span>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              multiple
              onChange={handleUpload}
              className="hidden"
              disabled={uploading}
            />
          </label>
        </div>
      </div>

      {/* 通知訊息 */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 rounded-lg flex items-center gap-2">
          <CheckCircle className="w-5 h-5 flex-shrink-0" />
          <span>{success}</span>
          <button onClick={() => setSuccess(null)} className="ml-auto">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* 上傳進度 */}
      {Object.keys(uploadProgress).length > 0 && (
        <div className="mb-4 space-y-2">
          {Object.entries(uploadProgress).map(([name, info]) => (
            <div 
              key={name}
              className={clsx(
                'p-3 rounded-lg flex items-center gap-3',
                info.status === 'success' && 'bg-green-50 dark:bg-green-900/20',
                info.status === 'error' && 'bg-red-50 dark:bg-red-900/20',
                info.status === 'uploading' && 'bg-blue-50 dark:bg-blue-900/20',
                info.status === 'pending' && 'bg-gray-50 dark:bg-gray-800'
              )}
            >
              {info.status === 'uploading' && <Loader2 className="w-4 h-4 animate-spin text-blue-500" />}
              {info.status === 'success' && <CheckCircle className="w-4 h-4 text-green-500" />}
              {info.status === 'error' && <AlertCircle className="w-4 h-4 text-red-500" />}
              {info.status === 'pending' && <File className="w-4 h-4 text-gray-400" />}
              
              <span className="text-sm flex-1 truncate">{name}</span>
              
              {info.error && (
                <span className="text-xs text-red-500">{info.error}</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 文件列表 */}
      <div className="flex-1 overflow-y-auto">
        {documents.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400">
            <div className="text-center">
              <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p>尚無文件</p>
              <p className="text-sm mt-1">上傳 PDF 文件開始使用</p>
            </div>
          </div>
        ) : (
          <div className="grid gap-3">
            {documents.map((doc, idx) => {
              const docName = doc.name || doc.document_name
              const isSelected = selectedDocs.includes(docName)
              const isDeleting = deleting === docName
              
              return (
                <div
                  key={idx}
                  className={clsx(
                    'p-4 rounded-lg border transition-all cursor-pointer',
                    isSelected 
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' 
                      : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600'
                  )}
                  onClick={() => toggleDocument(docName)}
                >
                  <div className="flex items-center gap-3">
                    {/* 選擇框 */}
                    <div className={clsx(
                      'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors',
                      isSelected 
                        ? 'bg-primary-600 border-primary-600 text-white' 
                        : 'border-gray-300 dark:border-gray-600'
                    )}>
                      {isSelected && <Check className="w-3 h-3" />}
                    </div>

                    {/* 圖示 */}
                    <div className="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                      <FileText className="w-5 h-5 text-red-600 dark:text-red-400" />
                    </div>

                    {/* 資訊 */}
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium truncate">{docName}</h3>
                      <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                        {doc.chunk_count && (
                          <span>{doc.chunk_count} 區塊</span>
                        )}
                        {doc.page_count && (
                          <span>{doc.page_count} 頁</span>
                        )}
                        {doc.uploaded_at && (
                          <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                        )}
                      </div>
                    </div>

                    {/* 刪除按鈕 */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteDocument(docName)
                      }}
                      disabled={isDeleting}
                      className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                      title="刪除"
                    >
                      {isDeleting ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default DocumentList
