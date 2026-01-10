import React, { useState, useEffect, useCallback } from 'react';
import { FileText, Trash2, Check, Upload, RefreshCw } from 'lucide-react';

/**
 * 多 PDF 選擇器組件 - Manus 深色主題
 */
export default function DocumentList({ 
  selectedDocs, 
  onSelectionChange, 
  onUploadSuccess,
  darkMode = true 
}) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDocuments = useCallback(async () => {
    try {
      setError(null);
      const res = await fetch('http://localhost:8001/documents');
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      setDocuments(data.documents);
      
      // 預設全選已索引的文件
      if (selectedDocs.length === 0 && data.documents.length > 0) {
        const indexedDocs = data.documents.filter(d => d.indexed).map(d => d.name);
        if (indexedDocs.length > 0) {
          onSelectionChange(indexedDocs);
        }
      }
    } catch (err) {
      setError('載入失敗');
    } finally {
      setLoading(false);
    }
  }, [selectedDocs.length, onSelectionChange]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const toggleDocument = (docName) => {
    if (selectedDocs.includes(docName)) {
      onSelectionChange(selectedDocs.filter(d => d !== docName));
    } else {
      onSelectionChange([...selectedDocs, docName]);
    }
  };

  const selectAll = () => {
    onSelectionChange(documents.filter(d => d.indexed).map(d => d.name));
  };

  const deselectAll = () => {
    onSelectionChange([]);
  };

  const deleteDocument = async (filename, e) => {
    e.stopPropagation();
    if (!window.confirm(`確定刪除 "${filename}"？`)) return;

    try {
      await fetch(`http://localhost:8001/documents/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
      });
      onSelectionChange(selectedDocs.filter(d => d !== filename));
      fetchDocuments();
    } catch (err) {
      alert('刪除失敗');
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <RefreshCw className="w-5 h-5 text-white/30 animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* 操作按鈕 */}
      <div className="px-3 py-2 flex items-center justify-between border-b border-white/5">
        <span className="text-xs text-white/40">
          {selectedDocs.length}/{documents.filter(d => d.indexed).length} 已選
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={selectAll}
            className="text-xs text-violet-400 hover:text-violet-300 transition-colors"
          >
            全選
          </button>
          <span className="text-white/20">|</span>
          <button
            onClick={deselectAll}
            className="text-xs text-white/40 hover:text-white/60 transition-colors"
          >
            清除
          </button>
        </div>
      </div>

      {/* 文件列表 */}
      <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1">
        {documents.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-white/30">
            <FileText className="w-8 h-8 mb-2" />
            <p className="text-sm">尚無文件</p>
          </div>
        ) : (
          documents.map((doc) => (
            <div
              key={doc.name}
              onClick={() => doc.indexed && toggleDocument(doc.name)}
              className={`
                group relative flex items-center gap-2 px-2 py-2 rounded-lg cursor-pointer transition-all duration-150
                ${!doc.indexed ? 'opacity-50 cursor-not-allowed' : ''}
                ${selectedDocs.includes(doc.name)
                  ? 'bg-violet-500/20 border border-violet-500/30'
                  : 'hover:bg-white/5 border border-transparent'
                }
              `}
            >
              {/* Checkbox */}
              <div className={`
                w-4 h-4 rounded flex items-center justify-center flex-shrink-0 transition-all
                ${selectedDocs.includes(doc.name)
                  ? 'bg-violet-500 text-white'
                  : 'bg-white/10 border border-white/20'
                }
              `}>
                {selectedDocs.includes(doc.name) && (
                  <Check className="w-3 h-3" />
                )}
              </div>

              {/* 文件資訊 */}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white/80 truncate" title={doc.name}>
                  {doc.name}
                </p>
                <div className="flex items-center gap-2 text-[10px] text-white/40">
                  <span>{formatSize(doc.size)}</span>
                  <span>•</span>
                  {doc.indexed ? (
                    <span className="text-emerald-400">{doc.vector_count} 向量</span>
                  ) : (
                    <span className="text-amber-400">索引中...</span>
                  )}
                </div>
              </div>

              {/* 刪除按鈕 */}
              <button
                onClick={(e) => deleteDocument(doc.name, e)}
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded transition-all"
              >
                <Trash2 className="w-3.5 h-3.5 text-red-400" />
              </button>
            </div>
          ))
        )}
      </div>

      {/* 錯誤提示 */}
      {error && (
        <div className="px-3 py-2 bg-red-500/10 border-t border-red-500/20">
          <p className="text-xs text-red-400">{error}</p>
        </div>
      )}
    </div>
  );
}
