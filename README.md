# 🧠 企業知識庫助手 - Agentic RAG System

一個基於 RAG (Retrieval-Augmented Generation) 的企業知識庫問答系統，整合 OpenCode Agentic 能力，支援多 PDF 索引、智能推理、來源引用。

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![React](https://img.shields.io/badge/React-18-61DAFB.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-FF6B6B.svg)

---

## ✨ 功能特色

| 功能 | 說明 |
|------|------|
| 📄 PDF 上傳與解析 | 使用 IBM Docling 解析 PDF 文件 |
| 🔍 語意搜尋 | Qdrant 向量資料庫 + OpenAI Embeddings |
| 🤖 Agentic RAG | OpenCode 自動推理、多步搜尋 |
| 💬 串流對話 | 即時顯示 AI 推理過程 |
| 📚 來源引用 | 回答附帶論文來源和頁碼 |
| 🔗 MCP 協議 | 標準化工具呼叫介面 |

---

## 🏗️ 系統架構

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React 前端    │────▶│  FastAPI 後端   │────▶│    Qdrant DB    │
│  (Vite + TW)    │     │   (Python)      │     │  (Vector Store) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   MCP Server    │
                        │  (Tool 提供者)   │
                        └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │    OpenCode     │
                        │  (Agentic AI)   │
                        └─────────────────┘
```

---

## 📂 專案結構

```
rag-project/
├── frontend/                    # React 前端
│   ├── src/
│   │   ├── App.jsx             # 主組件
│   │   └── components/
│   │       ├── ChatInterface.jsx    # 對話介面（含推理顯示）
│   │       ├── PDFViewer.jsx        # PDF 預覽
│   │       ├── ThinkingBlock.jsx    # 推理過程組件
│   │       └── ToolCallBlock.jsx    # 工具呼叫組件
│   ├── package.json
│   └── vite.config.js
├── src/                         # Python 後端
│   ├── main.py                  # FastAPI 主程式
│   ├── ingestion/               # PDF 處理
│   │   ├── parser.py            # Docling 解析
│   │   ├── indexer.py           # 向量索引
│   │   └── pipeline.py          # 處理流程
│   ├── retrieval/               # RAG 檢索
│   │   ├── search.py            # 語意搜尋
│   │   ├── generation.py        # 回答生成
│   │   └── agent.py             # Agentic 推理
│   └── mcp/                     # MCP Server
│       ├── __init__.py
│       └── server.py            # FastMCP 工具
├── data/raw/                    # PDF 上傳目錄
├── docs/                        # 文件
│   └── opencode-config.json     # OpenCode 配置範例
├── .env                         # 環境變數（API Keys）
├── requirements.txt             # Python 依賴
├── split_pdf.py                 # PDF 分割工具
└── README.md
```

---

## 🚀 快速開始

### 前置需求

- Python 3.10+
- Node.js 18+
- Docker（用於 Qdrant）
- OpenAI API Key

### 1. Clone 專案

```bash
git clone https://github.com/bai0821/rag-project.git
cd rag-project
```

### 2. 設定環境變數

```bash
# 建立 .env 檔案
echo OPENAI_API_KEY=你的API金鑰 > .env
```

### 3. 安裝依賴

```bash
# Python 依賴
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Node.js 依賴
cd frontend
npm install
cd ..
```

### 4. 啟動 Qdrant

```bash
docker run -d --name qdrant-rag -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### 5. 啟動服務

```bash
# Terminal 1: 後端
python -m src.main
# 運行在 http://localhost:8001

# Terminal 2: 前端
cd frontend
npm run dev
# 運行在 http://localhost:3000
```

### 6. 開始使用

1. 打開 http://localhost:3000
2. 上傳 PDF 文件
3. 等待處理完成
4. 開始提問！

---

## 🤖 OpenCode 整合（Agentic RAG）

### 配置步驟

1. **建立配置檔**

```bash
# Windows
mkdir %USERPROFILE%\.config\opencode
notepad %USERPROFILE%\.config\opencode\opencode.json
```

2. **貼入以下內容**

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "rag-server": {
      "type": "local",
      "command": ["C:\\Users\\你的用戶名\\Desktop\\PortableGit\\rag-project\\.venv\\Scripts\\python.exe", "-m", "src.mcp.server"],
      "enabled": true
    }
  }
}
```

> ⚠️ 請將路徑改成你的實際專案路徑

3. **啟動 OpenCode**

```bash
cd rag-project
opencode
```

4. **測試 MCP 工具**

在 OpenCode 中輸入：
```
列出知識庫中所有已索引的文件
```

### MCP 可用工具

| 工具 | 說明 |
|------|------|
| `rag_search` | 語意搜尋 |
| `rag_ask` | 問答生成 |
| `rag_upload` | 上傳 PDF |
| `rag_upload_batch` | 批次上傳 |
| `rag_upload_directory` | 上傳整個目錄 |
| `rag_list_documents` | 列出文件 |
| `rag_get_stats` | 知識庫統計 |
| `rag_delete_document` | 刪除文件 |
| `rag_get_status` | 查詢處理狀態 |

---

## 📄 PDF 分割工具

處理大型 PDF 避免 timeout：

```bash
# 安裝依賴
pip install pypdf

# 分割 PDF（每份 5 頁）
python split_pdf.py data/raw/your_file.pdf --pages 5
```

---

## 🔌 API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/upload` | POST | 上傳 PDF |
| `/chat` | POST | 對話（非串流） |
| `/chat/stream` | POST | 對話（串流） |
| `/search` | POST | 語意搜尋 |
| `/ask` | POST | 問答生成 |
| `/documents` | GET | 列出文件 |
| `/stats` | GET | 知識庫統計 |
| `/status/{file}` | GET | 處理狀態 |
| `/health` | GET | 健康檢查 |

API 文件：http://localhost:8001/docs

---

## 🛠️ 技術堆疊

| 領域 | 技術 |
|------|------|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | FastAPI, Python 3.10+ |
| Vector DB | Qdrant (Docker) |
| AI Model | GPT-4o, text-embedding-3-small |
| PDF Parser | IBM Docling |
| Agent | OpenCode |
| Protocol | MCP (FastMCP) |

---

## 📋 開發進度

- [x] PDF 上傳與解析
- [x] 向量索引 (Qdrant)
- [x] 語意搜尋 + GPT-4o 生成
- [x] React 前端介面
- [x] 來源引用 + 頁碼跳轉
- [x] MCP Server 整合
- [x] OpenCode Agentic RAG
- [x] 多 PDF 批次索引
- [x] 串流對話 + 推理顯示
- [ ] PDF 關鍵字高亮
- [ ] Deep Research 報告生成

---

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

---

## 📜 授權

MIT License