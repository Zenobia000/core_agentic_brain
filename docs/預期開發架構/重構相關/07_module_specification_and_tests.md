# 模組規格與測試案例 - OpenManus Linus 式重構

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2025-01-22`
**主要作者 (Lead Author):** `Linus-style 技術架構師`
**審核者 (Reviewers):** `核心開發團隊`
**狀態 (Status):** `開發中 (In Progress)`

---

## 目錄 (Table of Contents)

- [模組: Agent](#模組-agent)
  - [規格 1: process](#規格-1-process)
  - [測試情境與案例](#測試情境與案例-agent-process)
- [模組: LLM](#模組-llm)
  - [規格 1: call](#規格-1-call)
  - [測試情境與案例](#測試情境與案例-llm-call)
- [模組: ToolManager](#模組-toolmanager)
  - [規格 1: execute_tool](#規格-1-execute_tool)
  - [測試情境與案例](#測試情境與案例-toolmanager)

---

**目的**: 本文件遵循 Linus 式極簡哲學，定義 OpenManus 核心模組的詳細規格與測試案例。每個函數只做一件事，沒有特殊情況，保持簡潔。

---

## 模組: Agent

**對應架構文件**: `02_architecture_and_design_document.md#21-核心模組設計`
**檔案路徑**: `core/agent.py`
**行數限制**: < 150 行（包含進階功能）

---

### 規格 1: process

**描述 (Description)**: 處理用戶輸入，協調 LLM 調用與工具執行，返回最終結果。

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1.  `prompt` 不可為空字串
    2.  `config` 已正確載入並包含有效的 API key
    3.  所需工具已註冊並可用
*   **後置條件 (Postconditions)**:
    1.  返回一個非空字串結果
    2.  執行步驟不超過 `config.max_steps`
    3.  所有工具調用已完成或適當處理錯誤
*   **不變性 (Invariants)**:
    1.  Agent 實例的配置在處理過程中保持不變
    2.  工具執行不會修改 Agent 的內部狀態

---

### 測試情境與案例 (Agent.process)

#### 情境 1: 正常路徑 - 簡單文本響應

*   **測試案例 ID**: `TC-Agent-001`
*   **描述**: 處理不需要工具調用的簡單文本查詢
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        ```python
        agent = Agent("config.yaml")
        prompt = "什麼是 Python？"
        ```
    2.  **Act**:
        ```python
        result = agent.process(prompt)
        ```
    3.  **Assert**:
        *   驗證 `result` 為非空字串
        *   驗證 `result` 包含關於 Python 的描述
        *   驗證未調用任何工具

#### 情境 2: 工具調用路徑

*   **測試案例 ID**: `TC-Agent-002`
*   **描述**: 處理需要執行 Python 代碼的請求
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        ```python
        agent = Agent("config.yaml")
        prompt = "計算 2+2"
        ```
    2.  **Act**:
        ```python
        result = agent.process(prompt)
        ```
    3.  **Assert**:
        *   驗證 `result` 包含 "4"
        *   驗證調用了 Python 工具
        *   驗證執行步驟 <= 2

#### 情境 3: 邊界情況 - 達到最大步驟限制

*   **測試案例 ID**: `TC-Agent-003`
*   **描述**: 當執行步驟達到上限時的行為
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        ```python
        config = Config(max_steps=1)
        agent = Agent(config)
        prompt = "執行複雜多步驟任務"
        ```
    2.  **Act**:
        ```python
        result = agent.process(prompt)
        ```
    3.  **Assert**:
        *   驗證 `result` == "達到最大步驟限制"
        *   驗證執行步驟 == 1

#### 情境 4: 錯誤處理 - 無效輸入

*   **測試案例 ID**: `TC-Agent-004`
*   **描述**: 處理空字串輸入
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        ```python
        agent = Agent("config.yaml")
        prompt = ""
        ```
    2.  **Act & Assert**:
        ```python
        with pytest.raises(ValueError, match="prompt 不能為空"):
            agent.process(prompt)
        ```

---

## 模組: LLM

**對應架構文件**: `02_architecture_and_design_document.md#213-llm-封裝`
**檔案路徑**: `core/llm.py`
**行數限制**: < 80 行

