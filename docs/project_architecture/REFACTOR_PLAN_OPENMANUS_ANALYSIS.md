# OpenManus 設計分析與系統重構計畫

**文檔版本**: v1.0
**建立日期**: 2026-01-30
**分析對象**: OpenManus (legacy/OpenManus) vs Core Agentic Brain
**分析原則**: Linus Torvalds 技術哲學 - 好品味、實用主義、零特殊情況

---

## Executive Summary

### 核心判斷

**OpenManus 值得學習的設計**:
- `ask_human` 工具 - 明確的「問用戶」機制
- `PlanningTool` 的步驟狀態追蹤 - 計劃有結構化狀態
- `ToolCollection` 抽象 - 工具註冊與管理清晰

**現有系統已優於 OpenManus 的部分**:
- LLM Analyzer 的雙階段分析（問題理解 + 路由決策）
- System 1/2 概念分離
- Reviewer 品質檢核機制

**根本問題不在架構，在於「缺決策閘門」**:
> 系統能識別問題（ambiguity, missing info），但不阻止執行 - 這是最大的設計缺陷。

---

## 問題診斷：從 Log 直接讀到的症狀

### 當前系統的四大症狀

#### 1. 有辨識到模糊，但沒有真的去問
```
Analyzer 輸出:
- Ambiguity Level: medium
- Key Questions: ['旅遊地點偏好？', '冒險活動的具體要求？', ...]

實際行為:
- Orchestrator 沒有走 Clarify phase
- Executor 直接產出 itinerary
```

**結論**: 分析知道缺，但執行假裝不缺。

---

#### 2. ReAct loop 的終止條件太「順從模型」
```
Log: "No tool calls requested. Finishing ReAct loop."
```

**問題**: 模型沒說要用工具 -> 系統就收工
**後果**: 只要模型「覺得自己可以瞎掰」就會一路寫完，工具永遠不會被叫

---

#### 3. 旅遊規劃回答不合理，但 Reviewer 仍 APPROVED
```
輸出: 4天跨 4 國（清邁->宿霧->智利->尼泊爾）
Reviewer: verdict=APPROVED, quality_score=8, issues_found=2, needs_revision=False
```

**地理可行性檢核**:
- 4天3夜跨洲旅行（亞洲 -> 南美 -> 亞洲）
- 交通時間未計算
- 預算未拆分卻宣稱 "within budget"
- 無出發地、日期、簽證、航班資訊

**結論**: Reviewer 缺少「硬約束」與「可行性檢核」。

---

#### 4. Planner 47 steps 形同裝飾
```
Log: "Planning completed with 47 steps"
實際: Executor 第一個 Thought 就直接輸出完整行程
```

**問題**: 計劃是文字，沒有被機器可執行地約束
**後果**: Plan 不能控制 execution flow

---

## 設計對比分析

### 數據結構對比

#### OpenManus: 結構化計劃（機器可執行）
```python
# app/tool/planning.py
plan = {
    "plan_id": "plan_123",
    "title": "Travel Planning",
    "steps": [
        "Clarify destination preference",
        "Search flight options",
        "Book accommodation"
    ],
    "step_statuses": ["not_started", "in_progress", "completed"],
    "step_notes": ["", "Found 3 options", "Booked Hotel X"]
}
```

**優點**:
- 狀態可追蹤（not_started -> in_progress -> completed -> blocked）
- 機器可驗證（檢查所有 step_statuses 是否為 completed）
- 可視化進度（47% completed）

**缺點**:
- 步驟只是文字，沒有 `required_info` 或 `validation_criteria`
- 沒有「缺資訊就不能標記為 completed」的檢查

---

#### 現有系統: 文字計劃（不可驗證）
```python
# core/orchestration.py
context.metadata["plan"] = "規劃一趟4天3夜的..."
```

**問題**:
- 無法追蹤執行進度
- 無法驗證計劃完整性
- Reviewer 無法檢查「計劃是否被遵守」

---

### Agent 架構對比

#### OpenManus: 四層繼承
```
BaseAgent (state, memory, run loop)
  └─ ReActAgent (think/act pattern)
      └─ ToolCallAgent (tool execution)
          └─ Manus (具體實現 + MCP)
```

**品味評分**: 🔴 過度設計
- `ReActAgent.think()` 和 `ToolCallAgent.think()` 有重複邏輯
- 每層都在改 think/act，但沒有一層在做 gating
- 違反 Linus 原則：「如果需要超過 3 層縮進，你就完蛋了」

---

#### 現有系統: 三層分離
```
Router (LLMTaskAnalyzer)
  └─ Orchestrator (MultiAgentOrchestrator)
      └─ Agents (Planner, Executor, Reviewer)
```

**品味評分**: 🟢 結構清晰
- 職責分離明確（routing, orchestration, execution）
- 沒有不必要的繼承
- 符合 Linus 原則：簡單、直接

---

### 工具系統對比

#### OpenManus: ToolCollection + ask_human
```python
# app/tool/ask_human.py
class AskHuman(BaseTool):
    async def execute(self, inquire: str) -> str:
        return input(f"Bot: {inquire}\n\nYou: ").strip()

# app/agent/manus.py
available_tools: ToolCollection = ToolCollection(
    PythonExecute(),
    BrowserUseTool(),
    StrReplaceEditor(),
    AskHuman(),      # <- 關鍵：問用戶當作工具
    Terminate(),
)
```

