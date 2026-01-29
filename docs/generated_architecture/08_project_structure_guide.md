# 專案結構指南 (Project Structure Guide) - Core Agentic Brain

---

**文件版本 (Document Version):** `v2.0`
**最後更新 (Last Updated):** `2026-01-30`
**主要作者 (Lead Author):** `Gemini AI Assistant`
**狀態 (Status):** `活躍 (Active)`

---

## 1. 指南目的 (Purpose of This Guide)

*   為 `Core Agentic Brain` 提供一個標準化、可擴展且易於理解的目錄和文件結構。
*   確保團隊成員能夠快速定位代碼、配置文件和文檔，降低新成員的上手成本。
*   促進代碼的模塊化和關注點分離，提高可維護性。

## 2. 核心設計原則 (Core Design Principles)

*   **核心化調度 (Centralized Dispatch):** 以 `core/kernel.py` 作為系統的中心，所有操作都視為由 Kernel 調度的系統呼叫，以實現關注點分離。
*   **按功能組織 (Organize by Feature):** 相關的功能（例如，不同的 Agent 類型、工具）被組織在專門的目錄中 (`agents/`, `tools/`)。
*   **配置外部化 (Externalized Configuration):** 應用程式的配置 (`config.yaml`) 與代碼分離，並可通過環境變數覆寫，便於在不同環境中部署。
*   **根目錄簡潔 (Clean Root Directory):** 根目錄主要包含專案級別的文件，所有 Python 原始碼都放在對應的功能目錄下。

## 3. 頂層目錄結構 (Top-Level Directory Structure)

```plaintext
core_agentic_brain/
├── agents/               # 定義不同角色的 Agent (Planner, Executor)
├── cli/                  # (未來擴充) 命令列介面相關代碼
├── config/               # 預設的配置範本
├── core/                 # 系統核心，包含 Kernel、LLM 介面、工具管理器等
├── docs/                 # 專案文檔
├── prompts/              # Agent 所使用的 YAML 格式提示詞
├── router/               # 任務分析與路由策略
├── scripts/              # 開發與維運腳本
├── tests/                # 所有測試代碼
├── tools/                # Agent 可使用的工具 (內建與自訂)
├── web/                  # (未來擴充) Web 服務相關代碼
├── workspace/            # 執行期間產生的檔案、日誌、快取
├── main.py               # 應用程式主入口
├── config.yaml           # 主配置文件
├── requirements.txt      # Python 依賴
└── README.md             # 專案介紹
```

## 4. 目錄詳解 (Directory Breakdown)

### 4.1 `core/` - 系統核心
*   專案的心臟，所有核心邏輯都應放在這裡。遵循 Clean Architecture 的設計思想。
```plaintext
core/
├── kernel.py             # Kernel: 中央調度器，負責載入組件與協調流程
├── orchestration.py      # MultiAgentOrchestrator: 多代理協調，支援 ReAct 等策略
├── workspace.py          # WorkspaceManager: 工作區管理，隔離執行環境
├── communication.py      # CommunicationBus: 統一通訊匯流排
├── llm.py                # LLMProvider: 統一的 LLM 介面，支援多種模型
├── logger.py             # 基於 loguru 的日誌系統，支援 run_id 追蹤
├── config.py             # 負責載入與合併 config.yaml 和環境變數
├── prompt_loader.py      # 從 prompts/ 目錄載入 YAML 提示詞的工具
├── types.py              # 定義整個專案共用的核心資料結構
└── utils.py              # 通用工具函數
```

### 4.2 `agents/` - 智慧代理
*   定義具有不同職責的 Agent。每個 Agent 都是一個獨立的專家。
```plaintext
agents/
├── base.py               # 所有 Agent 的抽象基礎類別，支援 kernel 注入
├── planner.py            # PlannerAgent: 負責將複雜任務分解為步驟
├── executor.py           # ExecutorAgent: 負責執行任務，支援 ReAct 循環
└── reviewer.py           # ReviewerAgent: 負責審核其他 Agent 的產出
```

**ExecutorAgent ReAct 特性:**
- 最多 10 次迭代的 Think-Act-Observe 循環
- Token 預算管理 (8000 tokens)
- 重複偵測 (防止無限循環)
- 自動生成最終摘要

### 4.3 `tools/` - 功能工具
*   提供給 Agent 使用的具體能力，實現與外部世界的互動。
```plaintext
tools/
├── base.py               # BaseTool: 異步工具基礎類別
├── pure_base.py          # PureTool: 同步/異步混合基礎類別
├── builtin/              # 內建工具
│   ├── python.py         # Python 執行器 (workspace-aware)
│   ├── files.py          # 檔案操作 (workspace-aware)
│   ├── websearch.py      # Web 搜尋 (多引擎降級)
│   └── terminate.py      # 執行終止信號
└── custom/               # 針對特定專案需求的自訂工具
```

**工具特性:**
- Workspace-aware: 工具在 `workspace/run_xxx/` 目錄中操作
- Async-hybrid: `PureTool.handle()` 自動處理同步/異步執行
- Multi-engine fallback: websearch 支援 Serper → Tavily → DuckDuckGo

### 4.4 `prompts/` - 提示詞庫
*   存放給 LLM 的指令。將 Prompt 從代碼中分離，便於管理和優化。
*   以 YAML 格式儲存，例如 `planner.yaml`, `executor.yaml`。

### 4.5 `router/` - 任務路由器
*   在 Kernel 接收到任務後，決定該如何處理。
```plaintext
router/
├── analyzer.py           # TaskAnalyzer: 關鍵詞分析器 (備用)
├── llm_analyzer.py       # LLMTaskAnalyzer: LLM 智能分析器 (主要)
├── executor.py           # RoutingExecutor: 路由執行器
└── strategies.py         # 路由策略定義
```

**LLMTaskAnalyzer 功能:**
- 使用 LLM 分析任務複雜度 (simple/moderate/complex)
- 智能選擇執行策略 (direct/sequential/orchestrated/react)
- 推薦參與的代理列表

### 4.6 `tests/` - 測試代碼
*   測試代碼與 `src` 的結構應大致對應。
```plaintext
tests/
├── conftest.py           # Pytest 全局 fixtures
├── unit/                 # 單元測試，針對單一模組
├── integration/          # 整合測試，測試多個模組的協作
└── performance/          # (未來擴充) 效能測試
```

## 5. 文件命名約定 (File Naming Conventions)

*   **Python 模組:** `snake_case.py` (e.g., `prompt_loader.py`)。
*   **測試文件:** 以 `test_` 開頭 (e.g., `test_tools.py`)。
*   **Markdown 文件:** `kebab-case.md` 或 `CAPITALIZED_SNAKE_CASE.md`。

## 6. 演進原則 (Evolution Principles)

*   本結構是一個起點，應根據專案的發展進行調整。
*   任何對頂層目錄結構的重大變更，都應通過團隊討論或更新本文檔來記錄。
*   保持結構的清晰和一致性比嚴格遵守某個特定模式更重要。
