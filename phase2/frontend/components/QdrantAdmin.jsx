import React, { useState, useEffect } from 'react';

/**
 * Qdrant 向量資料庫管理組件
 * 支援 Collection 瀏覽、統計、刪除
 */
export default function QdrantAdmin() {
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState(null);
  const [collectionInfo, setCollectionInfo] = useState(null);
  const [points, setPoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [nextOffset, setNextOffset] = useState(null);

  // 載入 Collections 列表
  useEffect(() => {
    fetchCollections();
  }, []);

  const fetchCollections = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const res = await fetch('http://localhost:8001/qdrant/collections');
      if (!res.ok) throw new Error('Failed to fetch collections');
      const data = await res.json();
      setCollections(data.collections);
    } catch (err) {
      console.error('Error fetching collections:', err);
      setError('無法連接 Qdrant，請確認服務正在運行');
    } finally {
      setLoading(false);
    }
  };

  // 選擇 Collection
  const selectCollection = async (name) => {
    setSelectedCollection(name);
    setPoints([]);
    setNextOffset(null);
    
    try {
      // 取得詳細資訊
      const infoRes = await fetch(`http://localhost:8001/qdrant/collection/${name}`);
      if (!infoRes.ok) throw new Error('Failed to fetch collection info');
      const info = await infoRes.json();
      setCollectionInfo(info);
      
      // 取得 Points
      await loadPoints(name);
    } catch (err) {
      console.error('Error fetching collection:', err);
      setError('無法載入 Collection 資訊');
    }
  };

  // 載入 Points
  const loadPoints = async (name, offset = null) => {
    try {
      const url = new URL(`http://localhost:8001/qdrant/collection/${name}/points`);
      url.searchParams.set('limit', '20');
      if (offset) url.searchParams.set('offset', offset);
      
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch points');
      const data = await res.json();
      
      if (offset) {
        setPoints(prev => [...prev, ...data.points]);
      } else {
        setPoints(data.points);
      }
      setNextOffset(data.next_offset);
    } catch (err) {
      console.error('Error fetching points:', err);
    }
  };

  // 刪除 Collection
  const deleteCollection = async (name) => {
    if (!window.confirm(`⚠️ 確定要刪除 Collection "${name}" 嗎？\n\n這將刪除所有向量資料，此操作無法復原！`)) {
      return;
    }

    try {
      const res = await fetch(`http://localhost:8001/qdrant/collection/${name}`, {
        method: 'DELETE'
      });
      
      if (!res.ok) throw new Error('Failed to delete collection');
      
      // 重新載入列表
      fetchCollections();
      setSelectedCollection(null);
      setCollectionInfo(null);
      setPoints([]);
    } catch (err) {
      console.error('Error deleting collection:', err);
      alert('刪除失敗');
    }
  };

  // 格式化數字
  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num;
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <p className="text-gray-500">連接 Qdrant...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">❌</div>
          <p className="text-red-500 mb-4">{error}</p>
          <button
            onClick={fetchCollections}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            重試
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <span>🗄️</span>
          <span>Qdrant 向量資料庫管理</span>
        </h2>
        <button
          onClick={fetchCollections}
          className="px-4 py-2 bg-gray-100 rounded hover:bg-gray-200 text-sm flex items-center gap-2"
        >
          <span>🔄</span>
          <span>重新整理</span>
        </button>
      </div>

      <div className="flex-1 flex gap-6 min-h-0">
        {/* 左側：Collections 列表 */}
        <div className="w-80 flex-shrink-0">
          <div className="bg-white rounded-lg shadow p-4 h-full flex flex-col">
            <h3 className="font-semibold text-gray-700 mb-4 flex items-center justify-between">
              <span>Collections</span>
              <span className="text-sm font-normal text-gray-400">{collections.length} 個</span>
            </h3>
            
            {collections.length === 0 ? (
              <div className="flex-1 flex items-center justify-center text-gray-400">
                <div className="text-center">
                  <div className="text-4xl mb-2">📭</div>
                  <p>尚無 Collection</p>
                </div>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto space-y-2">
                {collections.map((col) => (
                  <div
                    key={col.name}
                    className={`p-4 rounded-lg cursor-pointer transition-all ${
                      selectedCollection === col.name
                        ? 'bg-blue-100 border-2 border-blue-300'
                        : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                    }`}
                    onClick={() => selectCollection(col.name)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-800">{col.name}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        col.status === 'Green' || col.status === 'green' 
                          ? 'bg-green-100 text-green-600'
                          : 'bg-yellow-100 text-yellow-600'
                      }`}>
                        {col.status}
                      </span>
                    </div>
                    <div className="flex gap-4 text-xs text-gray-500">
                      <span>📊 {formatNumber(col.points_count)} points</span>
                      <span>🔢 {formatNumber(col.vectors_count)} vectors</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 右側：詳細資訊 */}
        <div className="flex-1 min-w-0">
          {selectedCollection && collectionInfo ? (
            <div className="bg-white rounded-lg shadow p-6 h-full flex flex-col">
              {/* Collection 標題 */}
              <div className="flex items-center justify-between mb-6 pb-4 border-b">
                <div>
                  <h3 className="text-lg font-semibold text-gray-800">
                    {collectionInfo.name}
                  </h3>
                  <div className="flex gap-4 mt-1 text-sm text-gray-500">
                    <span>維度: {collectionInfo.config?.size || 'N/A'}</span>
                    <span>距離: {collectionInfo.config?.distance || 'N/A'}</span>
                  </div>
                </div>
                <button
                  onClick={() => deleteCollection(selectedCollection)}
                  className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
                >
                  🗑️ 刪除 Collection
                </button>
              </div>

              {/* 統計卡片 */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-blue-600">
                    {formatNumber(collectionInfo.points_count)}
                  </div>
                  <div className="text-sm text-blue-500">Points</div>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-green-600">
                    {formatNumber(collectionInfo.vectors_count)}
                  </div>
                  <div className="text-sm text-green-500">Vectors</div>
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                  <div className="text-2xl font-bold text-purple-600">
                    {collectionInfo.documents?.length || 0}
                  </div>
                  <div className="text-sm text-purple-500">Documents</div>
                </div>
              </div>

              {/* 文件統計 */}
              {collectionInfo.documents && collectionInfo.documents.length > 0 && (
                <div className="mb-6">
                  <h4 className="font-medium text-gray-700 mb-3">📄 文件向量分布</h4>
                  <div className="space-y-2">
                    {collectionInfo.documents.map((doc, i) => (
                      <div key={i} className="flex items-center gap-3">
                        <span className="text-sm text-gray-600 w-48 truncate" title={doc.name}>
                          {doc.name}
                        </span>
                        <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
                          <div
                            className="h-full bg-blue-500 rounded-full"
                            style={{
                              width: `${(doc.vectors / collectionInfo.vectors_count) * 100}%`
                            }}
                          />
                        </div>
                        <span className="text-xs text-gray-500 w-20 text-right">
                          {doc.vectors} 向量
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Points 瀏覽 */}
              <div className="flex-1 min-h-0 flex flex-col">
                <h4 className="font-medium text-gray-700 mb-3 flex items-center justify-between">
                  <span>📝 Points 瀏覽</span>
                  <span className="text-sm font-normal text-gray-400">
                    顯示 {points.length} 筆
                  </span>
                </h4>
                
                <div className="flex-1 overflow-y-auto space-y-2">
                  {points.map((point) => (
                    <div key={point.id} className="p-3 bg-gray-50 rounded-lg text-sm">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-mono text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                          ID: {point.id.substring(0, 8)}...
                        </span>
                        <span className="text-xs text-gray-500">
                          📄 {point.payload?.source} | p.{point.payload?.page}
                        </span>
                      </div>
                      <div className="text-gray-600 text-xs line-clamp-2">
                        {point.payload?.content}
                      </div>
                    </div>
                  ))}
                </div>

                {/* 載入更多 */}
                {nextOffset && (
                  <div className="mt-4 text-center">
                    <button
                      onClick={() => loadPoints(selectedCollection, nextOffset)}
                      className="px-4 py-2 bg-gray-100 rounded hover:bg-gray-200 text-sm"
                    >
                      載入更多
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow h-full flex items-center justify-center">
              <div className="text-center text-gray-400">
                <div className="text-6xl mb-4">👈</div>
                <p className="text-lg">選擇一個 Collection 查看詳情</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
