import React, { useState, useEffect } from 'react'
import { 
  MessageSquare, 
  FileText, 
  Search, 
  Settings, 
  Database,
  Sun,
  Moon,
  Menu,
  X,
  Microscope
} from 'lucide-react'
import ChatInterface from './components/ChatInterface'
import DocumentList from './components/DocumentList'
import SearchPanel from './components/SearchPanel'
import AdminPanel from './components/AdminPanel'
import ResearchPanel from './components/ResearchPanel'
import clsx from 'clsx'

const API_BASE = '/api'

// 側邊欄導航項目
const navItems = [
  { id: 'chat', label: '對話', icon: MessageSquare },
  { id: 'documents', label: '文件', icon: FileText },
  { id: 'search', label: '搜尋', icon: Search },
  { id: 'research', label: '研究', icon: Microscope },
  { id: 'admin', label: '管理', icon: Database },
]

function App() {
  const [activeTab, setActiveTab] = useState('chat')
  const [darkMode, setDarkMode] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [documents, setDocuments] = useState([])
  const [selectedDocs, setSelectedDocs] = useState([])
  const [stats, setStats] = useState(null)
  const [isConnected, setIsConnected] = useState(false)

  // 載入深色模式設定
  useEffect(() => {
    const isDark = localStorage.getItem('darkMode') === 'true'
    setDarkMode(isDark)
    if (isDark) {
      document.documentElement.classList.add('dark')
    }
  }, [])

  // 切換深色模式
  const toggleDarkMode = () => {
    const newMode = !darkMode
    setDarkMode(newMode)
    localStorage.setItem('darkMode', String(newMode))
    document.documentElement.classList.toggle('dark', newMode)
  }

  // 檢查連線狀態
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`)
        if (res.ok) {
          setIsConnected(true)
        } else {
          setIsConnected(false)
        }
      } catch {
        setIsConnected(false)
      }
    }
    
    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  // 載入文件列表
  const loadDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE}/documents`)
      if (res.ok) {
        const data = await res.json()
        setDocuments(data)
      }
    } catch (error) {
      console.error('載入文件失敗:', error)
    }
  }

  // 載入統計資訊
  const loadStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`)
      if (res.ok) {
        const data = await res.json()
        setStats(data)
      }
    } catch (error) {
      console.error('載入統計失敗:', error)
    }
  }

  useEffect(() => {
    if (isConnected) {
      loadDocuments()
      loadStats()
    }
  }, [isConnected])

  // 渲染當前頁面內容
  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return (
          <ChatInterface 
            documents={documents}
            selectedDocs={selectedDocs}
            onSelectDocs={setSelectedDocs}
            apiBase={API_BASE}
          />
        )
      case 'documents':
        return (
          <DocumentList 
            documents={documents}
            selectedDocs={selectedDocs}
            onSelectDocs={setSelectedDocs}
            onRefresh={loadDocuments}
            apiBase={API_BASE}
          />
        )
      case 'search':
        return (
          <SearchPanel apiBase={API_BASE} />
        )
      case 'research':
        return (
          <ResearchPanel documents={documents} apiBase={API_BASE} />
        )
      case 'admin':
        return (
          <AdminPanel 
            stats={stats}
            onRefresh={loadStats}
            apiBase={API_BASE}
          />
        )
      default:
        return null
    }
  }

  return (
    <div className="h-screen flex bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      {/* 側邊欄 */}
      <aside 
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">OC</span>
            </div>
            <span className="font-semibold text-lg">OpenCode</span>
          </div>
          <button 
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 導航 */}
        <nav className="p-4 space-y-1">
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={clsx('sidebar-item w-full', activeTab === item.id && 'active')}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        {/* 連線狀態 */}
        <div className="absolute bottom-4 left-4 right-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <div className={clsx(
              'w-2 h-2 rounded-full',
              isConnected ? 'bg-green-500' : 'bg-red-500'
            )} />
            <span>{isConnected ? '已連線' : '離線'}</span>
          </div>
        </div>
      </aside>

      {/* 側邊欄遮罩 (手機) */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* 主內容區 */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* 頂部欄 */}
        <header className="h-16 flex items-center justify-between px-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            >
              <Menu className="w-5 h-5" />
            </button>
            <h1 className="text-xl font-semibold">
              {navItems.find(i => i.id === activeTab)?.label}
            </h1>
          </div>
          
          <div className="flex items-center gap-2">
            {/* 選中文件數量 */}
            {selectedDocs.length > 0 && (
              <span className="px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-sm rounded-full">
                {selectedDocs.length} 文件已選
              </span>
            )}
            
            {/* 深色模式切換 */}
            <button
              onClick={toggleDarkMode}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title={darkMode ? '切換淺色模式' : '切換深色模式'}
            >
              {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            
            {/* 設定 */}
            <button
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title="設定"
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* 頁面內容 */}
        <div className="flex-1 overflow-hidden">
          {renderContent()}
        </div>
      </main>
    </div>
  )
}

export default App
