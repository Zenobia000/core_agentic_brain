import { useState, useEffect } from 'react';
import axios from 'axios';
import PDFViewer from './components/PDFViewer';
import ChatInterface from './components/ChatInterface';
import { Upload, FileText, AlertCircle, Loader2, CheckCircle2, Zap, Database } from 'lucide-react';

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
  
  // 🆕 高亮關鍵字
  const [highlightKeyword, setHighlightKeyword] = useState('');
  
  // 🆕 知識庫統計
  const [kbStats, setKbStats] = useState(null);

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
    // 每 30 秒更新一次
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
            // 更新知識庫統計
            const statsResponse = await axios.get(`${API_BASE_URL}/stats`);
            setKbStats(statsResponse.data);
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
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setPdfFile(file);
      setPdfUrl(`${API_BASE_URL}/files/${file.name}`);
      setProcessingStatus('processing');
      setProcessingMessage('正在解析文件...');
      
      setMessages([
        {
          type: 'system',
          content: `📄 已上傳文件：${file.name}，正在處理中...`
        }
      ]);
    } catch (error) {
      setUploadError(error.response?.data?.detail || '上傳失敗，請稍後再試');
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSourceClick = (pageLabel) => {
    const pageNum = parseInt(pageLabel);
    if (!isNaN(pageNum)) {
      setCurrentPage(pageNum);
    }
  };

  return (
    <div className="h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-700/50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">企業知識庫助手</h1>
            <p className="text-sm text-slate-400">Agentic RAG 智能問答系統</p>
          </div>
        </div>

        {/* 中間：知識庫統計 */}
        {kbStats && (
          <div className="flex items-center gap-4 px-4 py-2 bg-slate-800/50 rounded-lg border border-slate-700/30">
            <Database className="w-4 h-4 text-blue-400" />
            <div className="flex items-center gap-4 text-sm">
              <div>
                <span className="text-slate-400">文件：</span>
                <span className="text-white font-medium">{kbStats.document_count}</span>
              </div>
              <div className="w-px h-4 bg-slate-700" />
              <div>
                <span className="text-slate-400">區塊：</span>
                <span className="text-white font-medium">{kbStats.total_chunks}</span>
              </div>
            </div>
          </div>
        )}

        {/* 右側：上傳按鈕 & 狀態 */}
        <div className="flex items-center gap-4">
          {/* 處理狀態顯示 */}
          {processingStatus === 'processing' && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <Loader2 className="w-4 h-4 text-yellow-400 animate-spin" />
              <span className="text-sm text-yellow-300">{processingMessage}</span>
            </div>
          )}
          
          {processingStatus === 'completed' && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-lg">
              <CheckCircle2 className="w-4 h-4 text-green-400" />
              <span className="text-sm text-green-300">可以開始提問</span>
            </div>
          )}

          <label className="relative cursor-pointer">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              className="hidden"
              disabled={isUploading || processingStatus === 'processing'}
            />
            <div className={`
              flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all
              ${(isUploading || processingStatus === 'processing')
                ? 'bg-slate-700 text-slate-400 cursor-not-allowed' 
                : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white shadow-lg hover:shadow-xl'
              }
            `}>
              {isUploading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              {isUploading ? '上傳中...' : '上傳 PDF'}
            </div>
          </label>
        </div>
      </header>

      {/* Upload Error Alert */}
      {uploadError && (
        <div className="mx-6 mt-4 px-4 py-3 bg-red-500/10 border border-red-500/50 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-red-400 font-medium">上傳失敗</p>
            <p className="text-red-300/80 text-sm mt-1">{uploadError}</p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex gap-4 p-6 min-h-0">
        {/* Left: PDF Viewer */}
        <div className="w-1/2 bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
          <PDFViewer 
            pdfUrl={pdfUrl} 
            currentPage={currentPage}
            onPageChange={setCurrentPage}
            highlightKeyword={highlightKeyword}
          />
        </div>

        {/* Right: Chat Interface */}
        <div className="w-1/2 bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
          <ChatInterface 
            messages={messages}
            setMessages={setMessages}
            onSourceClick={handleSourceClick}
            isProcessing={processingStatus === 'processing'}
            highlightKeyword={setHighlightKeyword}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
