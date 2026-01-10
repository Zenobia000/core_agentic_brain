import { useState, useEffect } from 'react';
import axios from 'axios';
import PDFViewer from './components/PDFViewer';
import ChatInterface from './components/ChatInterface';
import DocumentList from './components/DocumentList';
import ResearchPanel from './components/ResearchPanel';
import QdrantAdmin from './components/QdrantAdmin';
import { 
  Upload, FileText, AlertCircle, Loader2, CheckCircle2, 
  Zap, Database, MessageSquare, FlaskConical, Settings,
  FolderOpen, ChevronRight, Sparkles
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8001';

function App() {
  const [pdfFile, setPdfFile] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [messages, setMessages] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  
  // 處理狀態
  const [processingStatus, setProcessingStatus] = useState(null);
  const [processingMessage, setProcessingMessage] = useState('');
  
  // 高亮關鍵字
  const [highlightKeyword, setHighlightKeyword] = useState('');
  
  // 知識庫統計
  const [kbStats, setKbStats] = useState(null);

  // Phase 2: Tab 切換
  const [activeTab, setActiveTab] = useState('chat');
  
  // Phase 2: 多文件選擇
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [refreshDocList, setRefreshDocList] = useState(0);
  
  // 側邊欄收合
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // 取得知識庫統計
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/stats`);
        setKbStats(response.data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      }
    };
    
    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  // 輪詢處理狀態
  useEffect(() => {
    let intervalId;
    
    if (pdfFile && processingStatus === 'processing') {
      intervalId = setInterval(async () => {
        try {
          const response = await axios.get(`${API_BASE_URL}/status/${pdfFile.name}`);
          setProcessingMessage(response.data.message);
          
          if (response.data.status === 'completed') {
            setProcessingStatus('completed');
            setMessages(prev => [
              ...prev.filter(m => m.type !== 'system' || !m.content.includes('處理中')),
              {
                type: 'system',
                content: `✅ 文件處理完成：${pdfFile.name}，可以開始提問了！`
              }
            ]);
            const statsResponse = await axios.get(`${API_BASE_URL}/stats`);
            setKbStats(statsResponse.data);
            setRefreshDocList(prev => prev + 1);
            clearInterval(intervalId);
          } else if (response.data.status === 'error') {
            setProcessingStatus('error');
            setProcessingMessage(response.data.message);
            clearInterval(intervalId);
          }
        } catch (error) {
          console.error('Status check error:', error);
        }
      }, 1000);
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [pdfFile, processingStatus]);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      setUploadError('請上傳 PDF 檔案');
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setProcessingStatus(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setPdfFile(file);
      setPdfUrl(`${API_BASE_URL}/files/${file.name}`);
      setProcessingStatus('processing');
      setProcessingMessage('正在解析文件...');
      
      setMessages([{
        type: 'system',
        content: `📄 已上傳文件：${file.name}，正在處理中...`
      }]);
    } catch (error) {
      setUploadError(error.response?.data?.detail || '上傳失敗，請稍後再試');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSourceClick = (source, page, keywords = []) => {
    if (typeof source === 'number' || !isNaN(parseInt(source))) {
      setCurrentPage(parseInt(source));
      return;
    }
    
    if (typeof source === 'string' && source.endsWith('.pdf')) {
      setPdfUrl(`${API_BASE_URL}/files/${source}`);
      if (page) setCurrentPage(page);
      if (keywords?.length > 0) setHighlightKeyword(keywords[0]);
    }
  };

  // Tab 配置
  const tabs = [
    { id: 'chat', label: '對話', icon: MessageSquare },
    { id: 'research', label: '深度研究', icon: FlaskConical },
    { id: 'admin', label: '資料管理', icon: Settings },
  ];

  return (
    <div className="h-screen bg-[#0a0a0f] flex flex-col overflow-hidden">
      {/* ===== 頂部導航欄 ===== */}
      <header className="h-14 bg-[#0d0d14] border-b border-white/5 px-4 flex items-center justify-between flex-shrink-0">
        {/* 左側 Logo */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-lg flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-white font-semibold">RAG Assistant</span>
            <span className="text-[10px] px-1.5 py-0.5 bg-violet-500/20 text-violet-400 rounded-full font-medium">
              v2.0
            </span>
          </div>
        </div>

        {/* 中間 Tab 切換 */}
        <nav className="flex items-center gap-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                ${activeTab === tab.id
                  ? 'bg-white/10 text-white'
                  : 'text-white/50 hover:text-white/80 hover:bg-white/5'
                }
              `}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>

        {/* 右側：統計 & 上傳 */}
        <div className="flex items-center gap-3">
          {/* 知識庫統計 */}
          {kbStats && (
            <div className="flex items-center gap-3 px-3 py-1.5 bg-white/5 rounded-lg text-xs">
              <div className="flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-violet-400" />
                <span className="text-white/50">文件</span>
                <span className="text-white font-medium">{kbStats.document_count}</span>
              </div>
              <div className="w-px h-3 bg-white/10" />
              <div className="flex items-center gap-1.5">
                <span className="text-white/50">向量</span>
                <span className="text-white font-medium">{kbStats.total_chunks}</span>
              </div>
            </div>
          )}

          {/* 處理狀態 */}
          {processingStatus === 'processing' && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-500/10 border border-amber-500/20 rounded-lg">
              <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />
              <span className="text-xs text-amber-300">{processingMessage}</span>
            </div>
          )}

          {/* 上傳按鈕 */}
          <label className="cursor-pointer">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              className="hidden"
              disabled={isUploading || processingStatus === 'processing'}
            />
            <div className={`
              flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
              ${(isUploading || processingStatus === 'processing')
                ? 'bg-white/5 text-white/30 cursor-not-allowed'
                : 'bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white shadow-lg shadow-violet-500/25'
              }
            `}>
              {isUploading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              <span>{isUploading ? '上傳中' : '上傳文件'}</span>
            </div>
          </label>
        </div>
      </header>

      {/* 上傳錯誤提示 */}
      {uploadError && (
        <div className="mx-4 mt-3 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-3">
          <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
          <p className="text-sm text-red-300">{uploadError}</p>
        </div>
      )}

      {/* ===== 主內容區 ===== */}
      <div className="flex-1 flex min-h-0">
        {/* 左側邊欄：文件列表 */}
        {(activeTab === 'chat' || activeTab === 'research') && (
          <aside className={`
            ${sidebarCollapsed ? 'w-12' : 'w-64'}
            bg-[#0d0d14] border-r border-white/5 flex flex-col transition-all duration-300
          `}>
            {/* 側邊欄標題 */}
            <div className="h-12 px-3 flex items-center justify-between border-b border-white/5">
              {!sidebarCollapsed && (
                <div className="flex items-center gap-2">
                  <FolderOpen className="w-4 h-4 text-white/50" />
                  <span className="text-sm font-medium text-white/70">知識庫</span>
                </div>
              )}
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="p-1.5 hover:bg-white/5 rounded-md transition-colors"
              >
                <ChevronRight className={`w-4 h-4 text-white/50 transition-transform ${sidebarCollapsed ? '' : 'rotate-180'}`} />
              </button>
            </div>

            {/* 文件列表 */}
            {!sidebarCollapsed && (
              <div className="flex-1 overflow-hidden">
                <DocumentList
                  key={refreshDocList}
                  selectedDocs={selectedDocs}
                  onSelectionChange={setSelectedDocs}
                  onUploadSuccess={() => setRefreshDocList(prev => prev + 1)}
                  darkMode={true}
                />
              </div>
            )}
          </aside>
        )}

        {/* 主內容 */}
        <main className="flex-1 flex min-h-0">
          {/* ===== 對話 Tab ===== */}
          {activeTab === 'chat' && (
            <>
              {/* 左側：PDF 預覽 */}
              <div className="flex-1 bg-[#12121a] m-3 mr-1.5 rounded-xl border border-white/5 overflow-hidden">
                <PDFViewer 
                  pdfUrl={pdfUrl} 
                  currentPage={currentPage}
                  onPageChange={setCurrentPage}
                  highlightKeyword={highlightKeyword}
                  darkMode={true}
                />
              </div>

              {/* 右側：對話 */}
              <div className="w-[420px] flex-shrink-0 bg-[#12121a] m-3 ml-1.5 rounded-xl border border-white/5 overflow-hidden">
                <ChatInterface 
                  messages={messages}
                  setMessages={setMessages}
                  onSourceClick={handleSourceClick}
                  isProcessing={processingStatus === 'processing'}
                  highlightKeyword={setHighlightKeyword}
                  selectedDocs={selectedDocs}
                  darkMode={true}
                />
              </div>
            </>
          )}

          {/* ===== 研究 Tab ===== */}
          {activeTab === 'research' && (
            <div className="flex-1 bg-[#12121a] m-3 rounded-xl border border-white/5 overflow-hidden">
              <ResearchPanel 
                selectedDocs={selectedDocs} 
                darkMode={true}
              />
            </div>
          )}

          {/* ===== 管理 Tab ===== */}
          {activeTab === 'admin' && (
            <div className="flex-1 bg-[#12121a] m-3 rounded-xl border border-white/5 overflow-hidden">
              <QdrantAdmin darkMode={true} />
            </div>
          )}
        </main>
      </div>

      {/* ===== 底部狀態欄 ===== */}
      <footer className="h-8 bg-[#0d0d14] border-t border-white/5 px-4 flex items-center justify-between text-xs text-white/30">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
            <span>Qdrant 已連接</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
            <span>GPT-4o 就緒</span>
          </div>
        </div>
        <div>
          {selectedDocs.length > 0 
            ? `已選擇 ${selectedDocs.length} 個文件` 
            : '搜尋全部文件'
          }
        </div>
      </footer>
    </div>
  );
}

export default App;
