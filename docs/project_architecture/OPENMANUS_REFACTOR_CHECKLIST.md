# OpenManus 重構實施清單

**基於**: REFACTOR_PLAN_OPENMANUS_ANALYSIS.md
**目標**: 從「自嗨 agent」變成「會問問題的 agent」
**原則**: 最小改動，最大效果

---

## Tier 1: Critical Fixes（35 分鐘）

### Task 1.1: 實施 ask_user 工具（10 分鐘）

**檔案**: `tools/builtin/ask_user.py`

- [ ] 創建 `tools/builtin/ask_user.py`
- [ ] 實作 `AskUserTool` 類（繼承 `BaseTool`）
- [ ] 參數：`question` (required), `context` (optional), `options` (optional)
- [ ] 回傳格式化的用戶輸入

**驗證**:
```bash
python -c "
from tools.builtin.ask_user import AskUserTool
import asyncio
tool = AskUserTool()
result = asyncio.run(tool.execute(question='測試問題', context='測試用'))
print(result)
"
```

---

- [ ] 在 `core/kernel.py` 註冊工具
  - 位置: `_initialize_builtin_tools` 方法
  - 加入: `self.tools["ask_user"] = AskUserTool()`

**驗證**:
```bash
python -c "
from core.kernel import Kernel
kernel = Kernel()
print('ask_user' in kernel.tools)  # Should print: True
"
```

---

- [ ] 更新 `tools/__init__.py`（如果需要）
  - 加入: `from tools.builtin.ask_user import AskUserTool`

---

### Task 1.2: 實施 Clarification Gate（15 分鐘）

**檔案**: `core/orchestration.py`

- [ ] 在 `_execute_orchestrated` 方法開頭（約第 150 行）加入 gate
- [ ] 檢查條件: `ambiguity_level in {"medium", "high"}` AND `key_questions` 存在
- [ ] 如果條件符合，返回 `ExecutionResult` with `error="CLARIFICATION_NEEDED"`

**程式碼位置**:
```python
async def _execute_orchestrated(self, context: TaskContext, agents: List[AgentRole]) -> ExecutionResult:
    # ========== ADD HERE (after line 154) ==========
    ambiguity = context.metadata.get("ambiguity_level", "low")
    key_questions = context.metadata.get("key_questions", [])

    if ambiguity in {"medium", "high"} and key_questions:
        # ... gate logic
        return ExecutionResult(success=False, ...)
    # ========== END ==========

    logger.info("=" * 50)
    # ... 原有流程
```

**驗證**:
```bash
# 測試案例（應該觸發 clarification）
python main.py
>>> 規劃旅遊

# 預期輸出
[Clarification Gate] Ambiguity detected
To provide an accurate response, I need to clarify:
1. 目的地偏好？
2. ...
```

---

- [ ] 可選：在 `main.py` 處理 `CLARIFICATION_NEEDED`
  - 位置: 主執行迴圈（約第 40-60 行）
  - 檢查: `if result.error == "CLARIFICATION_NEEDED"`
  - 行為: 印出問題，等待用戶輸入，重新執行

---

### Task 1.3: Reviewer Hard-Fail Rubric（10 分鐘）

**檔案**: `prompts/reviewer.yaml`

- [ ] 修改 `system` prompt，加入兩層評估標準
  - Layer A: Hard Constraints (MUST pass)
  - Layer B: Quality Scoring (1-10)

- [ ] 為不同任務類型定義 hard constraints:
  - Travel Planning: 地理可行性、預算拆分、時間合理性
  - Code Tasks: 語法正確、安全性、錯誤處理
  - Information Gathering: 引用來源、相關性

- [ ] 定義 JSON 輸出格式:
  ```json
  {
    "hard_constraints_passed": true/false,
    "failed_constraints": [...],
    "quality_score": 8,
    "verdict": "APPROVED|REVISION_NEEDED|REJECTED"
  }
  ```

---

**檔案**: `agents/reviewer.py`

- [ ] 在 `execute` 方法加入 hard constraint 檢查
  - 位置: 解析 review_response 之後
  - 邏輯: 如果 `hard_constraints_passed == false`，強制 `verdict = REJECTED`

**程式碼位置**:
```python
# agents/reviewer.py (約第 80-100 行)
review_json = json.loads(review_response)

# ========== ADD HERE ==========
if not review_json.get("hard_constraints_passed", True):
    logger.warning(f"[Reviewer] Hard constraints failed: {review_json.get('failed_constraints')}")
    review_json["needs_revision"] = True
    review_json["verdict"] = "REJECTED"
# ========== END ==========

return ExecutionResult(...)
```