**優點**:
- `ask_human` 是一等公民工具（與 shell、python 同級）
- 模型可以「選擇」問用戶

**缺點**:
- 沒有 policy 決定「何時必須問」
- 模型可以選擇「不問」然後瞎編

---

#### 現有系統: 缺少 ask_user 工具
```python
# tools/builtin/ 沒有 ask_user
# 只有: files.py, python.py, terminate.py, websearch.py
```

**問題**: 系統無法主動向用戶提問
**後果**: 遇到 ambiguity 只能硬著頭皮猜

---

### Clarification 機制對比

#### OpenManus: 無系統性 Clarification
- 有 `ask_human` 工具，但靠模型「想起來要問」
- 沒有 ambiguity detection
- 沒有 clarification gate

---

#### 現有系統: 有檢測，無行動
```python
# router/llm_analyzer.py
if refinement.get('key_questions'):
    logger.info(f"  - Key Questions: {refinement.get('key_questions')}")
    # ← 只 log，不阻止執行！
```

**問題**: 發現問題卻不解決
**改法**: 把 log 改成 gate

---

## 核心設計缺陷對照表

| 缺陷類型 | OpenManus | 現有系統 | 誰更嚴重 |
|---------|-----------|---------|----------|
| **Clarification Gate** | 無檢測、無工具 policy | 有檢測、無 gate | 現有系統更嚴重（知道卻不做） |
| **Tool-Use Policy** | 無 | 無 | 一樣嚴重 |
| **Plan Validation** | 無 validation criteria | 計劃是純文字 | 現有系統更嚴重 |
| **Reviewer Hard-Fail** | 沒有 Reviewer | 有 Reviewer 但太軟 | OpenManus 更嚴重 |

---

## 重構計畫：三個 Tier

### Tier 1: 立即可改（今天能落地）

#### 1.1 加入 ask_user 工具

**目標**: 讓系統可以主動向用戶提問

**實施步驟**:

1. 創建 `tools/builtin/ask_user.py`:
```python
"""
Ask User Tool - Interactive clarification tool
Based on OpenManus design pattern
"""

from tools.base import BaseTool, ToolResult
from typing import Any, Dict, Optional, List

class AskUserTool(BaseTool):
    """Tool for asking user clarification questions.

    Use this tool when:
    - Information is missing or ambiguous
    - Multiple valid approaches exist
    - User preference is needed

    Do NOT guess - ask instead.
    """

    def __init__(self):
        super().__init__(
            name="ask_user",
            description=(
                "Ask the user for clarification when information is missing or ambiguous. "
                "Use this tool instead of making assumptions or guessing. "
                "Provide clear, specific questions."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to ask the user (clear and specific)"
                    },
                    "context": {
                        "type": "string",
                        "description": "Why you need this information (helps user understand)"
                    },
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: Suggested options for the user to choose from"
                    }
                },
                "required": ["question"]
            }
        )

    async def execute(
        self,
        question: str,
        context: str = "",
        options: Optional[List[str]] = None,
        **kwargs
    ) -> ToolResult:
        """Execute the ask user tool.

        Args:
            question: The question to ask
            context: Why this information is needed
            options: Optional list of suggested answers

        Returns:
            ToolResult with user's response
        """
        # Build prompt
        prompt = f"\n{'='*60}\n"
        prompt += f"QUESTION: {question}\n"

        if context:
            prompt += f"\nCONTEXT: {context}\n"

        if options:
            prompt += f"\nSUGGESTED OPTIONS:\n"
            for i, opt in enumerate(options, 1):
                prompt += f"  {i}. {opt}\n"

        prompt += f"{'='*60}\n"
        prompt += "Your answer: "

        # Get user input
        user_input = input(prompt).strip()

        if not user_input:
            return ToolResult(
                success=False,
                output="",
                error="User provided no input"
            )

        return ToolResult(
            success=True,
            output=user_input
        )
```

2. 註冊到 Kernel (`core/kernel.py` 的 `_initialize_builtin_tools`):
```python
from tools.builtin.ask_user import AskUserTool

# 在 _initialize_builtin_tools 方法中:
self.tools["ask_user"] = AskUserTool()
```

**驗證方式**:
```bash
# 在 main.py 測試
pytest tests/unit/test_ask_user.py
```

**估計工時**: 10 分鐘

---

#### 1.2 加入 Clarification Gate

**目標**: 當 ambiguity >= medium 時，強制澄清

**實施步驟**:

