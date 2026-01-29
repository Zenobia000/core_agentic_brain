# 模組規格與測試案例 (Module Specification & Test Cases) - Core Agentic Brain

---

**文件版本 (Document Version):** `v2.0`
**最後更新 (Last Updated):** `2026-01-30`
**主要作者 (Lead Author):** `Gemini AI Assistant`
**審核者 (Reviewers):** `Core Development Team`
**狀態 (Status):** `草稿 (Draft)`

---

## 目錄 (Table of Contents)

- [模組: `core.kernel.Kernel`](#模組-corekernelkernel)
- [模組: `router.llm_analyzer.LLMTaskAnalyzer`](#模組-routerllmanalyzerllmtaskanalyzer)
- [模組: `core.llm.LLMProvider`](#模組-corellmllmprovider)
- [模組: `tools.builtin.python`](#模組-toolsbuiltinpython)

---

**目的**: 本文件旨在將高層次的架構設計分解到具體的模組層級，定義其詳細規格、測試場景，並使用契約式設計 (Design by Contract, DbC) 來精確定義每個函式的職責邊界，直接指導 TDD (測試驅動開發) 的實踐。

---

## 模組: `core.kernel.Kernel`

**對應架構文件**: `05_architecture_and_design_document.md`
**主要職責**: 系統的中央調度器，負責載入、管理和協調所有其他元件（Agents, Tools, LLM），並負責 System 2 上下文注入。

---

### 規格 1: `__init__(self, config_path)`

**描述 (Description)**: 初始化系統核心。此過程包括載入配置、初始化通訊匯流排、載入所有已啟用的工具，以及設定 LLM 提供者。

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1.  `config_path` 指向一個有效的 YAML 檔案，或者為 `None` 以使用預設路徑 `config.yaml`。
    2.  執行環境中必須設定必要的 API Key 環境變數 (例如 `OPENAI_API_KEY`)。
    3.  `prompts/` 和 `tools/` 目錄結構符合預期。
*   **後置條件 (Postconditions)**:
    1.  `self.config` 屬性被成功載入並合併。
    2.  `self.llm` 被初始化為一個 `LLMProvider` 實例。
    3.  `self.tools` 字典中包含了所有在 `config.yaml` 中啟用的工具實例。
    4.  `self.bus` 被初始化為一個 `CommunicationBus` 實例。
*   **不變性 (Invariants)**:
    1.  Kernel 實例在初始化後應處於一個可立即執行任務的狀態。

---

### 規格 2: `execute(self, request, context)`

**描述 (Description)**: 處理使用者請求的統一入口點，如同一個系統呼叫。它負責分析請求、路由到合適的 Agent、注入 System 2 上下文、透過通訊匯流排分發任務，並最終回傳執行結果。

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1.  Kernel 實例已被成功初始化。
    2.  `request` 是一個非空的字串。
*   **後置條件 (Postconditions)**:
    1.  如果 `LLMTaskAnalyzer` 返回 `refined_goal`，則注入到 `context` 中，且 `request` 被更新。
    2.  函式應回傳一個 `ExecutionResult` 物件。
    3.  `ExecutionResult.success` 標示了任務是否成功。
    4.  `ExecutionResult.response` 或 `ExecutionResult.error` 應包含對應的資訊。
*   **不變性 (Invariants)**:
    1.  無論成功或失敗，此函式都不應引發未處理的例外。

### 測試情境與案例 (`core.kernel.Kernel`)

*   **參考測試檔案**: `tests/integration/test_main_minimal.py`, `tests/test_system1_2_routing.py`

#### 情境 1: 正常路徑 (Happy Path)

*   **測試案例 ID**: `TC-Kernel-Exec-001`
*   **描述**: 成功執行一個簡單的直接任務 (無需工具)。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**: 初始化一個標準的 `Kernel`。
    2.  **Act**: 呼叫 `await kernel.execute("你好嗎？")`。
    3.  **Assert**:
        *   驗證回傳的 `result` 物件是 `ExecutionResult` 的實例。
        *   驗證 `result.success` 為 `True`。
        *   驗證 `result.response` 包含一段有意義的文字回答。

#### 情境 2: System 2 上下文注入

*   **測試案例 ID**: `TC-Kernel-Sys2-001`
*   **描述**: 驗證 Kernel 正確處理來自 System 2 的 refined goal。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**: 初始化 Kernel，Mock `LLMTaskAnalyzer` 使其返回帶有 `refined_goal="Refined"` 的 `RoutingDecision`。
    2.  **Act**: 呼叫 `await kernel.execute("Complex Task")`。
    3.  **Assert**:
        *   驗證下游 Agent 接收到的 Context Prompt 為 "Refined"。
        *   驗證 Context Metadata 中包含 `original_prompt="Complex Task"`。

---

## 模組: `router.llm_analyzer.LLMTaskAnalyzer`

**對應架構文件**: `05_architecture_and_design_document.md`
**主要職責**: 使用雙模態 (Dual-Process) 邏輯分析任務。

---

### 規格 1: `analyze(self, context)`

**描述**: 分析任務並返回路由決策。

**DbC**:
*   **Preconditions**: `context.prompt` 非空。
*   **Postconditions**:
    1.  返回 `RoutingDecision` 物件。
    2.  若觸發 System 2，`RoutingDecision.metadata` 包含 `refined_goal`。

---

## 模組: `core.llm.LLMProvider`

**對應架構文件**: `05_architecture_and_design_document.md`
**主要職責**: 提供一個統一的、支援多種模型的 LLM 介面，將不同服務 (OpenAI, Anthropic 等) 的 API 差異抽象化。

---

### 規格 1: `__init__(self, config)`

**描述 (Description)**: 根據傳入的 `config` 字典，初始化對應的 LLM 服務客戶端。

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1.  `config` 字典必須包含 `provider` 和 `model` 欄位。
    2.  對應 `provider` 的 API Key 必須在 `config` 中或在環境變數中提供。
*   **後置條件 (Postconditions)**:
    1.  `self.client` 被初始化為對應 LLM Provider 的客戶端物件 (例如 `openai.OpenAI` 或 `anthropic.Anthropic`)。
*   **不變性 (Invariants)**:
    1.  如果 `provider` 不被支援，應有降級機制 (fallback to OpenAI) 或拋出明確的錯誤。

### 規格 2: `generate(self, messages, tools)`

**描述 (Description)**: 呼叫 LLM 生成回應的核心方法。它處理了不同 Provider 的 API 差異，例如 Anthropic 的 system prompt 格式。

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1.  `messages` 是一個符合 OpenAI `chat.completions` 格式的列表。
*   **後置條件 (Postconditions)**:
    1.  回傳一個 `LLMResponse` 物件。
    2.  `LLMResponse.content` 包含模型生成的文字。
    3.  如果模型回傳了工具呼叫，`LLMResponse.tool_calls` 應包含其結構化資訊。

### 測試情境與案例 (`core.llm.LLMProvider`)

*   **參考測試檔案**: `tests/integration/test_llm_simple.py`

#### 情境 1: 正常路徑

*   **測試案例 ID**: `TC-LLM-Gen-001`
*   **描述**: 使用 OpenAI Provider 成功生成一段回應。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**: 建立一個 `LLMProvider` 實例，配置為使用 `openai`。
    2.  **Act**: 呼叫 `await provider.generate([{"role": "user", "content": "hello"}])`。
    3.  **Assert**:
        *   驗證回傳的 `response` 是 `LLMResponse` 的實例。
        *   驗證 `response.content` 是一個非空的字串。

#### 情境 2: 邊界情況 (Provider Fallback)

*   **測試案例 ID**: `TC-LLM-Init-001`
*   **描述**: 當 Provider 設定為一個未安裝 SDK 的服務 (例如 `anthropic`) 時，系統應能優雅地降級回 `openai`。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**: (在一個未安裝 `anthropic` 的環境中) 建立一個 `LLMProvider` 實例，`config` 中的 `provider` 設為 `anthropic`。
    2.  **Act**: 初始化過程。
    3.  **Assert**: 驗證 `provider.provider` 屬性最終被設定為 `openai`。

---

## 模組: `tools.builtin.python`

**對應架C-builti文件**: `08_project_structure_guide.md`
**主要職責**: 提供執行任意 Python 程式碼並回傳結果的能力。

---

### 規格 1: `execute(self, parameters)`

**描述 (Description)**: 執行 `parameters` 中提供的 Python 程式碼。

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1.  `parameters` 是一個字典。
    2.  `parameters` 中必須包含一個 `code` 鍵，其值為字串形式的 Python 程式碼。
*   **後置條件 (Postconditions)**:
    1.  回傳一個字典，其中包含程式碼執行的 `stdout`, `stderr`。
*   **不變性 (Invariants)**:
    1.  此函式不應讓執行的程式碼影響到主程式的穩定性（理想情況下應在沙箱中執行）。

### 測試情境與案例 (`tools.builtin.python`)

*   **參考測試檔案**: `tests/unit/test_tools.py`

#### 情境 1: 正常路徑

*   **測試案例 ID**: `TC-Tool-Py-001`
*   **描述**: 成功執行一段簡單的 print 敘述。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**: 實例化 `python` 工具。
    2.  **Act**: 呼叫 `tool.execute({"code": "print('hello world')"})`。
    3.  **Assert**: 驗證回傳結果字典中的 `stdout` 為 `'hello world\n'`。

#### 情境 2: 錯誤處理

*   **測試案例 ID**: `TC-Tool-Py-002`
*   **描述**: 執行一段會引發例外的程式碼。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**: 實例化 `python` 工具。
    2.  **Act**: 呼叫 `tool.execute({"code": "raise ValueError('test error')"})`。
    3.  **Assert**: 驗證回傳結果字典中的 `stderr` 包含 `ValueError: test error`。
