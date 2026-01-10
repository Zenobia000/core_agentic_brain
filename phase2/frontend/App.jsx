import React, { useState, useCallback } from 'react';
import DocumentList from './components/DocumentList';
import PDFViewer from './components/PDFViewer';
import ChatPanel from './components/ChatPanel';  // 你原有的 Chat 組件
import ResearchPanel from './components/ResearchPanel';
import QdrantAdmin from './components/QdrantAdmin';

/**
 * RAG 知識庫助手 - Phase 2
 * 整合多 PDF 選擇器、Deep Research、Qdrant 管理
 */
export default function App() {
  // Tab 狀態
  const [activeTab, setActiveTab] = useState('chat');
  
  // PDF 選擇狀態
  const [selectedDocs, setSelectedDocs] = useState([]);
  
  // PDF Viewer 狀態
  const [currentPdf, setCurrentPdf] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [highlightKeywords, setHighlightKeywords] = useState([]);

  // 刷新文件列表的 key
  const [refreshKey, setRefreshKey] = useState(0);

  // 處理來源點擊 - 從 ChatPanel 傳入
  const handleSourceClick = useCallback((source, page, keywords = []) => {
    setCurrentPdf(`http://localhost:8001/files/${source}`);
    setCurrentPage(page || 1);
    setHighlightKeywords(keywords);
  }, []);

  // 處理上傳成功
  const handleUploadSuccess = useCallback(() => {
    setRefreshKey(k => k + 1);
  }, []);

  // Tab 配置
  const tabs = [
    { id: 'chat', label: '💬 對話', icon: '💬' },
    { id: 'research', label: '🔬 研究', icon: '🔬' },
    { id: 'admin', label: '⚙️ 管理', icon: '⚙️' },
  ];

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* 頂部導航 */}
      <header className="bg-white shadow-sm px-6 py-3 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-gray-800">
            📚 RAG 知識庫助手
          </h1>
          <span className="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">
            Phase 2
          </span>
        </div>
        
        {/* Tab 導航 */}
        <nav className="flex gap-1 bg-gray-100 p-1 rounded-lg">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* 狀態指示 */}
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            Qdrant
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            API
          </span>
        </div>
      </header>

      {/* 主內容區 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左側：文件選擇器 (所有 Tab 都顯示) */}
        <aside className="w-72 flex-shrink-0 p-4 overflow-hidden flex flex-col border-r bg-gray-50">
          <DocumentList
            key={refreshKey}
            selectedDocs={selectedDocs}
            onSelectionChange={setSelectedDocs}
            onUploadSuccess={handleUploadSuccess}
          />
        </aside>

        {/* 中間/右側：根據 Tab 顯示不同內容 */}
        <main className="flex-1 flex overflow-hidden">
          {/* 對話 Tab */}
          {activeTab === 'chat' && (
            <>
              {/* PDF 預覽 */}
              <div className="w-1/2 border-r">
                <PDFViewer
                  pdfUrl={currentPdf}
                  currentPage={currentPage}
                  highlightKeywords={highlightKeywords}
                  onPageChange={setCurrentPage}
                />
              </div>
              
              {/* 對話區 */}
              <div className="w-1/2 flex flex-col">
                <ChatPanel
                  selectedDocs={selectedDocs}
                  onSourceClick={handleSourceClick}
                />
              </div>
            </>
          )}
          
          {/* 研究 Tab */}
          {activeTab === 'research' && (
            <div className="flex-1 p-6 overflow-y-auto">
              <ResearchPanel selectedDocs={selectedDocs} />
            </div>
          )}
          
          {/* 管理 Tab */}
          {activeTab === 'admin' && (
            <div className="flex-1 p-6 overflow-y-auto">
              <QdrantAdmin />
            </div>
          )}
        </main>
      </div>

      {/* 底部狀態列（可選） */}
      <footer className="bg-white border-t px-6 py-2 text-xs text-gray-400 flex justify-between">
        <span>
          已選擇 {selectedDocs.length} 個文件進行搜尋
        </span>
        <span>
          RAG Project Phase 2 • Powered by GPT-4o + Qdrant
        </span>
      </footer>
    </div>
  );
}