1. 修改 `core/orchestration.py` 的 `_execute_orchestrated`:
```python
async def _execute_orchestrated(
    self,
    context: TaskContext,
    agents: List[AgentRole]
) -> ExecutionResult:
    """協調執行 - Planner -> Executor -> Reviewer (with iteration)"""

    # ========== NEW: Clarification Gate ==========
    ambiguity = context.metadata.get("ambiguity_level", "low")
    key_questions = context.metadata.get("key_questions", [])

    # Check if clarification is needed
    if ambiguity in {"medium", "high"} and key_questions:
        logger.info("[Clarification Gate] Ambiguity detected, requesting clarification")
        logger.info(f"[Clarification Gate] Ambiguity level: {ambiguity}")
        logger.info(f"[Clarification Gate] Questions to ask: {key_questions}")

        # Build clarification request
        clarify_text = "To provide an accurate response, I need to clarify:\n\n"
        for i, q in enumerate(key_questions[:3], 1):  # Max 3 questions
            clarify_text += f"{i}. {q}\n"

        clarify_text += "\nPlease provide this information so I can proceed."

        return ExecutionResult(
            success=False,
            response=clarify_text,
            error="CLARIFICATION_NEEDED",
            metadata={
                "needs_clarification": True,
                "key_questions": key_questions,
                "ambiguity_level": ambiguity,
                "refined_goal": context.metadata.get("refined_goal", "")
            }
        )
    # ========== END: Clarification Gate ==========

    logger.info("=" * 50)
    logger.info("[Orchestrator] Starting orchestrated execution (Planner -> Executor -> Reviewer)")
    # ... 原有流程
```

2. 可選：加入 interactive mode 支援
```python
# 在 main.py 的主循環中處理 CLARIFICATION_NEEDED
if result.error == "CLARIFICATION_NEEDED":
    print(result.response)
    # 等待用戶補充資訊，重新執行
```

**驗證方式**:
```bash
# 測試案例
python main.py
>>> 規劃旅遊 4天3夜 喜歡冒險

# 預期輸出
[Clarification Gate] Ambiguity detected
To provide an accurate response, I need to clarify:
1. 旅遊地點偏好？
2. 冒險活動的具體要求？
3. 美食喜好或特色飲食？
```

**估計工時**: 15 分鐘

---

#### 1.3 Reviewer 加入 Hard-Fail Rubric

**目標**: Reviewer 從「評分員」變成「守門員」

**實施步驟**:

1. 修改 `prompts/reviewer.yaml`:
```yaml
system: |
  You are a quality reviewer using TWO-LAYER evaluation criteria.

  ## Layer A: Hard Constraints (MUST Pass)

  Evaluate if the response meets MINIMUM VIABILITY. If ANY constraint fails,
  verdict MUST be REJECTED or REVISION_NEEDED.

  ### For Travel Planning:
  - [ ] Has specific destination or clear region (not vague "somewhere nice")
  - [ ] Itinerary is geographically feasible:
        * No intercontinental travel within 4 days unless explicitly requested
        * No more than 2 countries in 4 days for budget travel
        * No long-haul flights (>8h) combined with intense activities same day
  - [ ] Budget breakdown provided:
        * Flights cost estimate
        * Accommodation per night
        * Activities total
        * Food budget
        * Local transport
  - [ ] Timeline is realistic:
        * Includes travel time between locations
        * Reasonable activity density (not 5 activities per day)

  ### For Code Tasks:
  - [ ] Code has no syntax errors
  - [ ] Handles edge cases mentioned in requirements
  - [ ] No obvious security vulnerabilities (SQL injection, XSS, etc.)
  - [ ] Has error handling for critical operations

  ### For Information Gathering:
  - [ ] Sources are cited (if using websearch)
  - [ ] Information is relevant to the question
  - [ ] No contradictory statements

  ## Layer B: Quality Scoring (1-10)

  Only evaluate quality if Layer A passes:
  - Clarity and presentation (2 points)
  - Completeness (3 points)
  - User experience (2 points)
  - Efficiency (2 points)
  - Additional value (1 point)

  ## Output Format (JSON):
  {
    "hard_constraints_passed": true/false,
    "failed_constraints": ["constraint that failed", ...],
    "quality_score": 8,
    "verdict": "APPROVED|REVISION_NEEDED|REJECTED",
    "needs_revision": false,
    "issues_found": ["minor issue 1", "minor issue 2"],
    "feedback": "Detailed feedback for improvement"
  }

  ## Decision Rules:
  - hard_constraints_passed = false -> verdict = REJECTED
  - hard_constraints_passed = true AND quality_score >= 7 -> verdict = APPROVED
  - hard_constraints_passed = true AND quality_score < 7 -> verdict = REVISION_NEEDED

  CRITICAL: Never approve a response that fails hard constraints,
  regardless of how well-written it is.

review: |
  Review the following execution result:

  Task: {task}
  Result: {result}

  Evaluate using the two-layer criteria above.
  Return ONLY valid JSON, no additional text.
```

2. 修改 `agents/reviewer.py` 處理邏輯:
```python
async def execute(self, context: TaskContext) -> ExecutionResult:
    # ... 現有代碼 ...

    # Parse review result
    try:
        review_json = json.loads(review_response)
    except json.JSONDecodeError:
        # Fallback if not valid JSON
        review_json = self._extract_json(review_response)

    # ========== NEW: Hard Constraint Enforcement ==========
    hard_constraints_passed = review_json.get("hard_constraints_passed", True)

    if not hard_constraints_passed:
        logger.warning(
            f"[Reviewer] Hard constraints failed: "
            f"{review_json.get('failed_constraints', [])}"
        )
        # Force rejection
        review_json["needs_revision"] = True
        review_json["verdict"] = "REJECTED"

        # If it was APPROVED, override it
        if review_json.get("verdict") == "APPROVED":
            logger.error(
                "[Reviewer] CRITICAL: LLM approved despite failed constraints. "
                "Overriding to REJECTED."
            )
            review_json["verdict"] = "REJECTED"
    # ========== END: Hard Constraint Enforcement ==========

    # ... 返回結果
```

