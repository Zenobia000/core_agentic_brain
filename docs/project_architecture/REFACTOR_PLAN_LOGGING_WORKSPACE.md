# 重構計畫：整合過程感知日誌與結構化工作區

---

**文件版本:** 1.0
**日期:** 2026-01-29
**作者:** Gemini AI Assistant

---

## 1. 總體目標與原則

### 1.1. 目標

本文檔旨在規劃一次架構重構，將 `OpenManus` 專案中成熟的**過程感知日誌 (Process-Aware Logging)** 和**結構化工作區 (Structured Workspace)** 思想，整合到 `core_agentic_brain` 的靈活架構中。

最終目標是達成：

1.  **增強可觀測性 (Observability)**：引入細粒度的日誌記錄，能夠清晰追蹤單一請求在系統內部流轉的完整生命週期，包括 Agent 的「思考」、「計畫」、「行動」和「觀察」過程。
2.  **強化產物管理 (Artifact Management)**：建立一個形式化的工作區 (Workspace) 機制，對每次執行的輸入、輸出和臨時檔案進行隔離和管理，提升安全性、可追蹤性和可重複性。

### 1.2. 設計原則

整個整合過程必須嚴格遵守 `core_agentic_brain` 原有的核心設計原則：

*   **維持微核心架構**：`Kernel` 的角色不變，依然是低耦合的中央調度器。
*   **保持組件解耦**：`Agent` 和 `Tool` 等組件依然透過 `CommunicationBus` 或抽象介面進行互動，不能引入對 `Kernel` 的直接依賴。
*   **配置驅動**：所有新功能（如日誌級別、工作區根目錄）都應是可透過 `config.yaml` 進行配置的。

---

## 2. 第一部分：過程感知日誌整合

### 2.1. 步驟一：引入 `loguru` 並取代 `simple_logger.py`

*   **行動**: 刪除 `core/simple_logger.py`，建立一個新的 `core/logger.py` 模組。
*   **細節**:
    *   在新模組中使用 `loguru` 函式庫作為日誌記錄引擎。
    *   預設配置兩個日誌輸出 (Sink)：
        1.  **控制台 (Console)**：日誌級別設為 `INFO`，格式應簡潔，方便開發者快速查看關鍵步驟。
        2.  **日誌檔案 (File)**：日誌級別設為 `DEBUG`，輸出到 `workspace/logs/` 目錄下，以時間戳（如 `run_{time}.log`）命名檔案。此檔案將記錄所有詳細資訊，用於深度除錯。
    *   日誌的相關配置（如級別、路徑）應可透過 `config.yaml` 進行設定。

### 2.2. 步驟二：建立 `run_id` 以追蹤完整執行鏈路

*   **行動**: 在 `core/kernel.Kernel.execute()` 方法的起始點，為每一次獨立的請求生成一個唯一的 `run_id`（例如 `run_...` 或 UUID）。
*   **細節**:
    *   將此 `run_id` 附加到 `core.types.TaskContext` 物件上，使其能夠在整個呼叫鏈中被訪問。
    *   使用 `loguru` 的 `contextualize` 或 `bind` 功能，將 `run_id` 綁定到當前的執行上下文中。這樣，後續的所有日誌訊息都會自動附加 `[run_id]` 前綴，無需在每個日誌點手動傳遞。
    *   **範例**:
      ```python
      # core/kernel.py
      from core.logger import logger

      async def execute(self, request: str, ...):
          run_id = f"run_{uuid.uuid4().hex[:8]}"
          with logger.contextualize(run_id=run_id):
              # ... all subsequent logs will have this run_id
              task_context.run_id = run_id
              # ...
      ```

### 2.3. 步驟三：在關鍵節點注入描述性日誌

*   **行動**: 在 `Kernel`, `PlannerAgent`, `ExecutorAgent` 的核心邏輯中，加入能反映其「意圖」的日誌。
*   **細節** (所有日誌都會自動包含 `[run_id]`):
    *   **Kernel**:
        *   `logger.info("Request received. Routing strategy: {strategy}")`
        *   `logger.info("Dispatching task to agent: {agent_name}")`
        *   `logger.info("Execution finished. Success: {status}")`
    *   **PlannerAgent**:
        *   `logger.info("Planning started for task: '{prompt}'")`
        *   `logger.debug("Plan created: {plan_steps}")` (使用 DEBUG 級別，因為計畫可能很長)
    *   **ExecutorAgent** (實現 ReAct 風格日誌):
        *   在呼叫 LLM 決定下一步行動前: `logger.info("Thinking...")`
        *   當 LLM 回應包含純文字內容時: `logger.info("Thought: {llm_content}")`
        *   當 LLM 回應要求呼叫工具時: `logger.info("Action: Call tool '{tool_name}' with args: {args}")`
        *   當工具執行完畢後: `logger.info("Observation: Tool '{tool_name}' returned: {result}")`

---

## 3. 第二部分：結構化工作區管理

### 3.1. 步驟一：建立 `core/workspace.py`

