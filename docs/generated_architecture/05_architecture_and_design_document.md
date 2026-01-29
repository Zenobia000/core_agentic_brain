# 整合性架構與設計文件 (Unified Architecture & Design Document) - Core Agentic Brain

---

**文件版本 (Document Version):** `v2.1`
**最後更新 (Last Updated):** `2026-01-30`
**主要作者 (Lead Author):** `Gemini AI Assistant`
**審核者 (Reviewers):** `Core Development Team`
**狀態 (Status):** `草稿 (Draft)`

---

## 目錄 (Table of Contents)

- [1. 需求摘要 (Requirements Summary)](#1-需求摘要-requirements-summary)
- [2. 高層次架構設計 (High-Level Architectural Design)](#2-高層次架構設計-high-level-architectural-design)
- [3. 技術選型詳述 (Technology Stack Details)](#3-技術選型詳述-technology-stack-details)
- [4. 數據架構 (Data Architecture)](#4-數據架構-data-architecture)
- [5. 跨領域考量 (Cross-Cutting Concerns)](#5-跨領域考量-cross-cutting-concerns)

---

## 1. 需求摘要 (Requirements Summary)

### 1.1 功能性需求摘要 (Functional Requirements Summary)
*   **FR-1:** 系統必須能夠理解並回應自然語言形式的任務或問題。
*   **FR-2:** 系統必須能夠將複雜任務分解為一系列可執行的步驟 (Planning)。
*   **FR-3:** 系統必須能夠執行具體的任務，並在需要時呼叫外部工具 (Execution)。
*   **FR-4:** 系統支援可插拔的工具集，例如執行 Python 程式碼、讀寫檔案。
*   **FR-5:** 系統支援透過更換模型配置來接入不同的 LLM (如 OpenAI, Anthropic)。
*   **FR-6 (New):** 系統應具備「快思慢想 (System 1/2)」的雙模態思考能力，區分簡單指令與複雜任務。

### 1.2 非功能性需求 (Non-Functional Requirements - NFRs)
| NFR 分類 | 具體需求描述 | 衡量指標/目標值 |
| :--- | :--- | :--- |
| **可擴展性 (Scalability)** | 能夠輕易增加新的 Agent 類型和工具。 | 新增工具不需修改 Kernel 程式碼。 |
| **可維護性 (Maintainability)** | 核心元件之間應低耦合，職責清晰。 | 各元件（Kernel, Agent, Tool）可獨立測試。 |
| **可用性 (Availability)** | 核心服務在互動模式下應保持響應。 | 互動模式下的單次請求處理時間 < 30s。 |
| **安全性 (Security)** | API Keys 等敏感資訊不能硬編碼在程式碼中。 | 透過環境變數或 `.env` 檔案載入。 |
| **智能深度 (Intelligence Depth)** | 複雜任務需經過解構與重塑 (Deconstruction & Refinement)。 | System 2 分析需包含完整的思考過程與重塑目標。 |

---

## 2. 高層次架構設計 (High-Level Architectural Design)

### 2.1 選定的架構模式 (Chosen Architectural Pattern)
*   **模式:** **核心化代理架構 (Kernel-based Agentic Architecture) 結合 雙重處理路由 (Dual-Process Routing)**
*   **選擇理由:** 此架構模式將系統的**調度中心 (Kernel)** 與**功能單元 (Agents, Tools)** 明確分離。Kernel 像一個微型作業系統，負責資源管理（載入 Agents/Tools）和任務分發。Router 層引入 Daniel Kahneman 的「快思慢想」框架，透過 System 1 (直覺/正則) 快速處理簡單指令，System 2 (邏輯/LLM) 深度解構複雜任務。這種設計不僅帶來極高的模組化，更大幅提升了系統對複雜意圖的理解能力。

### 2.2 系統組件圖 (System Component Diagram)

```mermaid
graph TD
    subgraph "使用者介面 (UI)"
        CLI[Interactive CLI]
    end

    subgraph "系統核心 (Core System)"
        Kernel[core.kernel.Kernel]
        subgraph "Router (Dual-Process)"
            Router[router.llm_analyzer.LLMTaskAnalyzer]
            System1[System 1: Fast Match]
            System2[System 2: LLM Deconstruction]
        end
        Orchestrator[core.orchestration.MultiAgentOrchestrator]
        Bus[core.communication.CommunicationBus]
        LLM[core.llm.LLMProvider]
        Workspace[core.workspace.WorkspaceManager]
        Logger[core.logger]
    end

    subgraph "智慧代理 (Agents)"
        Planner[agents.planner.PlannerAgent]
        Executor[agents.executor.ExecutorAgent]
        Reviewer[agents.reviewer.ReviewerAgent]
    end

    subgraph "工具 (Tools)"
        Python[tools.builtin.python]
        Files[tools.builtin.files]
        WebSearch[tools.builtin.websearch]
        Terminate[tools.builtin.terminate]
    end

    subgraph "外部服務 (External Services)"
        Ext_LLM[(Large Language Model)]
        Ext_System[(File System, Python, Web)]
    end

    CLI -->|user_input| Kernel
    Kernel -->|analyze| Router
    
    Router -->|Simple?| System1
    System1 -->|Direct/React| Kernel
    
    Router -->|Complex?| System2
    System2 -->|Deep Deconstruction| System2
    System2 -->|Refined Goal + Thought Process| Kernel
    
    Kernel -->|Context Update| Kernel
    Kernel -->|orchestrate (using Refined Goal)| Orchestrator

    Orchestrator -- "dispatches via" --> Bus
    Bus -->|message (with System 2 Context)| Planner
    Bus -->|message| Executor
    Bus -->|message| Reviewer

    Planner -->|calls (reads thought process)| LLM
    Executor -->|calls| LLM
    Executor -->|ReAct loop| Kernel
    Reviewer -->|calls| LLM

    Kernel -->|call_tool| Python
    Kernel -->|call_tool| Files
    Kernel -->|call_tool| WebSearch

    Kernel -->|create_run_context| Workspace
    Kernel -->|contextualize| Logger

    LLM -->|API call| Ext_LLM
    Python -->|execute| Ext_System
    Files -->|read/write| Ext_System
    WebSearch -->|search| Ext_System
```

### 2.3 主要組件/服務職責 (Key Components/Services Responsibilities)
| 組件/服務名稱 | 核心職責 | 主要技術/框架 | 依賴 |
| :--- | :--- | :--- | :--- |
| `main.py` | **應用入口**。提供互動式 CLI，並初始化 Kernel。 | Python | `core.kernel` |
| `core.kernel.Kernel` | **中央調度器**。管理生命週期，處理 System 2 上下文注入，分發任務。 | Python | `core.config`, `core.llm`, `agents`, `tools` |
| `core.orchestration.MultiAgentOrchestrator` | **多代理協調器**。實現 DIRECT/SEQUENTIAL/ORCHESTRATED/REACT 策略。 | Python | `core.kernel`, `agents` |
| `router.llm_analyzer.LLMTaskAnalyzer`| **雙模態分析器**。整合 System 1 (正則/快速) 與 System 2 (LLM/深度) 路由邏輯。 | Python, LLM | `core.types`, `core.llm` |
| `agents.planner.PlannerAgent` | **規劃者**。利用 System 2 的分析結果將任務分解為步驟。 | Python, LLM | `core.types`, `core.prompts` |
| `agents.executor.ExecutorAgent` | **執行者**。執行任務，支援 ReAct 循環，可呼叫工具。 | Python, LLM | `core.types`, `core.kernel` |
| `agents.reviewer.ReviewerAgent` | **審核者**。審核執行結果，提供改進建議。 | Python, LLM | `core.types` |
| `core.llm.LLMProvider` | **LLM 抽象層**。提供統一介面與多種 LLM 溝通。 | `openai`, `anthropic` | - |
| `core.workspace.WorkspaceManager` | **工作區管理器**。為每次執行建立隔離的目錄結構。 | `pathlib` | - |
| `core.logger` | **日誌系統**。基於 loguru，支援 run_id 上下文追蹤。 | `loguru` | - |

### 2.4 關鍵用戶旅程與組件交互 (Key User Journeys and Component Interactions)
*   **場景: 使用者輸入一個複雜任務 (例如："幫我重構 kernel 模組，把所有同步改成異步")**
    1.  **CLI (`main.py`)** 接收輸入，呼叫 `kernel.execute(task)`。
    2.  **Kernel** 呼叫 **Router (LLMTaskAnalyzer)**。
    3.  **Router** 識別此為複雜任務，啟動 **System 2 (Deep Research)** 流程。
    4.  **System 2** 進行解構，產出：
        *   `refined_goal`: "修改 core/kernel.py，將 execute 方法改為 async def..."
        *   `thought_process`: "用戶意圖是提升併發效能..."
        *   `key_questions`: "是否需要保持向後兼容？"
    5.  **Kernel** 接收分析結果，發現 `refined_goal`，於是**更新 Context**，將 Prompt 替換為 `refined_goal`，並將思考過程存入 `metadata`。
    6.  **Kernel** 根據策略 (e.g., `orchestrated`) 啟動 **Orchestrator**。
    7.  **Orchestrator** 呼叫 **PlannerAgent**。
    8.  **PlannerAgent** 讀取 Context 中的 `refined_goal` 與 `system_2_thought_process`，生成精確的執行計畫。
    9.  **Orchestrator** 依序調度 **ExecutorAgent** 執行計畫中的步驟。
    10. **ExecutorAgent** 執行具體代碼修改。
    11. 任務完成，返回結果。

---

## 3. 技術選型詳述 (Technology Stack Details)

| 分類 | 選用技術 | 選擇理由 (Justification) |
| :--- | :--- | :--- |
| **語言** | `Python 3.10+` | 生態豐富，開發效率高，適合 AI 應用。 |
| **核心框架** | `(無特定框架)` | 純 Python 實現，保持最大靈活性與可移植性。 |
| **配置管理** | `PyYAML` | 可讀性強，適合管理複雜的 Agent Prompts。 |
| **環境管理** | `python-dotenv` | 安全管理敏感資訊。 |
| **LLM 客戶端** | `openai`, `anthropic` | 穩定可靠的官方 SDK。 |
| **路由邏輯** | `Dual-Process Theory` | 結合啟發式規則 (System 1) 與 LLM 推理 (System 2)，平衡速度與深度。 |

---

## 4. 數據架構 (Data Architecture)

### 4.1 數據模型 (Data Models)
*   **`TaskContext`**: 核心上下文物件。新增 `metadata` 欄位用於存儲 `system_2_thought_process`, `refined_goal`, `key_questions`。
*   **`RoutingDecision`**: 包含 `complexity`, `strategy`, `agents` 以及 System 2 的分析產出。
*   **`ExecutionResult`**: 標準化執行結果。

### 4.2 數據流圖 (Data Flow Diagrams - DFDs)
*   數據流動遵循 System 1/2 的分流邏輯。簡單任務走快路徑，複雜任務經過 Context Enrichment (上下文增強) 階段。

---

## 5. 跨領域考量 (Cross-Cutting Concerns)

### 5.1 可觀測性 (Observability)
*   **日誌 (Logging):** 支援 `run_id` 追蹤。System 2 的分析過程會被完整記錄在 INFO/DEBUG 日誌中，便於事後審計。
*   **Metadata Tracking:** 每個步驟的執行結果都會保留 `metadata`，包含路由決策的依據。

### 5.2 工作區隔離 (Workspace Isolation)
*   每次執行在獨立目錄 (`workspace/run_xxx/`) 進行，確保檔案操作安全。

### 5.3 安全性與隱私 (Security and Privacy)
*   API Keys 環境變數管理。
*   System 2 的 Refinement 過程有助於識別並過濾潛在的惡意指令或高風險操作。