**驗證方式**:
```bash
# 測試案例：刻意給不合理的旅遊規劃
pytest tests/integration/test_reviewer_hard_fail.py
```

**估計工時**: 10 分鐘

---

### Tier 1 總結

**三個改動，核心問題解決 80%**:
1. ask_user 工具 -> 系統「能問」
2. Clarification Gate -> 系統「會問」
3. Hard-Fail Rubric -> 系統「會擋」

**總工時**: 35 分鐘
**立即效果**: 從「自嗨 agent」變成「會問問題的 agent」

---

### Tier 2: 短期改進（本週能完成）

#### 2.1 Tool-Use Policy（強制工具使用規則）

**目標**: 特定任務類型必須使用特定工具

**實施步驟**:

1. 在 `router/llm_analyzer.py` 的 `_decide_routing` 加入 policy:
```python
def _decide_routing(self, refinement: Dict[str, Any], context: TaskContext) -> RoutingDecision:
    # ... 現有邏輯 ...

    # ========== NEW: Tool-Use Policy ==========
    intent_type = refinement.get("intent_type", "task_execution")

    # Define required tools by intent type
    tool_policy = {
        "planning": {
            "required_tools": ["websearch", "ask_user"],  # At least one
            "min_tool_calls": 1,
            "rationale": "Planning requires either information gathering or clarification"
        },
        "information_gathering": {
            "required_tools": ["websearch"],
            "min_tool_calls": 1,
            "rationale": "Information gathering requires external search"
        },
        "task_execution": {
            "suggested_tools": ["python_execute", "shell", "file_write"],
            "min_tool_calls": 0,  # Not required, but suggested
            "rationale": "Task execution often requires code or file operations"
        }
    }

    policy = tool_policy.get(intent_type, {})
    if policy:
        metadata["tool_policy"] = policy
        logger.info(f"[Tool Policy] Applied for {intent_type}: {policy.get('rationale')}")
    # ========== END: Tool-Use Policy ==========

    return RoutingDecision(
        # ... 現有欄位 ...
        metadata=metadata
    )
```

2. 在 `agents/executor.py` 的 `_execute_react` 檢查 policy:
```python
# 在 ReAct loop 結束時（第 216 行 "No tool calls requested" 之後）
if not tool_call_requests:
    # Check tool policy before finishing
    tool_policy = context.metadata.get("tool_policy", {})
    required_tools = tool_policy.get("required_tools", [])
    min_calls = tool_policy.get("min_tool_calls", 0)

    # Check if minimum tool calls were made
    if min_calls > 0 and len(all_tool_calls) < min_calls:
        # Check if any required tool was used
        used_tools = {tc.name for tc in all_tool_calls}
        required_used = any(rt in used_tools for rt in required_tools) if required_tools else True

        if not required_used:
            logger.warning(
                f"[Tool Policy] Violation: Required tools {required_tools} not used. "
                f"Only {len(all_tool_calls)} tool calls made (min: {min_calls})"
            )

            # Inject enforcement prompt
            enforcement_msg = {
                "role": "system",
                "content": (
                    f"POLICY REQUIREMENT: This task requires using at least one of: {required_tools}. "
                    f"You have not made any tool calls yet. "
                    f"Rationale: {tool_policy.get('rationale', 'Required for task type')}. "
                    f"Please make the necessary tool call(s) before finishing."
                )
            }
            local_messages.append(enforcement_msg)

            # Continue loop instead of breaking
            continue

    logger.info("No tool calls requested. Finishing ReAct loop.")
    break
```

**驗證方式**:
```bash
# 測試案例
pytest tests/integration/test_tool_policy.py

# 手動測試
python main.py
>>> 規劃日本旅遊

# 預期：應該觸發 websearch 或 ask_user
```

**估計工時**: 20 分鐘

---

#### 2.2 結構化計劃（參考 OpenManus PlanningTool）

**目標**: Plan 從文字變成可驗證的數據結構

**實施步驟**:

1. 定義計劃 schema (`core/types.py`):
```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class PlanStepStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"

@dataclass
class PlanStep:
    """Single step in execution plan"""
    description: str
    required_info: List[str] = None  # <- 關鍵：明確需要什麼資訊
    validation_criteria: str = ""    # <- 關鍵：如何驗證完成
    status: PlanStepStatus = PlanStepStatus.NOT_STARTED
    notes: str = ""

    def is_ready(self) -> bool:
        """Check if step has all required information"""
        return not self.required_info or len(self.required_info) == 0

    def can_execute(self) -> bool:
        """Check if step can be executed"""
        return self.is_ready() and self.status == PlanStepStatus.NOT_STARTED

@dataclass
class StructuredPlan:
    """Structured execution plan"""
    plan_id: str
    title: str
    steps: List[PlanStep]
    missing_info: List[str] = None  # <- 關鍵：計劃級別缺失資訊
    ready_to_execute: bool = False  # <- 關鍵：是否可以執行

    def get_next_step(self) -> Optional[PlanStep]:
        """Get next executable step"""
        for step in self.steps:
            if step.can_execute():
                return step
        return None

    def progress_percentage(self) -> float:
        """Calculate completion percentage"""
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.status == PlanStepStatus.COMPLETED)
        return (completed / len(self.steps)) * 100
```