*   **行動**: 建立 `core/workspace.py` 檔案，並在其中定義 `WorkspaceManager` 類別，其設計應參考 `OpenManus` 的 `WorkspaceAPI`。
*   **細節**:
    *   `WorkspaceManager` 在初始化時讀取 `config.yaml` 中定義的工作區根目錄路徑（預設為 `workspace/`）。
    *   提供核心方法 `create_run_context(run_id: str) -> Path`。此方法會根據 `run_id` 建立一個專屬、隔離的執行目錄，例如 `workspace/runs/run_.../`。
    *   在該執行目錄下，自動建立標準子目錄：`input/` (用於放置初始檔案), `output/` (用於儲存最終產物), `temp/` (用於儲存中間過程檔案)。

### 3.2. 步驟二：將 Workspace 管理整合到 Kernel

*   **行動**:
    1.  `Kernel` 在 `__init__` 中實例化 `WorkspaceManager`。
    2.  在 `Kernel.execute()` 的開頭，緊隨 `run_id` 生成之後，呼叫 `workspace.create_run_context(run_id)` 來準備好本次執行的目錄。
    3.  將返回的工作區路徑 (`run_workspace_path`) 儲存到 `TaskContext.workspace_path` 屬性中，以便後續的組件可以訪問。

### 3.3. 步驟三：重構工具使其「工作區感知 (Workspace-Aware)」

*   **行動**: 這是確保安全和產物隔離的關鍵一步。讓所有工具的操作範圍被嚴格限制在當前執行的工作區內。
*   **細節**:
    1.  修改 `tools/base.py` 中的 `BaseTool` 介面，將 `execute` 方法的簽章從 `execute(parameters: Dict)` 修改為 `execute(parameters: Dict, context: TaskContext)`。這樣工具就能訪問到 `context.workspace_path`。
    2.  修改 `Kernel` 的 `call_tool` 方法，確保在呼叫工具時，將當前的 `TaskContext` 完整傳遞給工具的 `execute` 方法。
    3.  **重構所有內建工具** (以 `files` 工具為例):
        *   `files.write` 工具：
            *   **舊**: 參數可能包含絕對路徑 `path`。
            *   **新**: 參數應改為相對路徑的 `filename` 和 `content`。工具的內部實作會將檔案固定寫入到 `context.workspace_path / "output" / filename`。這能有效防止 Agent 在系統任意位置寫入檔案。
        *   `files.read` 工具：
            *   **舊**: 參數可能包含絕對路徑 `path`。
            *   **新**: 參數應改為相對路徑的 `filename`。工具會優先嘗試從 `context.workspace_path / "input"` 讀取，其次從 `output` 或 `temp` 讀取。
        *   `python.execute` 工具：
            *   執行的 Python 子進程的**當前工作目錄 (CWD)** 應被強制設定為 `context.workspace_path`。這樣，即使程式碼中有相對路徑的檔案操作，也會被限制在這個沙箱化的目錄內。

---

## 5. 第三部分：將 ReAct 循環整合到 ExecutorAgent

### 5.1. 目標

將 `OpenManus` 的高效 ReAct 執行引擎，作為一個**可選的、專門的執行策略**，無縫地嵌入到 `core_agentic_brain` 的靈活路由架構中。這意味著：

*   `Kernel` 依然負責高層次的路由決策。
*   `ExecutorAgent` 將具備內部 ReAct 循環，用於處理需要多步驟思考和工具使用的複雜任務。

### 5.2. 行動一：修改 `agents/executor.py` 中的 `ExecutorAgent.execute()` 方法

*   **說明**: 將目前 `ExecutorAgent` 的單次執行邏輯，改造成一個內部 `while` 循環，以模擬 `OpenManus` 的 ReAct 模式。

