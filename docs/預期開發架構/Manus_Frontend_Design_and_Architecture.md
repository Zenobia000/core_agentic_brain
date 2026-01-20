# Manus 統一前端架構與設計規格書 v3.0

## 1. 核心設計哲學

### 1.1 願景：駭客的數位指揮中心

Manus 的前端介面，無論是 Web 還是 Terminal，都旨在成為一個高效、專注、鍵盤優先的數位指揮中心。它借鑒了經典的「駭客綠」終端美學，將其與現代化的 UI 架構相結合，為開發者和進階使用者提供沉浸式、無干擾的互動體驗。

我們的設計理念是：**像使用 Terminal 一樣操作 Web，像閱讀故事一樣理解任務。**

### 1.2 三大核心原則

1.  **主線清晰 (Clarity of Intent)**
    *   **任務導向**: 當前執行的核心任務 (Task) 及其階段 (Phase) 永遠是視覺焦點，固定在畫面上方，使用者絕不會迷失方向。
    *   **資訊分層**: 嚴格區分人機對話、系統思考、工具調用和原始日誌，讓使用者可以按需深入，避免資訊過載。

2.  **雜訊可控 (Controllable Noise)**
    *   **預設極簡**: 機器思考的過程 (Thinking) 和工具執行的細節 (Tools) 預設是收合的，只展示摘要。使用者只有在關心時才需要展開，保持介面乾淨。
    *   **模式切換**: 提供 `Minimal`, `Standard`, `Hacker` 三種模式，使用者可以根據當前情境和螢幕空間，自由選擇資訊的詳細程度。

3.  **鍵盤優先 (Keyboard-First)**
    *   **全局快捷鍵**: 所有核心操作，如面板切換、命令調用、任務中斷，都有對應的快捷鍵。滑鼠是輔助，鍵盤是主宰。
    *   **命令面板**: `Ctrl+P` 呼叫的命令面板是所有功能的統一入口，實現快速的功能搜尋與執行。

## 2. 統一 UI/UX 架構

### 2.1 四層資訊架構

所有前端介面都遵循相同的資訊渲染層級，確保一致的認知模型。

| 層級 | 內容 | 目的 | 預設可見性 |
| :--- | :--- | :--- | :--- |
| **L1: 人本對話 (Human Text)** | 使用者與 Manus 之間的主要對話 | 最重要的頂層資訊，清晰易讀 | 永遠可見 |
| **L2: 計劃摘要 (Plan/Summary)** | 任務階段、進度、工具調用摘要 | 快速掌握當前狀態 | `Standard` 模式下可見 |
| **L3: 事件記錄 (Tool Events)** | 工具的呼叫、參數、輸出、耗時 | 除錯與細節追蹤 | `Hacker` 模式下可見 |
| **L4: 原始日誌 (Raw Logs)** | 最詳細的內部日誌與追蹤資訊 | 深度除錯 | 預設隱藏，按需展開 |

### 2.2 核心佈局 (The Grid)