**驗證**:
```bash
# 測試案例（應該 reject）
echo "規劃4天環遊世界 預算$1000" | python main.py

# 預期 Reviewer log
[Reviewer] Hard constraints failed: ['Itinerary geographically infeasible']
[Reviewer] Verdict: REJECTED
```

---

### Tier 1 完成檢查清單

測試所有三個功能:

- [ ] ask_user 工具可正常調用
- [ ] Clarification gate 在 ambiguity=medium 時觸發
- [ ] Reviewer 能 reject 不合理的旅遊規劃

**整合測試**:
```bash
pytest tests/integration/test_tier1_integration.py
```

---

## Tier 2: Policy & Structure（50 分鐘）

### Task 2.1: Tool-Use Policy（20 分鐘）

**檔案**: `router/llm_analyzer.py`

- [ ] 在 `_decide_routing` 方法定義 tool policy（約第 141-232 行）
- [ ] 根據 `intent_type` 設定 required_tools:
  - `planning` -> `["websearch", "ask_user"]` (至少一個)
  - `information_gathering` -> `["websearch"]`
  - `task_execution` -> suggested only

- [ ] 將 policy 存入 `metadata["tool_policy"]`

**程式碼位置**:
```python
# router/llm_analyzer.py (約第 215 行，return RoutingDecision 之前)
# ========== ADD HERE ==========
tool_policy = {
    "planning": {...},
    "information_gathering": {...}
}
policy = tool_policy.get(intent_type, {})
if policy:
    metadata["tool_policy"] = policy
# ========== END ==========
```

---

**檔案**: `agents/executor.py`

- [ ] 在 `_execute_react` 方法的終止判斷處加入 policy 檢查
  - 位置: 第 216-218 行（"No tool calls requested" 的 if 區塊）
  - 邏輯: 檢查 `required_tools` 是否被使用，如果沒有則 `continue` loop

**程式碼位置**:
```python
# agents/executor.py (第 216 行之後)
if not tool_call_requests:
    # ========== ADD HERE ==========
    tool_policy = context.metadata.get("tool_policy", {})
    if tool_policy.get("min_tool_calls", 0) > len(all_tool_calls):
        # Inject enforcement prompt
        local_messages.append({...})
        continue  # Don't break, retry
    # ========== END ==========

    logger.info("No tool calls requested. Finishing ReAct loop.")
    break
```

**驗證**:
```bash
# 測試案例（應該強制 websearch）
python main.py
>>> 東京有什麼好吃的

# 預期 log
[Tool Policy] Applied for information_gathering: requires websearch
[Executor] Calling tool 'websearch'
```

---

### Task 2.2: 結構化計劃（30 分鐘）

**檔案**: `core/types.py`

- [ ] 定義 `PlanStepStatus` enum
- [ ] 定義 `PlanStep` dataclass
  - 欄位: `description`, `required_info`, `validation_criteria`, `status`, `notes`
- [ ] 定義 `StructuredPlan` dataclass
  - 欄位: `plan_id`, `title`, `steps`, `missing_info`, `ready_to_execute`
  - 方法: `get_next_step()`, `progress_percentage()`

---

**檔案**: `prompts/planner.yaml`

- [ ] 修改 `system` prompt 要求 JSON 輸出
- [ ] 定義 JSON schema（包含 required_info 與 validation_criteria）
- [ ] 加入範例（missing info vs complete info）
- [ ] 強調規則：缺資訊 -> `ready_to_execute = false`

---

**檔案**: `agents/planner.py`

- [ ] 在 `execute` 方法解析 JSON plan
- [ ] 檢查 `ready_to_execute` flag
- [ ] 如果 `ready_to_execute == false`，返回 error with `PLAN_INCOMPLETE`
- [ ] 將 JSON 轉換為 `StructuredPlan` 物件
- [ ] 向後相容：支援文字 plan（fallback）

**程式碼位置**:
```python
# agents/planner.py (約第 60-90 行)
plan_json = json.loads(plan_response)

# ========== ADD HERE ==========
if not plan_json.get("ready_to_execute", False):
    return ExecutionResult(
        success=False,
        error="PLAN_INCOMPLETE",
        metadata={"missing_info": plan_json.get("missing_info")}
    )
# ========== END ==========
```

**驗證**:
```bash
# 測試案例（應該返回 missing_info）
pytest tests/unit/test_structured_plan.py
```

---