---

### 規格 1: call

**描述 (Description)**: 調用 OpenAI API，返回 AI 響應。

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1.  `prompt` 長度 > 0 且 < 10000 字元
    2.  `api_key` 為有效的 OpenAI API key
    3.  網路連接可用
*   **後置條件 (Postconditions)**:
    1.  返回非空字串響應
    2.  響應長度 <= `max_tokens`
    3.  API 調用狀態碼為 200
*   **不變性 (Invariants)**:
    1.  API key 不會被記錄或暴露
    2.  每次調用都有唯一的 request_id

---

### 測試情境與案例 (LLM.call)

#### 情境 1: 正常 API 調用

*   **測試案例 ID**: `TC-LLM-001`
*   **描述**: 成功調用 OpenAI API 並獲得響應
*   **測試步驟 (Mock)**:
    1.  **Arrange**:
        ```python
        llm = LLM(model="gpt-4", api_key="test_key", max_tokens=100)
        mock_response = {"choices": [{"message": {"content": "測試響應"}}]}
        ```
    2.  **Act**:
        ```python
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            result = llm.call("測試提示")
        ```
    3.  **Assert**:
        *   驗證 `result` == "測試響應"
        *   驗證 `mock_post` 被調用一次
        *   驗證請求包含正確的 headers 和 data

#### 情境 2: 網路錯誤處理

*   **測試案例 ID**: `TC-LLM-002`
*   **描述**: 處理網路超時錯誤
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        ```python
        llm = LLM(model="gpt-4", api_key="test_key", max_tokens=100)
        ```
    2.  **Act**:
        ```python
        with patch('requests.post', side_effect=requests.Timeout):
            result = llm.call("測試提示")
        ```
    3.  **Assert**:
        *   驗證 `result` 包含 "LLM 錯誤"
        *   驗證錯誤訊息明確且對用戶友好

#### 情境 3: 邊界情況 - 超長輸入

*   **測試案例 ID**: `TC-LLM-003`
*   **描述**: 處理超過長度限制的輸入
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        ```python
        llm = LLM(model="gpt-4", api_key="test_key", max_tokens=100)
        long_prompt = "a" * 10001
        ```
    2.  **Act & Assert**:
        ```python
        with pytest.raises(ValueError, match="輸入過長"):
            llm.call(long_prompt)
        ```

---

## 模組: ToolManager

**對應架構文件**: `02_architecture_and_design_document.md#22-工具系統設計`
**檔案路徑**: `core/tools.py`
**行數限制**: < 50 行

---

### 規格 1: execute_tool

**描述 (Description)**: 動態載入並執行指定工具。

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1.  `tool_name` 對應到已註冊的工具
    2.  `input_str` 符合工具的輸入格式要求
    3.  工具模組可被成功導入
*   **後置條件 (Postconditions)**:
    1.  返回工具執行結果（字串）
    2.  工具執行時間 < 30 秒
    3.  任何工具錯誤都被捕獲並返回錯誤訊息
*   **不變性 (Invariants)**:
    1.  工具執行不影響其他工具的狀態
    2.  工具註冊表在執行期間保持不變

---

### 測試情境與案例 (ToolManager)

#### 情境 1: 成功執行 Python 工具

*   **測試案例 ID**: `TC-Tool-001`
*   **描述**: 執行簡單的 Python 代碼
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        ```python
        tool_manager = ToolManager()
        tool_manager.register("python", python_execute)
        code = "print(2+2)"
        ```
    2.  **Act**:
        ```python
        result = tool_manager.execute_tool("python", code)
        ```
    3.  **Assert**:
        *   驗證 `result` == "4\n"
        *   驗證執行時間 < 1 秒

#### 情境 2: 工具不存在

*   **測試案例 ID**: `TC-Tool-002`
*   **描述**: 嘗試執行未註冊的工具
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        ```python
        tool_manager = ToolManager()
        ```
    2.  **Act**:
        ```python
        result = tool_manager.execute_tool("nonexistent", "input")
        ```
    3.  **Assert**:
        *   驗證 `result` 包含 "工具不存在"
        *   驗證不拋出異常

#### 情境 3: 工具執行超時