Web 和 Terminal 共享相同的佈局邏輯，僅在渲染技術上有所不同。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Task Header] 當前任務、階段、等待狀態                                      │ ← 固定頂部
├─────────────────────────────────────────────────────┬───────────────────────┤
│ [Main Panel]                                        │ [Sidebar]             │
│                                                     │                       │
│ ┌─[Conversation]────────────────────────────────┐   │  [Context]            │
│ │ L1: 人與 Manus 的主要對話                       │   │  [Connections]        │
│ └───────────────────────────────────────────────┘   │  [TODO]               │
│ ┌─[Thinking] (Collapsible)──────────────────────┐   │  [Memory]             │
│ │ ▼ Thinking                                    │   │                       │
│ │   ✨ Planning next steps                        │   │                       │
│ │   🛠️ Selecting 1 tool                           │   │                       │
│ │   🧰 Preparing tool: python_execute            │   │                       │
│ └───────────────────────────────────────────────┘   │                       │
│ ┌─[Tools] (Collapsible)─────────────────────────┐   │                       │
│ │ ▶ Tools: python_exec (exit 0)                 │   │                       │
│ └───────────────────────────────────────────────┘   │                       │
│                                                     │                       │
├─────────────────────────────────────────────────────┴───────────────────────┤
│ [Input Area] 使用者輸入、快捷鍵提示                                         │ ← 固定底部
└─────────────────────────────────────────────────────────────────────────────┘
```

*   **響應式設計**: 在窄螢幕或 `Minimal` 模式下，`Sidebar` 會自動隱藏或轉為浮動面板，確保 `Main Panel` 的可視空間。

### 2.3 互動模式 (Interaction Modes)

| 模式 | 核心特點 | 適用場景 |
| :--- | :--- | :--- |
| **Minimal** | 純文字流，無邊框，僅顯示 L1 對話和簡短狀態 | SSH 連線、小螢幕、專注於對話 |
| **Standard** | 包含 Task Header 和 L2 的摺疊式面板 | 日常使用的預設模式，平衡資訊與簡潔 |
| **Hacker** | 全功能多面板，包含 Sidebar，顯示 L3 事件 | 複雜任務、開發除錯、需要完整上下文 |

### 2.4 焦點管理

使用統一的視覺語言來標示當前活躍的面板。

*   **活躍面板 (Active Pane)**: 邊框高亮 (`bright`)，標題前綴為實心圓 `●`。
*   **非活躍面板 (Inactive Pane)**: 邊框變暗 (`dim`)，標題前綴為空心圓 `○`。

## 3. 視覺設計系統 (Matrix Theme)

統一的視覺語言是品牌識別和沉浸式體驗的關鍵。

### 3.1 核心色彩

```css
:root {
  --bg-primary: #0a0a0a;        /* 主背景 (深黑) */
  --text-primary: #00ff00;      /* 主要文字 (駭客綠) */
  --text-accent: #00ffff;       /* 強調色 (青色) */
  --text-dim: #006600;          /* 暗色文字 */
  --border-active: #00ff00;     /* 活躍面板邊框 */
  --border-inactive: #003300;   /* 非活躍面板邊框 */
  --status-success: #00ff00;    /* 成功狀態 */
  --status-warning: #ffcc00;    /* 警告狀態 */
  --status-error: #ff3333;      /* 錯誤狀態 */
}
```

### 3.2 字型規範

*   **字型**: `JetBrains Mono`, `Fira Code`, `Consolas`, `monospace`
*   **效果**: 輕微的 `letter-spacing` 和 `scanline` 動畫，模擬老式 CRT 顯示器效果，增強復古未來感。


## 4. 組件規格

### 4.1 Task Header

*   **職責**: 提供全局、持久的任務上下文。
*   **格式**: `[Task] {任務名稱} │ Phase {n/m} {階段名} │ {等待狀態}`
*   **狀態指示器 (`Waiting For`)**: `Ready`, `Thinking...`, `Tool: {tool_name} ⏳`, `Waiting for input...`, `Error ❌`, `✓ Completed`

### 4.2 主面板 (Main Panels) 與思維鏈呈現

*   **Conversation**: 核心對話區，不變。

*   **Thinking Panel (思維鏈面板)**:
    *   **職責**: 實時、高層次地展示 Manus 的思維鏈節點 (Chain of Thought)，讓使用者了解其「正在想什麼」和「打算做什麼」，而無需關心內部細節。
    *   **摺疊行為**:
        *   **收合 (預設)**: 顯示 `▶ Thinking` 以及當前最新一個思維節點的摘要，例如：`▶ Thinking: 🛠️ Selecting tools`。
        *   **展開**: 顯示 `▼ Thinking` 以及一個滾動的思維節點列表。
    *   **節點格式**: 每個節點都是一行，由 `圖標` + `摘要標題` 組成。
    *   **從後端日誌到 UI 的映射範例**:
        *   `INFO ... ✨ Manus's thoughts: ...`  ->  `✨ Planning next steps`
        *   `INFO ... 🛠️ Manus selected 1 tools to use` -> `🛠️ Selecting 1 tool`
        *   `INFO ... 🧰 Tools being prepared: ['python_execute']` -> `🧰 Preparing tool: python_execute`

*   **Tools Panel**:
    *   **職責**: 展示工具執行的詳細記錄，包括 `stdout` 和 `exit code`。
    *   **行為**: 預設收合，點擊可展開查看 L3/L4 層級的詳細日誌。

### 4.3 側邊欄 (Sidebar)

順序固定的四個區塊，提供即時的輔助資訊。