2. 修改 `prompts/planner.yaml` 要求 JSON 輸出:
```yaml
system: |
  You are a planning expert. Create structured, executable plans.

  CRITICAL RULES:
  1. If information is MISSING, list it in "missing_info" and set "ready_to_execute" to false
  2. Each step must specify "required_info" - what data is needed to execute it
  3. Each step must have "validation_criteria" - how to verify it's done correctly

  Output Format (JSON only, no markdown):
  {
    "title": "Brief plan title",
    "steps": [
      {
        "description": "Clear step description",
        "required_info": ["departure_city", "travel_date"],
        "validation_criteria": "Flight booking confirmed with receipt"
      }
    ],
    "missing_info": ["departure_city", "travel_date", "budget_breakdown"],
    "ready_to_execute": false
  }

  EXAMPLES:

  Example 1 - Missing Info:
  User: "Plan a trip to Japan"
  Output: {
    "title": "Japan Travel Planning",
    "steps": [...],
    "missing_info": ["departure_city", "travel_dates", "budget", "interests"],
    "ready_to_execute": false
  }

  Example 2 - Complete Info:
  User: "Plan a 4-day trip to Kyoto from Taipei, March 15-18, budget $2000, interested in temples and food"
  Output: {
    "title": "Kyoto 4-Day Cultural Tour",
    "steps": [...],
    "missing_info": [],
    "ready_to_execute": true
  }

planning: |
  Create an execution plan for: {task}

  Return ONLY valid JSON following the schema above.
```

3. 修改 `agents/planner.py` 解析與驗證:
```python
async def execute(self, context: TaskContext) -> ExecutionResult:
    # ... 現有代碼 ...

    # Parse JSON plan
    try:
        plan_json = json.loads(plan_response)
    except json.JSONDecodeError:
        plan_json = self._extract_json(plan_response)

    # ========== NEW: Plan Validation ==========
    ready = plan_json.get("ready_to_execute", False)
    missing_info = plan_json.get("missing_info", [])

    if not ready and missing_info:
        logger.warning(f"[Planner] Plan not ready: missing {missing_info}")

        return ExecutionResult(
            success=False,
            response=json.dumps(plan_json, indent=2),
            error="PLAN_INCOMPLETE",
            metadata={
                "plan": plan_json,
                "missing_info": missing_info,
                "needs_clarification": True
            }
        )
    # ========== END: Plan Validation ==========

    # Convert JSON to StructuredPlan object
    structured_plan = StructuredPlan(
        plan_id=f"plan_{int(time.time())}",
        title=plan_json["title"],
        steps=[
            PlanStep(**step) if isinstance(step, dict) else PlanStep(description=step)
            for step in plan_json.get("steps", [])
        ],
        missing_info=missing_info,
        ready_to_execute=ready
    )

    return ExecutionResult(
        success=True,
        response=str(plan_json.get("title", "Plan created")),
        metadata={
            "plan": structured_plan,  # <- 結構化 plan
            "plan_json": plan_json,   # <- 原始 JSON（相容性）
            "steps_count": len(structured_plan.steps)
        }
    )
```

**驗證方式**:
```bash
pytest tests/unit/test_structured_plan.py
```

**估計工時**: 30 分鐘

---

### Tier 2 總結

**兩個改動，提升系統可靠性**:
1. Tool-Use Policy -> 特定任務強制使用工具
2. 結構化計劃 -> Plan 可驗證、可追蹤

**總工時**: 50 分鐘
**效果**: 從「靠 prompt 祈禱」變成「有系統保證」

---

### Tier 3: 長期優化（系統性改善）

#### 3.1 類似 OpenManus 的 Flow Factory 模式

**目標**: 明確化執行模式選擇

**設計**:
```python
# core/orchestration.py
class OrchestrationMode(Enum):
    """Execution modes with different strictness levels"""
    FAST = "fast"          # System 1: Skip clarification, trust model
    STRICT = "strict"      # System 2: Force clarification when needed
    INTERACTIVE = "interactive"  # Allow mid-execution ask_user
    AUTONOMOUS = "autonomous"    # For API mode, no user interaction

class MultiAgentOrchestrator:
    def __init__(self, kernel, mode: OrchestrationMode = OrchestrationMode.STRICT):
        self.kernel = kernel
        self.mode = mode
        # ...

    async def orchestrate(self, context: TaskContext, ...) -> ExecutionResult:
        # Apply mode-specific behavior
        if self.mode == OrchestrationMode.FAST:
            # Skip clarification gate
            pass
        elif self.mode == OrchestrationMode.STRICT:
            # Apply all gates
            pass
```

**使用方式**:
```python
# main.py
orchestrator = MultiAgentOrchestrator(
    kernel,
    mode=OrchestrationMode.STRICT  # 預設嚴格模式
)

# 或讓用戶選擇
if args.fast:
    mode = OrchestrationMode.FAST
```

