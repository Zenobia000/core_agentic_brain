# OpenCode Platform - 專案狀態總覽

> 更新日期：2025-01-25
> 用途：供後續對話快速了解專案現況
> 版本：整合版 (含 rag-project 功能)

---

## 📦 專案資訊

| 項目 | 說明 |
|------|------|
| 專案名稱 | OpenCode Platform |
| 基礎框架 | 基於 rag-project 重構 + 整合 |
| 部署環境 | Windows 11 + Python 3.13 |
| 向量資料庫 | Qdrant (localhost:6333) |
| LLM | OpenAI API |

---

## ✅ 整合功能清單

### 🆕 從 rag-project 整合的功能

| 功能 | 狀態 | 說明 |
|------|------|------|
| Agent SSE 串流 | ✅ | 顯示思考過程、工具呼叫 |
| 深度研究 | ✅ | 自動子問題生成、多輪搜尋、報告整合 |
| 篩選搜尋 | ✅ | 限定特定文件搜尋 |
| Qdrant 管理 | ✅ | Collection 管理、瀏覽、刪除 |
| 處理狀態追蹤 | ✅ | 背景處理、狀態查詢 |

### API 端點總覽

| 端點 | 方法 | 功能 |
|------|------|------|
| `/chat` | POST | 同步對話 |
| `/chat/stream` | POST | SSE 串流對話 |
| `/search` | POST | 語意搜尋 |
| `/search/filtered` | POST | 篩選搜尋 |
| `/ask` | POST | 問答生成 |
| `/documents` | GET | 文件列表 |
| `/documents/{name}` | DELETE | 刪除文件 |
| `/upload` | POST | 上傳 PDF |
| `/status/{file}` | GET | 處理狀態 |
| `/stats` | GET | 統計資訊 |
| `/research/start` | POST | 啟動深度研究 |
| `/research/{id}` | GET | 研究狀態 |
| `/research` | GET | 研究列表 |
| `/qdrant/collections` | GET | Collection 列表 |
| `/qdrant/collection/{name}` | GET | Collection 詳情 |
| `/qdrant/collection/{name}/points` | GET | 瀏覽 Points |
| `/qdrant/collection/{name}` | DELETE | 刪除 Collection |
| `/health` | GET | 健康檢查 |

---

## 🚀 啟動指南

### 1. 啟動後端 API

```powershell
cd C:\Users\student\Desktop\opencode-platform
python -m cli.main api
```

### 2. 啟動前端

```powershell
cd C:\Users\student\Desktop\opencode-platform\frontend
npm install  # 首次
npm run dev
```

### 3. 存取服務

| 服務 | 網址 |
|------|------|
| 前端 | http://localhost:5173 |
| API | http://localhost:8000 |
| API 文件 | http://localhost:8000/docs |
| Qdrant | http://localhost:6333/dashboard |

---

## 📁 新增檔案

```
api/routes/
├── research.py           # 深度研究 API
└── qdrant.py             # Qdrant 管理 API

services/research/
├── __init__.py
└── service.py            # 深度研究服務

frontend/src/components/
└── ResearchPanel.jsx     # 深度研究面板
```

---

## 🔧 環境配置

### .env 檔案

```env
OPENAI_API_KEY=sk-proj-你的金鑰
QDRANT_HOST=localhost
QDRANT_PORT=6333
LOG_LEVEL=INFO
```

---

## 📋 CLI 命令

| 命令 | 功能 |
|------|------|
| `python -m cli.main api` | 啟動 API 伺服器 |
| `python -m cli.main chat <message>` | 對話 |
| `python -m cli.main search <query>` | 搜尋 |
| `python -m cli.main upload` | 上傳 PDF |
| `python -m cli.main docs` | 列出文件 |
| `python -m cli.main stats` | 顯示統計 |
