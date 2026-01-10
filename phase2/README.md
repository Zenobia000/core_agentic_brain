# 🚀 RAG Phase 2 安裝指南

## 📁 檔案結構

```
phase2/
├── backend/
│   └── routes_phase2.py     # 後端 API 擴展
├── frontend/
│   ├── App.jsx              # 整合後的主組件
│   └── components/
│       ├── DocumentList.jsx  # 多 PDF 選擇器
│       ├── PDFViewer.jsx     # PDF 預覽 + 高亮
│       ├── ChatPanel.jsx     # 對話面板
│       ├── ResearchPanel.jsx # Deep Research
│       └── QdrantAdmin.jsx   # Qdrant 管理
└── README.md                 # 本說明文件
```

---

## 🔧 安裝步驟

### 1️⃣ 後端設定

**複製 API 路由：**

```bash
# 複製 routes_phase2.py 到你的專案
cp phase2/backend/routes_phase2.py C:\Users\USER\Desktop\rag-project\src\
```

**修改 `src/main.py`：**

```python
# 在 imports 區塊加入
from routes_phase2 import router as phase2_router

# 在 app 定義後加入
app.include_router(phase2_router)
```

完整範例：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Phase 2 路由
from routes_phase2 import router as phase2_router

app = FastAPI(title="RAG API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 靜態檔案
app.mount("/files", StaticFiles(directory="data/raw"), name="files")

# Phase 2 路由
app.include_router(phase2_router)

# ... 你原有的路由 ...
```

---

### 2️⃣ 前端設定

**安裝新依賴：**

```bash
cd C:\Users\USER\Desktop\rag-project\frontend
npm install react-markdown react-pdf
```

**複製組件：**

```bash
# 複製所有組件
cp phase2/frontend/components/*.jsx frontend/src/components/

# 替換 App.jsx
cp phase2/frontend/App.jsx frontend/src/App.jsx
```

**確認 package.json 有以下依賴：**

```json
{
  "dependencies": {
    "react": "^18.x",
    "react-dom": "^18.x",
    "react-pdf": "^7.x",
    "react-markdown": "^9.x"
  }
}
```

---

## 🚀 啟動服務

### 1. 啟動 Qdrant

```bash
docker start qdrant-rag
```

### 2. 啟動後端

```bash
cd C:\Users\USER\Desktop\rag-project
python -m src.main
# 運行在 http://localhost:8001
```

### 3. 啟動前端

```bash
cd frontend
npm run dev
# 運行在 http://localhost:3000
```

---

## ✨ 新功能使用

### 📂 多 PDF 選擇器
- 左側顯示所有已上傳的 PDF
- 勾選要搜尋的文件
- 支援全選/取消
- 可刪除文件（同時刪除向量）

### 🔍 關鍵字高亮
- 點擊來源卡片後，PDF 會自動跳轉到對應頁面
- 搜尋關鍵字會以黃色高亮顯示

### 🔬 Deep Research
1. 切換到「研究」Tab
2. 輸入研究主題
3. 等待 AI 自動分析並生成報告
4. 可下載 Markdown 或 HTML 格式

### ⚙️ Qdrant 管理
- 查看所有 Collections
- 瀏覽向量資料
- 查看文件向量分布
- 刪除 Collection

---

## 🔌 API 端點列表

### 文件管理
| Method | Endpoint | 說明 |
|--------|----------|------|
| GET | `/documents` | 列出所有文件 |
| DELETE | `/documents/{filename}` | 刪除文件及向量 |
| POST | `/search/filtered` | 篩選搜尋 |

### Deep Research
| Method | Endpoint | 說明 |
|--------|----------|------|
| POST | `/research/start` | 啟動研究 |
| GET | `/research/{task_id}` | 查詢進度 |
| GET | `/research` | 列出所有任務 |

### Qdrant 管理
| Method | Endpoint | 說明 |
|--------|----------|------|
| GET | `/qdrant/collections` | 列出 Collections |
| GET | `/qdrant/collection/{name}` | Collection 詳情 |
| GET | `/qdrant/collection/{name}/points` | 瀏覽 Points |
| DELETE | `/qdrant/collection/{name}` | 刪除 Collection |

---

## ⚠️ 注意事項

1. **確保後端 /ask 端點存在**
   - ChatPanel 會呼叫 `/ask` 來生成回答
   - 如果你原本的端點名稱不同，請修改 `ChatPanel.jsx`

2. **CORS 設定**
   - 確保後端已設定 CORS 允許前端訪問

3. **PDF.js Worker**
   - PDFViewer 使用 CDN 載入 worker
   - 需要網路連線

4. **Deep Research 耗時**
   - 複雜主題可能需要 1-2 分鐘
   - 取決於 OpenAI API 回應速度

---

## 🐛 常見問題

### Q: 文件列表顯示「無法載入」
A: 檢查後端是否正確掛載了 Phase 2 路由

### Q: PDF 無法預覽
A: 確認 `/files/` 靜態路由正確設定

### Q: Deep Research 失敗
A: 檢查 OpenAI API Key 是否正確設定在 `.env`

### Q: 關鍵字高亮不生效
A: 確保 react-pdf 版本 >= 7.0，且文字層有正確渲染

---

## 📝 下一步

Phase 3 可以考慮：
- 聊天記錄持久化
- 多使用者支援
- 更多文件格式支援 (Word, Excel)
- 串接其他 LLM (Claude, Gemini)

---

有問題隨時問我！🎯