**估計工時**: 1 小時

---

#### 3.2 Event-Driven Clarification

**目標**: 把「需要澄清」當作 Event，解耦邏輯

**設計**（參考 OpenManus 的 `events/step_event.py`）:

```python
# core/events.py
from dataclasses import dataclass
from typing import List, Callable, Any
from enum import Enum

class EventType(Enum):
    CLARIFICATION_NEEDED = "clarification_needed"
    TOOL_POLICY_VIOLATION = "tool_policy_violation"
    HARD_CONSTRAINT_FAILED = "hard_constraint_failed"
    PLAN_INCOMPLETE = "plan_incomplete"

@dataclass
class ClarificationEvent:
    """Event raised when clarification is needed"""
    questions: List[str]
    context: str
    priority: str  # "required" | "optional"
    source: str    # Which component raised this (analyzer, planner, executor)

@dataclass
class PolicyViolationEvent:
    """Event raised when tool policy is violated"""
    required_tools: List[str]
    tools_used: List[str]
    policy_type: str

class EventBus:
    """Simple event bus for decoupled communication"""

    def __init__(self):
        self.handlers: Dict[EventType, List[Callable]] = {}

    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to an event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    async def publish(self, event_type: EventType, event_data: Any):
        """Publish an event to all subscribers"""
        if event_type not in self.handlers:
            return

        for handler in self.handlers[event_type]:
            await handler(event_data)
```

**使用方式**:
```python
# core/kernel.py
class Kernel:
    def __init__(self):
        self.event_bus = EventBus()

        # Subscribe to clarification events
        self.event_bus.subscribe(
            EventType.CLARIFICATION_NEEDED,
            self._handle_clarification
        )

    async def _handle_clarification(self, event: ClarificationEvent):
        """Handle clarification requests"""
        if event.priority == "required":
            # Block execution, ask user
            pass
        else:
            # Log as optional, continue
            pass

# router/llm_analyzer.py
if refinement.get('key_questions'):
    # Instead of just logging
    await kernel.event_bus.publish(
        EventType.CLARIFICATION_NEEDED,
        ClarificationEvent(
            questions=refinement['key_questions'],
            context=refinement['refined_goal'],
            priority="required" if ambiguity == "high" else "optional",
            source="analyzer"
        )
    )
```

**估計工時**: 2 小時

---

#### 3.3 參考 OpenManus 的 Session Management

OpenManus 有 workspace/session 管理（`app/agent/base.py` 第 212-246 行）:
- `SessionManager` 追蹤執行狀態
- `TaskClassifier` 自動分類任務
- Workspace 隔離（避免污染）

**你的系統已經有 workspace.py**（untracked file），可以整合。

**估計工時**: 3 小時

---

### Tier 3 總結

**系統性改善**:
1. OrchestrationMode -> 使用者可選嚴格程度
2. Event-Driven -> 解耦 clarification 邏輯
3. Session Management -> 追蹤與隔離

**總工時**: 6 小時
**效果**: 從「單次執行」變成「可配置、可追蹤的系統」

---

## 實施路線圖

### Week 1: Critical Fixes（Tier 1）
```
Day 1:
- [ ] 實施 ask_user 工具（10min）
- [ ] 實施 Clarification Gate（15min）
- [ ] 測試 clarification flow（15min）

Day 2:
- [ ] 實施 Reviewer Hard-Fail Rubric（10min）
- [ ] 測試 hard constraint 檢核（20min）
- [ ] 整合測試（30min）

Deliverable: 系統會問問題、會擋不合理輸出
```

---

### Week 2: Policy Enforcement（Tier 2）
```
Day 3-4:
- [ ] 實施 Tool-Use Policy（20min）
- [ ] 測試 policy enforcement（30min）
- [ ] 定義 Plan schema（30min）
- [ ] 實施結構化 Plan（1h）
- [ ] 整合測試（1h）

Deliverable: 計劃可驗證、工具使用有規則
```

---

### Week 3-4: System Enhancement（Tier 3）
```
Week 3:
- [ ] OrchestrationMode 設計與實施（1h）
- [ ] EventBus 基礎架構（2h）
- [ ] Event-driven clarification（1h）

Week 4:
- [ ] Session Management 整合（3h）
- [ ] 端到端測試（2h）
- [ ] 文檔更新（1h）

Deliverable: 完整的可配置、可追蹤系統
```

---

## 關鍵設計決策

### 1. 是否採用 OpenManus 的四層繼承？

**決定**: ❌ 不採用

**理由**:
- 現有三層架構已足夠（Router -> Orchestrator -> Agents）
- OpenManus 的四層繼承沒有帶來額外價值，反而增加複雜度
- 遵循 Linus 原則：「複雜性是萬惡之源」

---

### 2. 是否需要完整的 PlanningFlow？

**決定**: ⚠️ 部分採用

**採用**:
- 結構化計劃（JSON + status tracking）
- 步驟狀態機（not_started -> in_progress -> completed）

**不採用**:
- 獨立的 Flow 類（現有 Orchestrator 已足夠）
- 過於細緻的步驟管理（YAGNI - You Ain't Gonna Need It）

---

### 3. ask_user 應該是工具還是系統功能？

**決定**: ✅ 兩者都要