*   **測試案例 ID**: `TC-Tool-003`
*   **描述**: 處理工具執行超時
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        ```python
        tool_manager = ToolManager(timeout=1)
        code = "import time; time.sleep(5)"
        ```
    2.  **Act**:
        ```python
        result = tool_manager.execute_tool("python", code)
        ```
    3.  **Assert**:
        *   驗證 `result` 包含 "執行超時"
        *   驗證執行時間 ≈ 1 秒

#### 情境 4: 工具執行錯誤

*   **測試案例 ID**: `TC-Tool-004`
*   **描述**: 處理工具執行時的異常
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        ```python
        tool_manager = ToolManager()
        code = "print(undefined_variable)"
        ```
    2.  **Act**:
        ```python
        result = tool_manager.execute_tool("python", code)
        ```
    3.  **Assert**:
        *   驗證 `result` 包含 "NameError"
        *   驗證錯誤訊息清楚且有幫助

---

## 模組: SubAgentManager (進階功能)

**對應架構文件**: `11_claude_code_integration_architecture.md#2-sub-agent-系統設計`
**檔案路徑**: `core/sub_agents.py`
**行數限制**: < 100 行
**模式**: 可選

---

### 規格 1: select_agent

**描述 (Description)**: 基於任務上下文自動選擇最適合的子代理。

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1.  至少有一個子代理已註冊
    2.  `task_context` 為非空字串
*   **後置條件 (Postconditions)**:
    1.  返回一個有效的子代理名稱
    2.  如果無匹配，返回 "general" 作為默認
*   **不變性 (Invariants)**:
    1.  子代理註冊表在選擇過程中不變

### 測試情境與案例 (SubAgentManager)

#### 情境 1: 關鍵字匹配選擇

*   **測試案例 ID**: `TC-SubAgent-001`
*   **描述**: 基於關鍵字成功選擇專門化子代理
*   **測試步驟**:
    1.  **Arrange**:
        ```python
        manager = SubAgentManager()
        config = SubAgentConfig(
            name="code_reviewer",
            specialization="代碼審查",
            prompt_template="...",
            available_skills=["analyze_code"],
            max_autonomy=3
        )
        manager.register_agent(config)
        ```
    2.  **Act**:
        ```python
        selected = manager.select_agent("請幫我審查這段代碼")
        ```
    3.  **Assert**:
        *   驗證 `selected` == "code_reviewer"

---

## 模組: RuleEngine (進階功能)

**對應架構文件**: `11_claude_code_integration_architecture.md#3-rulesprompt-templates-管理`
**檔案路徑**: `core/rules_engine.py`
**行數限制**: < 80 行
**模式**: 可選

---

### 規格 1: match_context

**描述 (Description)**: 根據上下文匹配適用的規則。

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1.  規則已從 YAML 檔案載入
    2.  `context` 為有效的字典結構
*   **後置條件 (Postconditions)**:
    1.  返回匹配規則名稱列表
    2.  列表可能為空（無匹配）
*   **不變性 (Invariants)**:
    1.  規則定義在匹配過程中不被修改

---

## 測試執行策略

### 單元測試框架
```python
# tests/test_agent.py
import pytest
from unittest.mock import patch, Mock
from core.agent import Agent

class TestAgent:
    def test_process_simple_text(self):
        """TC-Agent-001: 測試簡單文本響應"""
        agent = Agent("config.test.yaml")
        result = agent.process("什麼是 Python？")
        assert result
        assert "Python" in result

    def test_process_with_tool(self):
        """TC-Agent-002: 測試工具調用"""
        agent = Agent("config.test.yaml")
        result = agent.process("計算 2+2")
        assert "4" in result
```

### 測試覆蓋率要求
- 核心模組覆蓋率 > 90%
- 關鍵路徑覆蓋率 100%
- 錯誤處理路徑覆蓋率 > 80%

### 測試執行命令
```bash
# 執行所有測試
pytest tests/

# 執行特定模組測試
pytest tests/test_agent.py

# 生成覆蓋率報告
pytest --cov=core tests/
```

---

**批准簽字**:
- Linus-style Tech Lead: 待批准
- 核心開發團隊: 待批准

**下一步**: 實現測試案例並進行 TDD 開發