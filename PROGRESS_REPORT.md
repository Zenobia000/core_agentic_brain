# OpenCode Platform - 進度報告

> 更新日期：2025-01-26
> 狀態：Cohere 整合完成

---

## 📊 整體完成度

| 模組 | 完成度 | 狀態 |
|------|--------|------|
| 後端架構 | 95% | ✅ 完成 |
| 前端 UI | 85% | ✅ 基本完成 |
| RAG 搜尋 | 95% | ✅ **Cohere 整合完成** |
| PDF 解析 | 95% | ✅ **DoclingReader + PyMuPDF** |
| 口語化理解 | 70% | ✅ 已實現 |

---

## 🆕 本次更新：Cohere 整合

### 架構變更

| 項目 | 舊架構 | **新架構** |
|------|--------|-----------|
| PDF 解析 | PyPDF2 (問題多) | **DoclingReader + PyMuPDF 備用** |
| Embedding | OpenAI (1536 dim) | **Cohere embed-multilingual-v3.0 (1024 dim)** |
| 多語言支援 | 一般 | **優秀 (100+ 語言)** |

### 新增檔案

```
services/knowledge_base/
├── parser.py      # 🆕 PDF 解析 (DoclingReader + PyMuPDF)
├── indexer.py     # 🆕 Cohere Embedding 索引
├── retriever.py   # 🆕 Cohere 查詢
└── service.py     # ✏️ 整合新模組
```

### Cohere 關鍵特性

1. **input_type 區分**：
   - 索引文件：`input_type="search_document"`
   - 查詢時：`input_type="search_query"`

2. **向量維度**：1024 (vs OpenAI 1536)

3. **多語言支援**：100+ 語言，中英文混合查詢效果優秀

---

## ⚠️ 重要：首次使用步驟

### 1. 安裝新依賴

```powershell
pip install cohere pymupdf --break-system-packages
pip install llama-index llama-index-readers-docling --break-system-packages
```

### 2. 設定 Cohere API Key

```powershell
# 編輯 .env 檔案
# 新增: COHERE_API_KEY=your_key_here
```

取得 API Key: https://dashboard.cohere.com/api-keys (免費)

### 3. 重置 Qdrant (必要！維度變更)

```powershell
curl -X POST http://localhost:8000/debug/qdrant/reset
```

### 4. 重新上傳 PDF

在前端「文件」頁面重新上傳 PDF

### 5. 驗證

```powershell
# 檢查數據
curl http://localhost:8000/debug/qdrant

# 應該看到:
# - text_preview 有實際內容
# - embed_dim: 1024 (如果用 Cohere)
```

---

## ✅ 已完成功能

### 後端

| 功能 | 檔案 | 說明 |
|------|------|------|
| PDF 解析 | `parser.py` | DoclingReader + PyMuPDF 備用 |
| Embedding | `indexer.py` | Cohere/OpenAI 雙支援 |
| 向量搜尋 | `retriever.py` | 支援過濾條件 |
| 服務整合 | `service.py` | 統一 API |
| 診斷端點 | `api/main.py` | `/debug/qdrant`, `/debug/qdrant/reset` |

### 前端

| 功能 | 說明 |
|------|------|
| 對話介面 | 串流對話 + 文件選擇 |
| PDF 預覽 | iframe 方式 |
| 文件管理 | 上傳、刪除、列表 |
| 搜尋面板 | 語意搜尋 |

---

## 📦 依賴清單

### Python (requirements.txt)

```txt
# Core
openai>=1.0.0
cohere>=5.0.0

# RAG
llama-index>=0.11.0
llama-index-readers-docling>=0.3.0
pymupdf>=1.23.0
qdrant-client>=1.7.0

# Web
fastapi>=0.108.0
uvicorn>=0.25.0
```

---

## 🚀 啟動指令

```powershell
# 後端
cd opencode-platform
python -m cli.main api

# 前端
cd frontend
npm run dev

# 訪問
# 前端: http://localhost:5173
# 後端: http://localhost:8000
# API 文件: http://localhost:8000/docs
```

---

## 📋 下次對話的起點

1. **首先**：執行 Cohere 整合步驟 (安裝依賴、設定 API Key、重置 Qdrant)
2. **測試**：上傳 PDF 後嘗試對話
3. **驗證**：確認 `/debug/qdrant` 顯示正確的 text_preview

---

> 📅 最後更新：2025-01-26
> 💡 如有問題，請在下一個對話框繼續討論！