**工具層** (`tools/builtin/ask_user.py`):
- Agent 可以在 ReAct loop 中主動調用
- 靈活，model 決定何時問

**系統層** (`core/orchestration.py` 的 Clarification Gate):
- 強制性檢查（ambiguity gate）
- 保證關鍵資訊不缺失

---

### 4. 是否需要 Event-Driven 架構？

**決定**: 🔄 Tier 3 考慮

**現階段**:
- 先用直接的 if/else gate（Tier 1-2）
- 簡單、可維護

**未來**:
- 如果 clarification 邏輯變複雜（多種 trigger）
- 才引入 EventBus 解耦

**理由**: 遵循 Linus 實用主義 - "Theory and practice sometimes clash. Theory loses."

---

## 與 OpenManus 的核心差異總結

### 架構哲學

| 面向 | OpenManus | Core Agentic Brain |
|------|-----------|-------------------|
| **設計風格** | All-in-one agent | Multi-agent orchestration |
| **複雜度控制** | 工具豐富但無 routing | 有 routing 但缺 gating |
| **擴展性** | MCP 為核心 | 內建工具為核心 + 可選 MCP |
| **用戶互動** | 有工具但無 policy | 缺工具也缺 policy |

---

### 學習重點

**從 OpenManus 學習**:
1. ✅ 把 clarification 當工具（`ask_human`）
2. ✅ 計劃有狀態追蹤（`step_statuses`）
3. ✅ 工具集中管理（`ToolCollection`）

**不要學的**:
1. ❌ 四層繼承的 agent 設計
2. ❌ 缺少 routing 邏輯（單一 flow 處理所有任務）
3. ❌ 缺少 reviewer 機制

---

### 保持現有優勢

**已優於 OpenManus 的設計**:
1. ✅ LLM-based routing（雙階段分析）
2. ✅ System 1/2 分離
3. ✅ Reviewer 品質檢核
4. ✅ 三層清晰架構（無過度抽象）

**需要加強的**:
1. ❌ Gate 機制（有檢測無行動）
2. ❌ Tool policy（無強制規則）
3. ❌ Plan 結構化（純文字無法驗證）

---

## 風險評估

### 技術風險

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|----------|
| ask_user 在非互動環境失效 | 高 | 中 | 提供 mock mode 與 auto mode |
| 結構化 plan 破壞現有流程 | 低 | 高 | 向後相容檢查（支援文字 plan） |
| Clarification gate 拖慢簡單任務 | 中 | 低 | 提供 fast mode（跳過 gate） |
| Hard-fail rubric 過於嚴格 | 中 | 中 | 可配置的 rubric 嚴格程度 |

---

### 相容性考量

**向後相容策略**:
```python
# 在 Orchestrator 中
if isinstance(plan, dict):
    # New: Structured plan
    structured_plan = StructuredPlan.from_dict(plan)
elif isinstance(plan, str):
    # Legacy: Text plan (fallback to current behavior)
    logger.warning("Using legacy text plan (consider upgrading)")
    structured_plan = StructuredPlan.from_text(plan)
```

---

## 測試計劃

### Tier 1 測試（Critical Path）

```bash
# Test 1: ask_user tool
pytest tests/unit/test_ask_user.py

# Test 2: Clarification gate
pytest tests/integration/test_clarification_gate.py
# Expected: ambiguity=medium -> request clarification before execution

# Test 3: Reviewer hard-fail
pytest tests/integration/test_reviewer_hard_fail.py
# Expected: Geographically impossible itinerary -> REJECTED
```

---

### Tier 2 測試（Policy & Structure）

```bash
# Test 4: Tool policy
pytest tests/integration/test_tool_policy.py
# Expected: travel planning without websearch/ask_user -> retry with tools

# Test 5: Structured plan
pytest tests/unit/test_structured_plan.py
# Expected: Plan with missing_info -> ready_to_execute = false
```

---

### 端到端測試案例

#### Case 1: 模糊請求（應該 clarify）
```
Input: "規劃旅遊"
Expected Flow:
1. Analyzer detects high ambiguity
2. Clarification Gate blocks execution
3. Returns clarification questions to user
4. User provides info
5. Execution proceeds

Pass Criteria:
- No execution before clarification
- Questions are relevant and specific (max 3)
```

---

#### Case 2: 完整請求（直接執行）
```
Input: "規劃4天京都旅遊，從台北出發，3/15-3/18，預算$2000，喜歡寺廟和美食"
Expected Flow:
1. Analyzer detects low ambiguity
2. Skip clarification gate
3. Planner creates structured plan with ready_to_execute=true
4. Executor follows plan
5. Reviewer checks hard constraints (pass)

Pass Criteria:
- No unnecessary clarification
- Plan includes budget breakdown
- Itinerary is geographically feasible
```

---

#### Case 3: 不合理輸出（應該 reject）
```
Input: "規劃4天環遊世界"
Expected Flow:
1. Executor might produce 4-continent itinerary
2. Reviewer checks hard constraints
3. Fails: "No intercontinental travel within 4 days"
4. Verdict: REJECTED
5. Triggers revision

Pass Criteria:
- Reviewer correctly identifies infeasibility
- Provides clear feedback for revision
- Does NOT approve despite high quality score
```

