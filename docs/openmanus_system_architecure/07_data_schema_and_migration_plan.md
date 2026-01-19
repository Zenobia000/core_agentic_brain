# 數據模型與遷移計畫 (Data Schema & Migration Plan) - OpenManus

---

**文件版本 (Document Version):** `v1.0`

**最後更新 (Last Updated):** `2025-10-14`

**主要作者 (Lead Author):** `OpenManus Team`

**審核者 (Reviewers):** `Community Contributors`

**狀態 (Status):** `已批准 (Approved)`

---

## 目錄 (Table of Contents)

1.  [概述 (Overview)](#1-概述-overview)
2.  [現有數據模型 (Current Data Models)](#2-現有數據模型-current-data-models)
3.  [配置 Schema (Configuration Schema)](#3-配置-schema-configuration-schema)
4.  [持久化遷移計畫 (Future Persistence Migration Plan)](#4-持久化遷移計畫-future-persistence-migration-plan)

---

## 1. 概述 (Overview)

### 1.1 文件目的 (Document Purpose)
*   記錄 OpenManus 當前的內存數據結構與配置格式。
*   為未來引入資料庫持久化（如：對話記錄保存）建立遷移路線圖。

---

## 2. 現有數據模型 (Current Data Models)

OpenManus 目前主要使用 Pydantic 模型管理內存中的對話狀態。

### 2.1 對話記憶體 (Memory & Message)
定義於 `app/schema.py`:
*   **Message**: 
    *   `role`: `system`, `user`, `assistant`, `tool`
    *   `content`: 文本內容
    *   `tool_calls`: LLM 生成的工具調用指令
    *   `tool_call_id`: 關聯工具執行結果的 ID
*   **Memory**:
    *   `messages`: `List[Message]`
    *   `max_messages`: 限制上下文窗口長度（預設 100）

### 2.2 沙箱狀態 (Sandbox State)
*   **SandboxSettings**: 定義於 `app/config.py`，管理 Docker 映像檔、內存限制、超時等。

---

## 3. 配置 Schema (Configuration Schema)

### 3.1 `config.toml` 格式
```toml
[llm]
model = "gpt-4o"
base_url = "https://api.openai.com/v1"
api_key = "sk-..."

[sandbox]
use_sandbox = true
image = "python:3.12-slim"

[browser]
headless = false
```

### 3.2 `mcp.json` 格式
```json
{
  "mcpServers": {
    "weather": {
      "type": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

---

## 4. 持久化遷移計畫 (Future Persistence Migration Plan)

若未來需要支持對話歷史持久化，建議採取以下步驟：

### 4.1 階段一：引入 SQLAlchemy 與 SQLite
*   **目標**: 實現本地對話紀錄自動保存。
*   **Schema 變更**:
    *   `sessions` 表: 存儲對話 ID、開始時間、標題。
    *   `messages` 表: 存儲對話內容、Role、與 `session_id` 關聯。

### 4.2 階段二：數據導出/導入
*   **功能**: 支持將 `Memory` 導出為 JSON 並重新載入。
*   **腳本**: 實作 `Memory.save_to_file()` 與 `Memory.load_from_file()`。

### 4.3 階段三：雲端同步 (PostgreSQL)
*   **目標**: 多端同步 Agent 狀態。
*   **方案**: 透過環境變數切換 SQLite 為 PostgreSQL。

---

## 5. 數據備份與安全

*   **Workspace**: 運行期間產生的所有檔案均存儲於 `workspace/`。
*   **清理**: Agent 結束時應清理 Sandbox 內的臨時文件。
*   **加密**: `config.toml` 內的 API Key 應避免提交至 Git，建議使用 `.env` 或系統環境變數。