### Tier 2 完成檢查清單

- [ ] Tool policy 對 planning 任務強制 websearch/ask_user
- [ ] Structured plan 能識別 missing_info
- [ ] Planner 在資訊不足時拒絕產出 plan

**整合測試**:
```bash
pytest tests/integration/test_tier2_integration.py
```

---

## Tier 3: System Enhancement（6 小時）

### Task 3.1: OrchestrationMode（1 小時）

- [ ] 在 `core/orchestration.py` 定義 `OrchestrationMode` enum
- [ ] 在 `MultiAgentOrchestrator.__init__` 加入 `mode` 參數
- [ ] 在 gate 邏輯中根據 mode 決定行為:
  - `FAST`: 跳過 clarification gate
  - `STRICT`: 強制所有 gate
  - `INTERACTIVE`: 允許中途 ask_user
  - `AUTONOMOUS`: API 模式，無用戶互動

- [ ] 在 `main.py` 加入 mode 選擇:
  ```bash
  python main.py --mode strict  # 預設
  python main.py --mode fast    # 快速模式
  ```

---

### Task 3.2: Event-Driven Architecture（2 小時）

- [ ] 創建 `core/events.py`
- [ ] 定義 `EventType` enum
- [ ] 定義 Event dataclasses:
  - `ClarificationEvent`
  - `PolicyViolationEvent`
  - `HardConstraintFailedEvent`
- [ ] 實作 `EventBus`

- [ ] 在 `Kernel` 整合 EventBus
- [ ] 訂閱 clarification events
- [ ] 修改 Analyzer/Orchestrator 發布 events

---

### Task 3.3: Session Management（3 小時）

- [ ] 檢視現有 `core/workspace.py`（untracked file）
- [ ] 整合 OpenManus 的 session management 概念
- [ ] 實作 session tracking
- [ ] 實作 task classification（參考 OpenManus）

---

## 測試計畫

### 單元測試

建立以下測試檔案:

- [ ] `tests/unit/test_ask_user.py`
  - 測試 ask_user 工具基本功能
  - 測試 options 參數
  - 測試空輸入處理

- [ ] `tests/unit/test_structured_plan.py`
  - 測試 PlanStep 的 is_ready()
  - 測試 StructuredPlan 的 get_next_step()
  - 測試 progress_percentage()

---

### 整合測試

- [ ] `tests/integration/test_clarification_gate.py`
  - 案例 1: 模糊請求 -> 觸發 gate
  - 案例 2: 明確請求 -> 跳過 gate
  - 案例 3: medium ambiguity -> 提出 2-3 個問題

- [ ] `tests/integration/test_tool_policy.py`
  - 案例 1: planning 任務未用 websearch -> 強制重試
  - 案例 2: info gathering 使用 websearch -> 正常通過
  - 案例 3: 簡單任務無 policy -> 不受影響

- [ ] `tests/integration/test_reviewer_hard_fail.py`
  - 案例 1: 跨洲旅遊規劃 -> REJECTED
  - 案例 2: 無預算拆分 -> REJECTED
  - 案例 3: 合理規劃 -> APPROVED

---

### 端到端測試

- [ ] `tests/test_e2e_tier1.py`
  - 完整流程：模糊請求 -> clarify -> 重新執行 -> reviewer 檢查
  - 驗證所有 gate 協同工作

**測試案例**:
```python
async def test_travel_planning_with_clarification():
    """Test complete flow with ambiguous travel request"""

    # Step 1: 模糊請求
    result1 = await kernel.run("規劃旅遊")

    # 驗證: 應該要求 clarification
    assert result1.error == "CLARIFICATION_NEEDED"
    assert "目的地" in result1.response or "地點" in result1.response

    # Step 2: 提供資訊後重試
    result2 = await kernel.run(
        "規劃旅遊 京都 4天3夜 從台北出發 3/15 預算$2000 喜歡寺廟"
    )

    # 驗證: 應該成功執行
    assert result2.success == True
    assert "預算" in result2.response  # 應該有預算拆分

    # Step 3: Reviewer 檢查
    review = result2.metadata.get("execution_chain", [])[-1]
    assert review["verdict"] == "APPROVED"
    assert review.get("hard_constraints_passed") == True
```

---

## 快速驗證腳本

### 完整流程測試