---

## 成功指標

### 量化指標

**Before (當前系統)**:
- Clarification rate: 0% (never asks)
- Tool usage in planning tasks: ~0% (observed from log)
- Reviewer rejection rate: ~0% (approves everything)
- User trust: Low (produces unrealistic plans)

**After (Tier 1 完成)**:
- Clarification rate: 70%+ (medium/high ambiguity)
- Tool usage in planning tasks: 80%+ (policy enforcement)
- Reviewer rejection rate: 30%+ (hard constraints)
- User trust: High (asks when unsure)

**After (Tier 2 完成)**:
- Plan validation: 100% (structured plans only)
- Policy compliance: 95%+ (required tools used)
- Execution traceability: 100% (step status tracking)

---

### 質化指標

**使用者體驗**:
- "Agent 會問我問題了" (vs "Agent 瞎猜一通")
- "行程是合理的" (vs "4天跨3洲")
- "我知道進度到哪" (vs "不知道它在幹嘛")

**開發者體驗**:
- "Debug 變容易" (有結構化 plan 與 event log)
- "行為可預測" (有 policy 與 gate)
- "容易加新 policy" (基於 intent_type)

---

## 附錄：關鍵代碼片段

### A1: OpenManus ask_human 工具（原始設計）

```python
# legacy/OpenManus/app/tool/ask_human.py
class AskHuman(BaseTool):
    name: str = "ask_human"
    description: str = "Use this tool to ask human for help."
    parameters: str = {
        "type": "object",
        "properties": {
            "inquire": {
                "type": "string",
                "description": "The question you want to ask human.",
            }
        },
        "required": ["inquire"],
    }

    async def execute(self, inquire: str) -> str:
        return input(f"""Bot: {inquire}\n\nYou: """).strip()
```

**優點**: 簡單、直接、可用
**缺點**: 無 context、無 options、無 validation

---

### A2: OpenManus PlanningTool（結構化計劃）

```python
# legacy/OpenManus/app/tool/planning.py
plan = {
    "plan_id": plan_id,
    "title": title,
    "steps": steps,
    "step_statuses": ["not_started"] * len(steps),
    "step_notes": [""] * len(steps),
}
```

**優點**: 可追蹤、可驗證
**缺點**: 缺少 required_info 與 validation_criteria

---

### A3: OpenManus ToolCallAgent think 方法

```python
# legacy/OpenManus/app/agent/toolcall.py (第 39-136 行)
async def think(self) -> bool:
    # Get response with tool options
    response = await self.llm.ask_tool(
        messages=self.messages,
        system_msgs=[...],
        tools=self.available_tools.to_params(),
        tool_choice=self.tool_choices,
    )

    # Handle different tool_choices modes
    if self.tool_choices == ToolChoice.NONE:
        # No tools allowed
        return bool(content)

    if self.tool_choices == ToolChoice.REQUIRED and not self.tool_calls:
        return True  # Will fail in act()

    if self.tool_choices == ToolChoice.AUTO and not self.tool_calls:
        return bool(content)  # <- 關鍵：有 content 就認為 OK
```

**學習點**: `ToolChoice.REQUIRED` 選項
**問題**: AUTO 模式下模型可以不用工具

---

## 總結：從分析到行動

### 三個前提問題的答案

1. **這是個真問題還是臆想出來的？**
   ✅ 真問題。旅遊規劃的 log 證實：系統會產出地理上不可能的行程。

2. **有更簡單的方法嗎？**
   ✅ 有。不需要重寫架構，只需要加 3 個 gate（35 分鐘）。

3. **會破壞什麼嗎？**
   ⚠️ Clarification gate 會讓簡單任務變慢 -> 提供 fast mode 解決。

---

### 最短路徑（如果只改一個地方）

**改這裡**:
`core/orchestration.py` 的 `_execute_orchestrated` 開頭，加入：
```python
# If ambiguity detected, block and request clarification
if context.metadata.get("ambiguity_level") in {"medium", "high"}:
    return ExecutionResult(
        success=False,
        response="Clarification needed: " + str(context.metadata.get("key_questions")),
        error="CLARIFICATION_NEEDED"
    )
```

**10 行代碼，解決 50% 的問題**。

---

### 終極口訣

**從 OpenManus 學到的三件事**:
1. 計劃要有結構（JSON + 狀態）
2. ask_user 要當工具（一等公民）
3. 發現問題要行動（不是只 log）

**不要學的三件事**:
1. 四層繼承（過度抽象）
2. 無 Reviewer（你已有）
3. 無 Routing（你已有）

**一句話**:
> OpenManus 教你「把問題當第一公民」，你的系統教你「先分析再執行」。
> 把兩者結合：**分析出問題 -> 立即處理問題**，就是正確設計。

---

## 參考資料

- OpenManus Repository: `legacy/OpenManus/`
- 關鍵文件:
  - `app/tool/ask_human.py` - Clarification tool
  - `app/tool/planning.py` - Structured plan
  - `app/flow/planning.py` - Plan execution flow
  - `app/agent/toolcall.py` - Tool calling pattern
- 現有系統分析: 基於 2026-01-30 的執行 log

---

**下一步**: 執行 Tier 1（35 分鐘），立即見效。
