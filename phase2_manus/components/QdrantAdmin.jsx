import React, { useState, useEffect } from 'react';
import { Database, Trash2, RefreshCw, ChevronRight, FileText, Layers, HardDrive } from 'lucide-react';

/**
 * Qdrant 管理組件 - Manus 風格
 */
export default function QdrantAdmin({ darkMode = true }) {
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState(null);
  const [collectionInfo, setCollectionInfo] = useState(null);
  const [points, setPoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [nextOffset, setNextOffset] = useState(null);

  useEffect(() => {
    fetchCollections();
  }, []);

  const fetchCollections = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://localhost:8001/qdrant/collections');
      const data = await res.json();
      setCollections(data.collections);
    } catch (err) {
      setError('無法連接 Qdrant');
    } finally {
      setLoading(false);
    }
  };

  const selectCollection = async (name) => {
    setSelectedCollection(name);
    setPoints([]);
    try {
      const infoRes = await fetch(`http://localhost:8001/qdrant/collection/${name}`);
      const info = await infoRes.json();
      setCollectionInfo(info);
      await loadPoints(name);
    } catch (err) {
      setError('載入失敗');
    }
  };

  const loadPoints = async (name, offset = null) => {
    const url = new URL(`http://localhost:8001/qdrant/collection/${name}/points`);
    url.searchParams.set('limit', '20');
    if (offset) url.searchParams.set('offset', offset);
    
    const res = await fetch(url);
    const data = await res.json();
    
    setPoints(prev => offset ? [...prev, ...data.points] : data.points);
    setNextOffset(data.next_offset);
  };

  const deleteCollection = async (name) => {
    if (!window.confirm(`確定刪除 "${name}"？此操作無法復原！`)) return;
    
    await fetch(`http://localhost:8001/qdrant/collection/${name}`, { method: 'DELETE' });
    fetchCollections();
    setSelectedCollection(null);
    setCollectionInfo(null);
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num;
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <RefreshCw className="w-6 h-6 text-white/30 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Database className="w-12 h-12 text-red-400/50 mx-auto mb-4" />
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={fetchCollections}
            className="px-4 py-2 bg-white/10 text-white rounded-lg hover:bg-white/20"
          >
            重試
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex">
      {/* 左側：Collections 列表 */}
      <div className="w-72 border-r border-white/5 flex flex-col">
        <div className="p-4 border-b border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-violet-400" />
            <span className="font-medium text-white">Collections</span>
          </div>
          <button
            onClick={fetchCollections}
            className="p-1.5 hover:bg-white/5 rounded-md transition-colors"
          >
            <RefreshCw className="w-4 h-4 text-white/40" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {collections.map((col) => (
            <div
              key={col.name}
              onClick={() => selectCollection(col.name)}
              className={`
                p-3 rounded-lg cursor-pointer transition-all
                ${selectedCollection === col.name
                  ? 'bg-violet-500/20 border border-violet-500/30'
                  : 'hover:bg-white/5 border border-transparent'
                }
              `}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-white">{col.name}</span>
                <ChevronRight className={`w-4 h-4 text-white/30 transition-transform ${selectedCollection === col.name ? 'rotate-90' : ''}`} />
              </div>
              <div className="flex items-center gap-3 text-xs text-white/40">
                <span>{formatNumber(col.points_count)} pts</span>
                <span>{formatNumber(col.vectors_count)} vecs</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 右側：詳細資訊 */}
      <div className="flex-1 flex flex-col">
        {selectedCollection && collectionInfo ? (
          <>
            {/* 標題 */}
            <div className="p-4 border-b border-white/5 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white">{collectionInfo.name}</h3>
                <div className="flex items-center gap-3 mt-1 text-xs text-white/40">
                  <span>維度: {collectionInfo.config?.size || 'N/A'}</span>
                  <span>距離: {collectionInfo.config?.distance || 'N/A'}</span>
                </div>
              </div>
              <button
                onClick={() => deleteCollection(selectedCollection)}
                className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                <span className="text-sm">刪除</span>
              </button>
            </div>

            {/* 統計卡片 */}
            <div className="p-4 grid grid-cols-3 gap-4 border-b border-white/5">
              <div className="bg-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Layers className="w-4 h-4 text-blue-400" />
                  <span className="text-xs text-white/40">Points</span>
                </div>
                <span className="text-2xl font-bold text-white">{formatNumber(collectionInfo.points_count)}</span>
              </div>
              <div className="bg-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <HardDrive className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs text-white/40">Vectors</span>
                </div>
                <span className="text-2xl font-bold text-white">{formatNumber(collectionInfo.vectors_count)}</span>
              </div>
              <div className="bg-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="w-4 h-4 text-violet-400" />
                  <span className="text-xs text-white/40">Documents</span>
                </div>
                <span className="text-2xl font-bold text-white">{collectionInfo.documents?.length || 0}</span>
              </div>
            </div>

            {/* 文件分布 */}
            {collectionInfo.documents?.length > 0 && (
              <div className="p-4 border-b border-white/5">
                <h4 className="text-sm font-medium text-white/50 mb-3">向量分布</h4>
                <div className="space-y-2">
                  {collectionInfo.documents.slice(0, 5).map((doc, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-xs text-white/50 w-40 truncate">{doc.name}</span>
                      <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-violet-500 to-fuchsia-500"
                          style={{ width: `${(doc.vectors / collectionInfo.vectors_count) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-white/30 w-16 text-right">{doc.vectors}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Points 列表 */}
            <div className="flex-1 flex flex-col min-h-0 p-4">
              <h4 className="text-sm font-medium text-white/50 mb-3">
                Points 瀏覽 <span className="text-white/30">({points.length})</span>
              </h4>
              <div className="flex-1 overflow-y-auto space-y-2">
                {points.map((point) => (
                  <div key={point.id} className="p-3 bg-white/5 rounded-lg border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-mono text-white/30 bg-white/5 px-2 py-0.5 rounded">
                        {point.id.slice(0, 8)}...
                      </span>
                      <span className="text-xs text-white/40">
                        {point.payload?.source} · p.{point.payload?.page}
                      </span>
                    </div>
                    <p className="text-xs text-white/50 line-clamp-2">{point.payload?.content}</p>
                  </div>
                ))}
              </div>
              {nextOffset && (
                <button
                  onClick={() => loadPoints(selectedCollection, nextOffset)}
                  className="mt-3 w-full py-2 bg-white/5 text-white/50 rounded-lg hover:bg-white/10 text-sm"
                >
                  載入更多
                </button>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Database className="w-16 h-16 text-white/10 mx-auto mb-4" />
              <p className="text-white/30">選擇一個 Collection 查看詳情</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