1.  **CONTEXT**: `Tokens`, `Model`, `Cost`, `Latency` 等與 LLM 相關的即時數據。
2.  **CONNECTIONS**: `LLM`, `MCP`, `LSP`, `Workspace` 等後端服務的連線狀態。
3.  **TODO**: 當前任務的步驟清單，支援互動（跳轉、重跑、標記完成）。
4.  **MEMORY**: `Session ID`, `Parent Task` 等記憶/上下文關聯資訊。

### 4.4 輸入區 (Input Area)

*   **組成**: `Prompt符號 (manus>)` + `文字輸入框` + `快捷鍵提示`。
*   **功能**: 支援歷史命令（上下箭頭）、自動補全和 `Ctrl+P` 命令面板。

### 4.5 回饋與通知

統一的、可預測的狀態回饋格式。

*   **成功 (Success)**: `✓ Done: {action} ({details})`
    *   *範例*: `✓ Done: file saved to /app/user.py`
*   **警告 (Warning)**: `⚠ Warning: {issue}; {suggestion}`
    *   *範例*: `⚠ Warning: deprecated API used; consider upgrading to v2`
*   **失敗 (Error)**: `✗ Failed: {reason} → {next_action}`
    *   *範例*: `✗ Failed: connection timeout → check API key in /config`

## 5. 互動與快捷鍵

### 5.1 命令面板 (Command Palette)

*   **觸發**: `Ctrl+P`
*   **功能**: 模糊搜尋並執行所有可用命令，如 `/mode`, `/theme`, `/export`, `/help`。

### 5.2 全局快捷鍵

| 按鍵 | 功能 |
| :--- | :--- |
| `Ctrl+K` | 在 `Conversation`, `Thinking`, `Tools`, `Sidebar` 面板間切換焦點 |
| `Ctrl+J` | 摺疊/展開當前焦點所在的面板 |
| `Ctrl+G` | 跳轉到最近的錯誤訊息 |
| `Ctrl+C` | 中斷當前正在執行的操作 |
| `Ctrl+/` | 顯示/隱藏 Sidebar |

## 6. 技術架構與實作

（此部分主要基於 Web UI 的實作，作為參考實現）

### 6.1 前端技術棧

*   **核心**: Vanilla JavaScript (ES6+ Classes)，無框架依賴，確保輕量與高效。
*   **佈局**: CSS Grid + Flexbox。
*   **樣式**: CSS Variables (自訂主題) + class-based 狀態管理。
*   **渲染**: DOM 操作，針對高效能的 Log 輸出進行優化（虛擬滾動）。

### 6.2 即時通訊

*   **主要通道**: **WebSocket**，用於雙向、低延遲的指令和事件傳輸（如狀態更新、工具調用）。
*   **輔助通道**: **Server-Sent Events (SSE)**，用於從後端到前端的單向文本流（如 LLM 的 token stream），實現打字機效果。

### 6.3 後端 API 協定 (以 FastAPI 為例)

*   **`/api/chat` (POST)**: 接收使用者查詢，以 SSE 串流形式回傳 LLM 回應。
*   **`/ws` (WebSocket)**: 處理所有非 LLM token 的即時事件，如 `task_update`, `tool_event`, `context_update`。
*   **`/api/settings` (GET)**: 獲取使用者個人化設定（主題、模式等）。

## 7. 部署

*   **容器化**: 使用 **Docker** 封裝前端靜態資源和後端 FastAPI 應用。
*   **反向代理**: 使用 **Nginx** 處理靜態檔案服務、API 請求和 WebSocket 連線的代理，並可輕鬆配置 HTTPS。

## 8. 開發路線圖 (建議)

1.  **Phase 1: 核心 MVP**
    *   實現 Task Header、Conversation 和 Input 區。
    *   建立基本的 WebSocket 連線和回饋模板。
2.  **Phase 2: 標準模式**
    *   開發摺疊式的 Thinking 和 Tools 面板。
    *   實現 `Standard` 模式的佈局和焦點管理。
3.  **Phase 3: 駭客模式**
    *   建構完整的 Sidebar 四大區塊。
    *   開發 `Ctrl+P` 命令面板和 TODO 互動功能。
4.  **Phase 4: 打磨優化**
    *   完善所有快捷鍵和主題切換功能。
    *   進行效能優化（虛擬滾動、減少重繪）和無障礙支援。