創建 `scripts/test_refactor.sh`:
```bash
#!/bin/bash
set -euo pipefail

echo "=========================================="
echo "Tier 1 Refactor Validation"
echo "=========================================="

# Test 1: ask_user tool exists
echo "Test 1: Checking ask_user tool..."
python -c "from core.kernel import Kernel; k=Kernel(); assert 'ask_user' in k.tools" && \
  echo "✓ ask_user tool registered" || \
  echo "✗ ask_user tool NOT found"

# Test 2: Clarification gate
echo ""
echo "Test 2: Testing clarification gate..."
python -c "
from core.kernel import Kernel
from core.types import TaskContext
import asyncio

async def test():
    kernel = Kernel()
    context = TaskContext(prompt='規劃旅遊')
    result = await kernel.run(context)
    if result.error == 'CLARIFICATION_NEEDED':
        print('✓ Clarification gate triggered')
        return True
    else:
        print('✗ Clarification gate NOT triggered')
        return False

asyncio.run(test())
"

# Test 3: Run unit tests
echo ""
echo "Test 3: Running unit tests..."
pytest tests/unit/test_ask_user.py -v
pytest tests/unit/test_structured_plan.py -v

# Test 4: Run integration tests
echo ""
echo "Test 4: Running integration tests..."
pytest tests/integration/test_tier1_integration.py -v

echo ""
echo "=========================================="
echo "Validation Complete"
echo "=========================================="
```

---

## 逐步實施指南

### 第一天（35 分鐘）

**09:00 - 09:10**: Task 1.1 - 實施 ask_user 工具
- 創建 `tools/builtin/ask_user.py`
- 註冊到 Kernel

**09:10 - 09:25**: Task 1.2 - 實施 Clarification Gate
- 修改 `core/orchestration.py`
- 測試 gate 觸發邏輯

**09:25 - 09:35**: Task 1.3 - Reviewer Hard-Fail
- 修改 `prompts/reviewer.yaml`
- 修改 `agents/reviewer.py`

**09:35 - 09:50**: 整合測試
- 運行 `scripts/test_refactor.sh`
- 修正任何問題

**09:50 - 10:00**: 提交 Tier 1
```bash
git add tools/builtin/ask_user.py core/orchestration.py prompts/reviewer.yaml agents/reviewer.py
git commit -m "feat: implement Tier 1 refactor - clarification gates and hard-fail reviewer"
```

---

### 第二天（1.5 小時）

**10:00 - 10:20**: Task 2.1 - Tool-Use Policy
- 修改 `router/llm_analyzer.py`
- 修改 `agents/executor.py`

**10:20 - 10:50**: Task 2.2 - 結構化計劃
- 定義 schema in `core/types.py`
- 修改 `prompts/planner.yaml`
- 修改 `agents/planner.py`

**10:50 - 11:20**: 整合測試
- 運行 Tier 2 測試
- 端到端驗證

**11:20 - 11:30**: 提交 Tier 2
```bash
git add router/llm_analyzer.py agents/executor.py core/types.py prompts/planner.yaml agents/planner.py
git commit -m "feat: implement Tier 2 refactor - tool policy and structured plans"
```

---

## 常見問題與解決方案

### Q1: ask_user 在非互動環境（如 API）會失效怎麼辦？

**解決方案**:
```python
# tools/builtin/ask_user.py
class AskUserTool(BaseTool):
    def __init__(self, mode="interactive"):
        self.mode = mode  # "interactive" | "mock" | "auto"

    async def execute(self, question: str, **kwargs):
        if self.mode == "interactive":
            return input(f"Q: {question}\nA: ").strip()
        elif self.mode == "mock":
            return "MOCK_ANSWER"  # For testing
        elif self.mode == "auto":
            return "AUTO_DECLINED"  # Skip clarification
```

---

### Q2: Clarification gate 會不會讓簡單任務變慢？

**解決方案**: OrchestrationMode.FAST
```python
# 簡單任務使用 fast mode
kernel.orchestrator.mode = OrchestrationMode.FAST

# 或在 main.py
if task_looks_simple:
    orchestrator.mode = OrchestrationMode.FAST
```

---

### Q3: 結構化 plan 會破壞現有流程嗎？

**解決方案**: 向後相容
```python
# agents/executor.py (第 434 行)
async def _execute_with_plan(self, context, plan):
    if isinstance(plan, str):
        # Legacy text plan
        logger.warning("Using legacy text plan")
        return await self._execute_react(context)
    elif isinstance(plan, dict):
        # New structured plan
        structured = StructuredPlan.from_dict(plan)
        return await self._execute_structured_plan(context, structured)
```

---

### Q4: Reviewer 的 hard constraints 如何配置？

