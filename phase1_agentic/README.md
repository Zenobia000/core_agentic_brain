# 🚀 Phase 1: Agentic 推理顯示 - 安裝說明

## 📁 檔案清單

### 後端 (Python)
| 檔案 | 放置位置 | 說明 |
|------|----------|------|
| `agent.py` | `src/retrieval/agent.py` | 🆕 Agent 邏輯 |
| `main.py` | `src/main.py` | 更新的 API（含串流） |

### 前端 (React)
| 檔案 | 放置位置 | 說明 |
|------|----------|------|
| `App.jsx` | `frontend/src/App.jsx` | 更新的主組件 |
| `ChatInterface.jsx` | `frontend/src/components/ChatInterface.jsx` | 更新的對話介面 |
| `ThinkingBlock.jsx` | `frontend/src/components/ThinkingBlock.jsx` | 🆕 推理過程組件 |
| `ToolCallBlock.jsx` | `frontend/src/components/ToolCallBlock.jsx` | 🆕 工具呼叫組件 |

---

## 📋 安裝步驟

### 1. 備份現有檔案
```bash
cd C:\Users\student\Desktop\PortableGit\rag-project

# 備份後端
copy src\main.py src\main.py.bak

# 備份前端
copy frontend\src\App.jsx frontend\src\App.jsx.bak
copy frontend\src\components\ChatInterface.jsx frontend\src\components\ChatInterface.jsx.bak
```

### 2. 複製後端檔案
```bash
# 建立 agent.py
copy agent.py src\retrieval\agent.py

# 更新 main.py
copy main.py src\main.py
```

### 3. 複製前端檔案
```bash
# 更新主組件
copy App.jsx frontend\src\App.jsx

# 更新對話介面
copy ChatInterface.jsx frontend\src\components\ChatInterface.jsx

# 新增推理組件
copy ThinkingBlock.jsx frontend\src\components\ThinkingBlock.jsx
copy ToolCallBlock.jsx frontend\src\components\ToolCallBlock.jsx
```

### 4. 重啟服務
```bash
# Terminal 1: 重啟後端
cd C:\Users\student\Desktop\PortableGit\rag-project
python -m src.main

# Terminal 2: 重啟前端
cd frontend
npm run dev
```

---

## 🧪 測試

### 1. 檢查後端 API
打開 `http://localhost:8001/health`，確認看到：
```json
{
  "status": "healthy",
  "retriever": true,
  "generator": true,
  "agent": true
}
```

### 2. 打開前端
瀏覽器訪問 `http://localhost:3000`

### 3. 測試 Agentic 對話
- 上傳 PDF 或使用已有的知識庫
- 輸入問題，觀察：
  - 💜 紫色推理過程 (Thinking)
  - 🔵 藍色工具呼叫 (Tool Call)
  - ✅ 綠色結果提示
  - 📝 最終回答 + 來源引用

---

## 🎯 新功能一覽

| 功能 | 說明 |
|------|------|
| 串流回答 | 即時顯示 AI 推理過程 |
| Thinking 顯示 | 紫色區塊顯示 Agent 思考 |
| Tool Call 顯示 | 顯示搜尋關鍵字和結果 |
| 知識庫統計 | Header 顯示文件數和區塊數 |
| 多步推理 | Agent 自動拆解複雜問題 |

---

## ⚠️ 常見問題

### Q: 後端啟動報錯 `ModuleNotFoundError: No module named 'src.retrieval.agent'`
A: 確認 `agent.py` 放在 `src/retrieval/` 目錄下

### Q: 前端報錯 `ThinkingBlock is not defined`
A: 確認 `ThinkingBlock.jsx` 和 `ToolCallBlock.jsx` 放在 `frontend/src/components/` 目錄下

### Q: 串流沒有反應
A: 檢查後端 log，確認 `/chat/stream` 端點有收到請求

---

## 🔜 Phase 2 預告

下一步將實作：
- PDF 關鍵字高亮
- 使用 react-pdf 替換 embed
- 搜尋詞高亮顯示
