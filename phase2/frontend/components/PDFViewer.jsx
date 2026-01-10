import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// 設置 PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

/**
 * PDF 預覽組件
 * 支援頁面跳轉和關鍵字高亮
 */
export default function PDFViewer({ 
  pdfUrl, 
  currentPage = 1, 
  highlightKeywords = [],
  onPageChange 
}) {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(currentPage);
  const [scale, setScale] = useState(1.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const containerRef = useRef(null);
  const pageRef = useRef(null);

  // 當外部頁碼改變時更新
  useEffect(() => {
    if (currentPage && currentPage !== pageNumber) {
      setPageNumber(currentPage);
    }
  }, [currentPage]);

  // 文檔載入成功
  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    setLoading(false);
    setError(null);
  };

  // 文檔載入失敗
  const onDocumentLoadError = (err) => {
    console.error('PDF load error:', err);
    setError('無法載入 PDF 文件');
    setLoading(false);
  };

  // 頁面切換
  const goToPage = (page) => {
    const newPage = Math.max(1, Math.min(numPages, page));
    setPageNumber(newPage);
    if (onPageChange) onPageChange(newPage);
  };

  // 縮放控制
  const zoomIn = () => setScale(s => Math.min(2.0, s + 0.1));
  const zoomOut = () => setScale(s => Math.max(0.5, s - 0.1));
  const resetZoom = () => setScale(1.0);

  // 自定義文字渲染器 - 處理高亮
  const customTextRenderer = useCallback((textItem) => {
    if (!highlightKeywords || highlightKeywords.length === 0) {
      return textItem.str;
    }

    let text = textItem.str;
    
    // 為每個關鍵字創建高亮
    highlightKeywords.forEach((keyword) => {
      if (!keyword || keyword.length < 2) return;
      
      try {
        // 轉義特殊正則字符
        const escapedKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${escapedKeyword})`, 'gi');
        text = text.replace(regex, '<mark class="pdf-highlight">$1</mark>');
      } catch (e) {
        console.warn('Invalid regex for keyword:', keyword);
      }
    });
    
    return text;
  }, [highlightKeywords]);

  // 高亮後滾動到第一個高亮處
  useEffect(() => {
    if (highlightKeywords.length > 0 && !loading) {
      setTimeout(() => {
        const highlight = document.querySelector('.pdf-highlight');
        if (highlight) {
          highlight.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 500);
    }
  }, [pageNumber, highlightKeywords, loading]);

  // 鍵盤導航
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        goToPage(pageNumber - 1);
      } else if (e.key === 'ArrowRight' || e.key === 'PageDown') {
        goToPage(pageNumber + 1);
      } else if (e.key === 'Home') {
        goToPage(1);
      } else if (e.key === 'End') {
        goToPage(numPages);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [pageNumber, numPages]);

  if (!pdfUrl) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-100">
        <div className="text-center text-gray-400">
          <div className="text-6xl mb-4">📄</div>
          <p className="text-lg">選擇來源後顯示 PDF</p>
          <p className="text-sm mt-2">點擊對話中的來源卡片</p>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="h-full flex flex-col bg-gray-200">
      {/* 工具列 */}
      <div className="flex items-center justify-between px-4 py-2 bg-white border-b shadow-sm">
        {/* 頁面導航 */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => goToPage(1)}
            disabled={pageNumber <= 1}
            className="p-1 text-gray-600 hover:text-gray-900 disabled:opacity-30"
            title="第一頁"
          >
            ⏮️
          </button>
          <button
            onClick={() => goToPage(pageNumber - 1)}
            disabled={pageNumber <= 1}
            className="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-30 transition-colors"
          >
            ◀
          </button>
          
          <div className="flex items-center gap-1">
            <input
              type="number"
              min={1}
              max={numPages || 1}
              value={pageNumber}
              onChange={(e) => goToPage(parseInt(e.target.value) || 1)}
              className="w-12 px-2 py-1 text-center border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-gray-500">/ {numPages || '?'}</span>
          </div>
          
          <button
            onClick={() => goToPage(pageNumber + 1)}
            disabled={pageNumber >= numPages}
            className="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-30 transition-colors"
          >
            ▶
          </button>
          <button
            onClick={() => goToPage(numPages)}
            disabled={pageNumber >= numPages}
            className="p-1 text-gray-600 hover:text-gray-900 disabled:opacity-30"
            title="最後一頁"
          >
            ⏭️
          </button>
        </div>

        {/* 縮放控制 */}
        <div className="flex items-center gap-2">
          <button
            onClick={zoomOut}
            className="px-2 py-1 bg-gray-100 rounded hover:bg-gray-200"
            title="縮小"
          >
            ➖
          </button>
          <button
            onClick={resetZoom}
            className="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 text-sm"
          >
            {Math.round(scale * 100)}%
          </button>
          <button
            onClick={zoomIn}
            className="px-2 py-1 bg-gray-100 rounded hover:bg-gray-200"
            title="放大"
          >
            ➕
          </button>
        </div>

        {/* 高亮關鍵字提示 */}
        {highlightKeywords.length > 0 && (
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>🔍</span>
            <span className="max-w-[200px] truncate">
              {highlightKeywords.slice(0, 3).join(', ')}
              {highlightKeywords.length > 3 && ` +${highlightKeywords.length - 3}`}
            </span>
          </div>
        )}
      </div>

      {/* PDF 內容區 */}
      <div className="flex-1 overflow-auto p-4">
        {loading && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin text-4xl mb-2">⏳</div>
              <p className="text-gray-500">載入中...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-red-500">
              <div className="text-4xl mb-2">❌</div>
              <p>{error}</p>
            </div>
          </div>
        )}

        <Document
          file={pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={onDocumentLoadError}
          loading={null}
          className="flex justify-center"
        >
          <Page
            pageNumber={pageNumber}
            scale={scale}
            renderTextLayer={true}
            renderAnnotationLayer={true}
            customTextRenderer={highlightKeywords.length > 0 ? customTextRenderer : undefined}
            className="shadow-xl"
            loading={
              <div className="flex items-center justify-center h-[800px] w-[600px] bg-white">
                <div className="animate-pulse text-gray-400">載入頁面...</div>
              </div>
            }
          />
        </Document>
      </div>

      {/* 高亮樣式 */}
      <style>{`
        .pdf-highlight {
          background-color: #fef08a !important;
          padding: 2px 0;
          border-radius: 2px;
          box-shadow: 0 0 0 2px #fef08a;
        }
        
        .react-pdf__Page__textContent {
          user-select: text;
        }
        
        .react-pdf__Page__textContent mark {
          background-color: #fef08a !important;
          color: inherit;
        }
      `}</style>
    </div>
  );
}