**解決方案**: 可配置的 rubric
```yaml
# config.yaml
reviewer:
  enable_hard_constraints: true
  travel_planning:
    max_countries_per_4days: 2
    require_budget_breakdown: true
    max_flight_hours_before_activity: 8
  code_tasks:
    require_syntax_check: true
    require_security_scan: true
```

---

## 成功標準

### Tier 1 成功標準

**功能**:
- [ ] 系統能偵測 ambiguity 並要求 clarification
- [ ] 系統能主動使用 ask_user 工具
- [ ] Reviewer 能 reject 地理上不可行的旅遊規劃

**測試**:
- [ ] 所有 Tier 1 單元測試通過
- [ ] 手動測試 3 個場景（模糊/完整/不合理）都符合預期

**用戶體驗**:
- [ ] 用戶反饋：「agent 會問問題了」
- [ ] 輸出品質：無明顯不合理的建議

---

### Tier 2 成功標準

**功能**:
- [ ] Planning 任務強制使用 websearch 或 ask_user
- [ ] Plan 有結構化 JSON 格式
- [ ] Plan 能識別 missing_info

**測試**:
- [ ] Tool policy 測試通過
- [ ] Structured plan 單元測試通過
- [ ] 端到端測試通過

**開發者體驗**:
- [ ] Debug 變容易（可看 plan 狀態）
- [ ] 行為可預測（有 policy 保證）

---

## 回退計畫

如果改動導致問題:

### Tier 1 回退
```bash
# 移除 clarification gate（保留 ask_user 工具）
git revert <commit-hash>

# 或手動註解
# core/orchestration.py
# if ambiguity in {"medium", "high"}:
#     # ... gate logic (commented out)
```

### Tier 2 回退
```bash
# 保留結構化 plan，但不強制
# agents/planner.py
if not plan_json.get("ready_to_execute", True):  # 改為 True（預設可執行）
    logger.warning("Plan incomplete but proceeding anyway")
    # Don't return error, continue
```

---

## 下一步行動

### 立即執行（現在就能做）

1. 創建 `tools/builtin/ask_user.py`
2. 修改 `core/orchestration.py` 加入 gate（約 10 行）
3. 修改 `prompts/reviewer.yaml` 加入 hard constraints

### 本週完成（Week 1）

- Tier 1 全部完成（35 分鐘）
- 寫測試（1 小時）
- 整合驗證（30 分鐘）

### 本月完成（Month 1）

- Tier 1 + Tier 2 完成
- 撰寫使用文檔
- 收集用戶反饋

---

## 附錄：快速參考

### 關鍵檔案清單

**需要修改**:
- `tools/builtin/ask_user.py` (新建)
- `core/kernel.py` (註冊 ask_user)
- `core/orchestration.py` (加入 gate)
- `core/types.py` (定義 StructuredPlan)
- `prompts/reviewer.yaml` (hard constraints)
- `prompts/planner.yaml` (JSON schema)
- `agents/reviewer.py` (hard constraint 檢查)
- `agents/planner.py` (plan validation)
- `router/llm_analyzer.py` (tool policy)
- `agents/executor.py` (policy enforcement)

**測試檔案**（新建）:
- `tests/unit/test_ask_user.py`
- `tests/unit/test_structured_plan.py`
- `tests/integration/test_clarification_gate.py`
- `tests/integration/test_tool_policy.py`
- `tests/integration/test_reviewer_hard_fail.py`
- `tests/integration/test_tier1_integration.py`
- `tests/integration/test_tier2_integration.py`

---

### 估計總工時

- **Tier 1**: 35 分鐘（核心修復）
- **Tier 1 測試**: 1 小時
- **Tier 2**: 50 分鐘（policy & structure）
- **Tier 2 測試**: 1 小時
- **Tier 3**: 6 小時（系統增強）

**總計**: 約 9 小時（可在 2-3 天完成）

---

### 優先序決策樹

```
需要立即解決問題？
├─ 是 -> Tier 1（35分鐘）
└─ 否
    └─ 需要系統性改善？
        ├─ 是 -> Tier 2（50分鐘）
        └─ 否 -> Tier 3（6小時，可延後）

生產環境有問題？
├─ 是 -> Tier 1（今天完成）
└─ 否 -> 按照 Week 1/2/3 計畫執行

時間有限？
└─ 只改這一行（10 行代碼解決 50% 問題）：
    core/orchestration.py 加入 clarification gate
```

---

**最後更新**: 2026-01-30
**狀態**: Ready for implementation
**下一步**: 執行 Tier 1 Task 1.1
