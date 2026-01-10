import React, { useState, useEffect, useCallback } from 'react';

/**
 * 多 PDF 選擇器組件
 * 顯示知識庫中的所有文件，支援多選篩選搜尋範圍
 */
export default function DocumentList({ selectedDocs, onSelectionChange, onUploadSuccess }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(null);

  // 載入文件列表
  const fetchDocuments = useCallback(async () => {
    try {
      setError(null);
      const res = await fetch('http://localhost:8001/documents');
      if (!res.ok) throw new Error('Failed to fetch documents');
      const data = await res.json();
      setDocuments(data.documents);
      
      // 如果沒有選擇任何文件，預設全選所有已索引的文件
      if (selectedDocs.length === 0 && data.documents.length > 0) {
        const indexedDocs = data.documents
          .filter(d => d.indexed)
          .map(d => d.name);
        if (indexedDocs.length > 0) {
          onSelectionChange(indexedDocs);
        }
      }
    } catch (err) {
      console.error('Failed to fetch documents:', err);
      setError('無法載入文件列表');
    } finally {
      setLoading(false);
    }
  }, [selectedDocs.length, onSelectionChange]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // 切換單個文件選擇
  const toggleDocument = (docName) => {
    if (selectedDocs.includes(docName)) {
      onSelectionChange(selectedDocs.filter(d => d !== docName));
    } else {
      onSelectionChange([...selectedDocs, docName]);
    }
  };

  // 全選已索引的文件
  const selectAllIndexed = () => {
    const indexedDocs = documents.filter(d => d.indexed).map(d => d.name);
    onSelectionChange(indexedDocs);
  };

  // 取消全選
  const deselectAll = () => {
    onSelectionChange([]);
  };

  // 刪除文件
  const deleteDocument = async (filename, e) => {
    e.stopPropagation();
    
    if (!window.confirm(`確定要刪除 "${filename}" 嗎？\n這將同時刪除檔案和向量索引。`)) {
      return;
    }

    try {
      const res = await fetch(`http://localhost:8001/documents/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
      });
      
      if (!res.ok) throw new Error('Failed to delete');
      
      // 從選擇中移除
      onSelectionChange(selectedDocs.filter(d => d !== filename));
      
      // 重新載入列表
      fetchDocuments();
    } catch (err) {
      console.error('Failed to delete document:', err);
      alert('刪除失敗');
    }
  };

  // 處理文件上傳
  const handleUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploadProgress({ current: 0, total: files.length, status: 'uploading' });

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const formData = new FormData();
      formData.append('file', file);

      try {
        setUploadProgress({ current: i + 1, total: files.length, status: 'uploading', filename: file.name });
        
        const res = await fetch('http://localhost:8001/upload', {
          method: 'POST',
          body: formData
        });

        if (!res.ok) throw new Error(`Failed to upload ${file.name}`);
      } catch (err) {
        console.error(`Upload error for ${file.name}:`, err);
        setUploadProgress(prev => ({ ...prev, status: 'error', error: file.name }));
      }
    }

    setUploadProgress({ current: files.length, total: files.length, status: 'done' });
    
    // 清除 input
    e.target.value = '';
    
    // 重新載入列表
    setTimeout(() => {
      fetchDocuments();
      setUploadProgress(null);
      if (onUploadSuccess) onUploadSuccess();
    }, 1500);
  };

  // 格式化文件大小
  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  // 統計
  const indexedCount = documents.filter(d => d.indexed).length;
  const selectedCount = selectedDocs.length;
  const totalVectors = documents.reduce((sum, d) => sum + (d.vector_count || 0), 0);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow flex flex-col h-full">
      {/* 標題 */}
      <div className="p-4 border-b">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-semibold text-gray-700 flex items-center gap-2">
            <span>📂</span>
            <span>知識庫文件</span>
          </h3>
          <div className="flex gap-2 text-xs">
            <button
              onClick={selectAllIndexed}
              className="text-blue-600 hover:text-blue-800 hover:underline"
            >
              全選
            </button>
            <span className="text-gray-300">|</span>
            <button
              onClick={deselectAll}
              className="text-gray-500 hover:text-gray-700 hover:underline"
            >
              清除
            </button>
          </div>
        </div>
        
        {/* 統計資訊 */}
        <div className="flex gap-4 text-xs text-gray-500">
          <span>📄 {documents.length} 個文件</span>
          <span>✅ {indexedCount} 已索引</span>
          <span>🔢 {totalVectors} 向量</span>
        </div>
      </div>

      {/* 上傳區 */}
      <div className="p-3 border-b bg-gray-50">
        <label className="flex items-center justify-center gap-2 p-3 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors">
          <span className="text-xl">📤</span>
          <span className="text-sm text-gray-600">
            {uploadProgress ? (
              uploadProgress.status === 'done' ? '✅ 上傳完成！' :
              uploadProgress.status === 'error' ? `❌ ${uploadProgress.error} 失敗` :
              `上傳中 ${uploadProgress.current}/${uploadProgress.total}...`
            ) : '點擊或拖曳上傳 PDF'}
          </span>
          <input
            type="file"
            accept=".pdf"
            multiple
            onChange={handleUpload}
            className="hidden"
            disabled={uploadProgress && uploadProgress.status === 'uploading'}
          />
        </label>
      </div>

      {/* 錯誤提示 */}
      {error && (
        <div className="p-3 bg-red-50 text-red-600 text-sm">
          ⚠️ {error}
          <button onClick={fetchDocuments} className="ml-2 underline">重試</button>
        </div>
      )}

      {/* 文件列表 */}
      <div className="flex-1 overflow-y-auto p-2">
        {documents.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            <div className="text-4xl mb-2">📭</div>
            <p>尚無文件</p>
            <p className="text-xs">上傳 PDF 開始建立知識庫</p>
          </div>
        ) : (
          <div className="space-y-1">
            {documents.map((doc) => (
              <div
                key={doc.name}
                className={`group flex items-center p-3 rounded-lg cursor-pointer transition-all ${
                  selectedDocs.includes(doc.name)
                    ? 'bg-blue-50 border border-blue-200 shadow-sm'
                    : 'bg-gray-50 hover:bg-gray-100 border border-transparent'
                } ${!doc.indexed ? 'opacity-60' : ''}`}
                onClick={() => doc.indexed && toggleDocument(doc.name)}
              >
                {/* Checkbox */}
                <input
                  type="checkbox"
                  checked={selectedDocs.includes(doc.name)}
                  onChange={() => doc.indexed && toggleDocument(doc.name)}
                  disabled={!doc.indexed}
                  className="mr-3 h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
                />
                
                {/* 文件資訊 */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate" title={doc.name}>
                    {doc.name}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span>{formatSize(doc.size)}</span>
                    <span>•</span>
                    {doc.indexed ? (
                      <span className="text-green-600">✅ {doc.vector_count} 向量</span>
                    ) : (
                      <span className="text-yellow-600">⏳ 索引中...</span>
                    )}
                  </div>
                </div>

                {/* 刪除按鈕 */}
                <button
                  onClick={(e) => deleteDocument(doc.name, e)}
                  className="ml-2 p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                  title="刪除文件"
                >
                  🗑️
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 底部選擇狀態 */}
      <div className="p-3 border-t bg-gray-50 text-sm text-gray-600">
        <div className="flex items-center justify-between">
          <span>
            已選擇 <strong className="text-blue-600">{selectedCount}</strong> / {indexedCount} 個文件
          </span>
          {selectedCount > 0 && (
            <span className="text-xs text-gray-400">
              搜尋將限制在選中的文件中
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
