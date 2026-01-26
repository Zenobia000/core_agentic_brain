import React, { useState, useEffect } from 'react'
import { 
  Database, 
  FileText, 
  HardDrive, 
  RefreshCw, 
  Activity,
  Server,
  Cpu,
  Clock,
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react'
import clsx from 'clsx'

function AdminPanel({ stats, onRefresh, apiBase }) {
  const [health, setHealth] = useState(null)
  const [services, setServices] = useState([])
  const [isLoading, setIsLoading] = useState(false)

  // 載入健康狀態
  const loadHealth = async () => {
    try {
      const res = await fetch(`${apiBase}/health`)
      if (res.ok) {
        setHealth(await res.json())
      }
    } catch (error) {
      console.error('載入健康狀態失敗:', error)
    }
  }

  // 載入服務列表
  const loadServices = async () => {
    try {
      const res = await fetch(`${apiBase}/services`)
      if (res.ok) {
        setServices(await res.json())
      }
    } catch (error) {
      console.error('載入服務列表失敗:', error)
    }
  }

  useEffect(() => {
    loadHealth()
    loadServices()
  }, [apiBase])

  const handleRefresh = async () => {
    setIsLoading(true)
    await Promise.all([loadHealth(), loadServices(), onRefresh()])
    setIsLoading(false)
  }

  // 統計卡片資料
  const statCards = [
    {
      label: '文件數量',
      value: stats?.document_count || 0,
      icon: FileText,
      color: 'blue'
    },
    {
      label: '向量數量',
      value: stats?.vector_count || stats?.points_count || 0,
      icon: Database,
      color: 'green'
    },
    {
      label: '索引大小',
      value: formatBytes(stats?.index_size || 0),
      icon: HardDrive,
      color: 'purple'
    },
    {
      label: '系統狀態',
      value: health?.status === 'healthy' ? '正常' : '異常',
      icon: Activity,
      color: health?.status === 'healthy' ? 'green' : 'red'
    }
  ]

  return (
    <div className="h-full overflow-y-auto p-4 space-y-6">
      {/* 標題 */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">系統管理</h2>
        <button
          onClick={handleRefresh}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          <RefreshCw className={clsx('w-4 h-4', isLoading && 'animate-spin')} />
          <span>重新整理</span>
        </button>
      </div>

      {/* 統計卡片 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, idx) => (
          <StatCard key={idx} {...card} />
        ))}
      </div>

      {/* 詳細統計 */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Qdrant 狀態 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-green-500" />
            Qdrant 向量資料庫
          </h3>
          
          <div className="space-y-3">
            <InfoRow 
              label="Collection" 
              value={stats?.collection_name || 'rag_knowledge_base'} 
            />
            <InfoRow 
              label="狀態" 
              value={
                <span className={clsx(
                  'px-2 py-0.5 rounded text-xs font-medium',
                  stats?.status === 'green' 
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                    : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                )}>
                  {stats?.status || 'unknown'}
                </span>
              }
            />
            <InfoRow 
              label="向量維度" 
              value={stats?.vector_dim || stats?.config?.params?.vectors?.size || 1536} 
            />
            <InfoRow 
              label="距離函數" 
              value={stats?.distance || stats?.config?.params?.vectors?.distance || 'Cosine'} 
            />
            <InfoRow 
              label="分段數量" 
              value={stats?.segments_count || 0} 
            />
          </div>
        </div>

        {/* API 健康狀態 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Server className="w-5 h-5 text-blue-500" />
            API 服務狀態
          </h3>
          
          <div className="space-y-3">
            <InfoRow 
              label="狀態" 
              value={
                health?.status === 'healthy' ? (
                  <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
                    <CheckCircle className="w-4 h-4" /> 正常運行
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-red-600 dark:text-red-400">
                    <AlertCircle className="w-4 h-4" /> 異常
                  </span>
                )
              }
            />
            <InfoRow 
              label="引擎就緒" 
              value={health?.engine_ready ? '是' : '否'} 
            />
            <InfoRow 
              label="版本" 
              value={health?.version || '1.0.0'} 
            />
          </div>
        </div>
      </div>

      {/* 可用服務 */}
      {services.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-purple-500" />
            可用服務 ({services.length})
          </h3>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
            {services.map((service, idx) => (
              <ServiceCard key={idx} service={service} />
            ))}
          </div>
        </div>
      )}

      {/* 文件統計 */}
      {stats?.documents && stats.documents.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-orange-500" />
            文件詳情
          </h3>
          
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-2 px-3 font-medium">文件名稱</th>
                  <th className="text-right py-2 px-3 font-medium">區塊數</th>
                  <th className="text-right py-2 px-3 font-medium">頁數</th>
                  <th className="text-right py-2 px-3 font-medium">上傳時間</th>
                </tr>
              </thead>
              <tbody>
                {stats.documents.map((doc, idx) => (
                  <tr 
                    key={idx}
                    className="border-b border-gray-100 dark:border-gray-700/50 last:border-0"
                  >
                    <td className="py-2 px-3 truncate max-w-xs">{doc.name || doc.document_name}</td>
                    <td className="py-2 px-3 text-right">{doc.chunk_count || '-'}</td>
                    <td className="py-2 px-3 text-right">{doc.page_count || '-'}</td>
                    <td className="py-2 px-3 text-right text-gray-500">
                      {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

// 統計卡片組件
function StatCard({ label, value, icon: Icon, color }) {
  const colorClasses = {
    blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
    green: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
    purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
    red: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
    orange: 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400',
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-3">
        <div className={clsx('w-10 h-10 rounded-lg flex items-center justify-center', colorClasses[color])}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
          <p className="text-xl font-semibold">{value}</p>
        </div>
      </div>
    </div>
  )
}

// 資訊列組件
function InfoRow({ label, value }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700/50 last:border-0">
      <span className="text-gray-500 dark:text-gray-400">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  )
}

// 服務卡片組件
function ServiceCard({ service }) {
  const { id, name, description, status } = service

  return (
    <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <div className="flex items-center justify-between mb-1">
        <span className="font-medium text-sm">{name || id}</span>
        <span className={clsx(
          'w-2 h-2 rounded-full',
          status === 'ready' ? 'bg-green-500' : 'bg-yellow-500'
        )} />
      </div>
      {description && (
        <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
          {description}
        </p>
      )}
    </div>
  )
}

// 格式化位元組
function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export default AdminPanel