```python
# agents/executor.py
import json
import uuid # 為了範例中的 run_id，但實際應從 TaskContext 獲取
from typing import List, Dict, Any, Optional

from agents.base import BaseAgent
from core.types import TaskContext, ExecutionResult, LLMResponse # 假設 LLMResponse 已在 core.types 中定義
from core.logger import logger # 使用新的日誌系統

# (假設 ExecutorAgent 的 __init__ 已被修改，能接收 Kernel 實例，或有其他方式獲取 LLM 與工具定義)
# 為了簡化範例，假設 self.llm 和 self.kernel 在 Agent 內部可用。

class ExecutorAgent(BaseAgent):
    # ... (其他初始化與方法不變)

    async def execute(self, context: TaskContext) -> ExecutionResult:
        """
        使用內建的 ReAct 循環來執行給定的任務。
        """
        max_react_steps = 10 # 可從 config.yaml 或 context 中獲取
        current_react_step = 0
        
        # 為本次 ReAct 循環建立一個本地的對話歷史
        local_messages: List[Dict[str, Any]] = [{"role": "user", "content": context.prompt}]

        # 確保 TaskContext 中有 run_id，用於日誌追蹤
        run_id = context.run_id if hasattr(context, 'run_id') else f"local_react_{uuid.uuid4().hex[:4]}"
        
        with logger.contextualize(run_id=run_id, agent="ExecutorAgent"): # 新增 agent 標籤
            logger.info(f"Starting internal ReAct loop for task: '{context.prompt}'")

            while current_react_step < max_react_steps:
                current_react_step += 1
                logger.debug(f"ReAct Step {current_react_step}/{max_react_steps}")

                # --- 1. Think 階段 (LLM 思考與決定行動) ---
                logger.info("ExecutorAgent thinking with LLM...")
                
                # 呼叫 LLM 獲取思考和工具呼叫
                llm_response: LLMResponse = await self.llm.generate(
                    messages=local_messages,
                    tools=self.kernel.get_tool_definitions() # 透過 Kernel 獲取所有工具的定義
                )

                thought = llm_response.content if llm_response.content else ""
                action_requests = llm_response.tool_calls if llm_response.tool_calls else []

                if thought:
                    logger.info(f"Thought: {thought}")
                
                # 將 LLM 的思考和行動決策加入本地歷史
                assistant_message: Dict[str, Any] = {"role": "assistant", "content": thought}
                if action_requests:
                    # 工具呼叫需符合 LLM API 格式，這裡簡化為直接附加
                    assistant_message["tool_calls"] = action_requests
                local_messages.append(assistant_message)

                # --- 2. 判斷 ReAct 循環終止條件 ---
                if not action_requests:
                    logger.info("No more actions required by LLM. Finishing ReAct loop.")
                    return ExecutionResult(success=True, response=thought)
                
                # 檢查是否呼叫了 Terminate 工具 (假設工具名為 'terminate')
                if any(call.function.name == "terminate" for call in action_requests):
                     logger.info("Terminate tool called. Finishing ReAct loop.")
                     final_thought = thought.split("terminate")[0].strip() if thought else "" # 截斷 terminate 之前的思考
                     return ExecutionResult(success=True, response=final_thought)

                # --- 3. Act 階段 (執行工具並獲取觀察結果) ---
                tool_observations: List[Dict[str, Any]] = []
                for tool_call_obj in action_requests:
                    # 假設 tool_call_obj 是符合 LLM tool_call 格式的物件
                    tool_name = tool_call_obj.function.name
                    tool_args = json.loads(tool_call_obj.function.arguments) # 參數為 JSON 字串

                    logger.info(f"Action: Calling tool '{tool_name}' with args: {tool_args}")
                    
                    # 透過 Kernel 呼叫工具，並傳遞完整的 TaskContext (包含 workspace_path)
                    try:
                        observation_result = await self.kernel.call_tool(
                            tool_name=tool_name, 
                            parameters=tool_args, 
                            context=context # 傳遞 TaskContext
                        )
                        observation_content = str(observation_result)
                    except Exception as e:
                        observation_content = f"Tool execution failed: {e}"
                        logger.error(f"Tool '{tool_name}' failed: {e}")

                    logger.info(f"Observation: Tool '{tool_name}' returned: {observation_content}")
                    
                    tool_observations.append({
                        "tool_call_id": tool_call_obj.id, # 確保 tool_call_obj 有 id 屬性
                        "role": "tool",
                        "name": tool_name,
                        "content": observation_content,
                    })

                # 將觀察結果加入本地歷史，供 LLM 下一輪思考使用
                local_messages.extend(tool_observations)
            
            # 循環結束 (達到 max_react_steps)
            logger.warning(f"Reached max ReAct steps ({max_react_steps}). Finishing ReAct loop.")
            final_response = local_messages[-1]['content'] if local_messages and 'content' in local_messages[-1] else "Execution finished after reaching max steps."
            return ExecutionResult(success=True, response=final_response)
```

### 5.3. 行動二：更新 `Kernel` 介面 (如果需要)

*   **說明**: 確保 `Kernel` 提供了 `ExecutorAgent` 呼叫工具所需的所有資訊。
*   **細節**:
    *   `Kernel` 的 `call_tool` 方法需要能接受並傳遞 `TaskContext`。
    *   `Kernel` 需提供一個方法（如 `get_tool_definitions()`）讓 Agent 能夠獲取所有可用工具的定義。

### 5.4. 行動三：與 `TaskAnalyzer` (路由器) 協同工作

*   **說明**: `Router` 仍將負責判斷何時需要啟動 `ExecutorAgent` 的 ReAct 循環。
*   **細節**:
    *   `TaskAnalyzer` 將繼續根據任務複雜度、關鍵字等判斷是否將任務路由給 `ExecutorAgent`。
    *   對於簡單的問答，`TaskAnalyzer` 可能會將任務路由給一個更輕量級的 Agent（例如一個直接呼叫 LLM 的 QA Agent），繞過 `ExecutorAgent` 的複雜循環。

### 5.5. 預期效益

*   **優化資源使用**: 只有在必要時才使用 ReAct 循環，避免不必要的 LLM 呼叫。
*   **保持靈活性**: `core_agentic_brain` 的路由層依然是主控方，決定執行策略。
*   **增強能力**: `ExecutorAgent` 透過 ReAct 模式，能夠更有效地解決需要工具協調和多步驟推理的複雜任務。
*   **高可觀測性**: 結合第一部分導入的日誌系統，ReAct 的每一步思考、行動和觀察都將被詳細記錄。
