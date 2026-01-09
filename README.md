# RAG 知識庫系統 (RAG Knowledge Base)

本專案為基於 LLM + NQ1D (Normalized Question) 架構的 RAG 系統開發原型。

## 📁 專案結構
- `src/ingestion/`: 離線資料處理 (Blue Line) - 負責解析文件與建立索引。
- `src/retrieval/`: 線上檢索推理 (Green Line) - 負責回答使用者問題。
- `data/`: 存放文件資料。

## 🚀 快速開始 (Quick Start)

### 1. 環境準備
請確保已安裝 Python 3.10+ 與 Docker。

```bash
# 安裝相依套件
pip install -r requirements.txt