import React, { useState, useEffect } from 'react'
import { Loader2, FileText, AlertCircle, ExternalLink, Download } from 'lucide-react'

function PDFViewer({ filename, apiBase }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // 預覽 URL (inline)
  const pdfUrl = `${apiBase}/documents/${encodeURIComponent(filename)}/pdf`
  // 下載 URL
  const downloadUrl = `${apiBase}/documents/${encodeURIComponent(filename)}/pdf?download=true`

  const handleLoad = () => {
    setLoading(false)
    setError(null)
  }

  const handleError = () => {
    setError('無法載入 PDF 文件')
    setLoading(false)
  }

  // 重置狀態當文件改變
  useEffect(() => {
    setLoading(true)
    setError(null)
  }, [filename])

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4 text-center">
        <AlertCircle className="w-12 h-12 text-red-400 mb-3" />
        <p className="text-red-500 font-medium">{error}</p>
        <p className="text-gray-500 text-sm mt-2">
          請確認 PDF 文件已正確上傳
        </p>
        <a 
          href={pdfUrl} 
          target="_blank" 
          rel="noopener noreferrer"
          className="mt-3 text-primary-600 hover:underline flex items-center gap-1"
        >
          <ExternalLink className="w-4 h-4" />
          在新視窗開啟
        </a>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* 工具列 */}
      <div className="flex items-center justify-between p-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <span className="text-xs text-gray-600 dark:text-gray-400 truncate">
          {filename}
        </span>
        <div className="flex items-center gap-1">
          <a 
            href={pdfUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
            title="在新視窗開啟"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
          <a 
            href={downloadUrl}
            download={filename}
            className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
            title="下載 PDF"
          >
            <Download className="w-4 h-4" />
          </a>
        </div>
      </div>

      {/* PDF 顯示區 */}
      <div className="flex-1 relative bg-gray-100 dark:bg-gray-900">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white dark:bg-gray-800">
            <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
          </div>
        )}
        
        <iframe
          src={pdfUrl}
          className="w-full h-full border-0"
          onLoad={handleLoad}
          onError={handleError}
          title={`PDF: ${filename}`}
        />
      </div>
    </div>
  )
}

export default PDFViewer
