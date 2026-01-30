# Universal ReAct Architecture Design

## Problem Statement

ReAct (Reason + Act) pattern is universal, but domain knowledge is not.
Current issue: We hardcode domain logic (travel planning) into prompts.
Goal: Make the STRUCTURE universal while keeping domain knowledge PLUGGABLE.

---

## Core Insight

```
ReAct Loop = Engine (universal)
Domain Schema = Fuel (pluggable)
Validation Rules = Guardrails (pluggable)

Like Linux: Kernel is universal, drivers are specific.
```

---

## Proposed Architecture

### 1. Domain Schema System

```yaml
# schemas/travel.yaml
domain: travel_planning
version: "1.0"

# Phase 1: What MUST be known before planning?
intake:
  required_fields:
    - name: departure_city
      question: "從哪裡出發？"
      validation: "must be a valid city name"
    - name: travel_dates
      question: "什麼時候出發？（日期範圍）"
      validation: "must be valid date range"
    - name: budget_scope
      question: "預算範圍？（含機票嗎？總預算還是每人？）"
      validation: "must specify inclusion/exclusion"
    - name: travelers_count
      question: "幾個人？"
      validation: "must be positive integer"

  optional_fields:
    - name: dietary_restrictions
    - name: mobility_constraints
    - name: interests

# Phase 2: What tools are allowed in each phase?
tool_policy:
  intake_phase:
    allowed: [ask_user]
    purpose: "Gather required information"

  validation_phase:
    allowed: [websearch, ask_user]
    search_pattern: "specific queries only"
    examples:
      good: ["flight TPE to ROM March 15 price", "Amalfi hotel cost per night March"]
      bad: ["top travel destinations", "best places to visit"]

  execution_phase:
    allowed: [websearch, python, files]
    purpose: "Generate detailed plan with validated data"

# Phase 3: What must the output contain?
output_requirements:
  must_have:
    - budget_breakdown:
        fields: [flights, accommodation, activities, food, transport, total]
    - daily_itinerary:
        per_day: [morning, afternoon, evening, accommodation]
        per_activity: [what, where, when, cost, booking_required, transport_to_next]
    - logistics:
        fields: [visa_requirements, best_booking_time, weather_notes]

  quality_checks:
    - "No activity immediately after long flight (>6hrs)"
    - "Transport time between activities must be noted"
    - "Total cost must not exceed stated budget"

# Phase 4: Review criteria
review:
  hard_fail:
    - "Missing any required field from intake"
    - "Budget breakdown missing or doesn't match total"
    - "Physically impossible logistics"

  soft_fail:
    - "Missing backup options for weather-dependent activities"
    - "No local tips or insider recommendations"
```

```yaml
# schemas/code_task.yaml
domain: code_task
version: "1.0"

intake:
  required_fields:
    - name: task_description
      question: "What should the code do?"
    - name: target_language
      question: "What programming language?"
    - name: environment
      question: "Where will this run? (browser, server, CLI, etc.)"

  optional_fields:
    - name: existing_codebase
    - name: dependencies_allowed
    - name: performance_requirements

tool_policy:
  intake_phase:
    allowed: [ask_user, files]
  validation_phase:
    allowed: [websearch, files]
    purpose: "Check API docs, library compatibility"
  execution_phase:
    allowed: [python, files, websearch]
  testing_phase:
    allowed: [python, bash]
    purpose: "Run and verify the code works"

output_requirements:
  must_have:
    - working_code: "Must be syntactically valid"
    - usage_example: "How to run/use the code"
    - error_handling: "Common error cases handled"

  quality_checks:
    - "No hardcoded credentials"
    - "Input validation on user-provided data"
    - "Tests pass"
```

---

## Phase Controller (Universal)

```python
class PhaseController:
    """
    Universal phase controller that works with any domain schema.
    The ReAct loop runs WITHIN each phase, with phase-specific constraints.
    """

    PHASES = ["intake", "validation", "execution", "review"]

    async def run(self, context: TaskContext, schema: DomainSchema) -> ExecutionResult:
        """
        Run through all phases with domain-specific rules.
        """
        collected_info = {}

        # Phase 1: Intake
        intake_result = await self._run_phase(
            phase="intake",
            context=context,
            schema=schema,
            collected_info=collected_info
        )
        if not intake_result.complete:
            return intake_result  # Need more info from user

        collected_info.update(intake_result.data)

        # Phase 2: Validation
        validation_result = await self._run_phase(
            phase="validation",
            context=context,
            schema=schema,
            collected_info=collected_info
        )
        if not validation_result.feasible:
            return validation_result  # Plan is not feasible

        # Phase 3: Execution
        execution_result = await self._run_phase(
            phase="execution",
            context=context,
            schema=schema,
            collected_info=collected_info
        )

        # Phase 4: Review
        review_result = await self._run_phase(
            phase="review",
            context=context,
            schema=schema,
            execution_result=execution_result
        )

        if review_result.needs_revision:
            # Loop back to execution with feedback
            return await self._revision_loop(context, schema, review_result)

        return review_result

    async def _run_phase(self, phase: str, context: TaskContext,
                         schema: DomainSchema, **kwargs) -> PhaseResult:
        """
        Run ReAct loop within a single phase.
        Tools are restricted based on phase policy.
        """
        phase_config = schema.tool_policy[f"{phase}_phase"]
        allowed_tools = phase_config["allowed"]

        # Create phase-specific executor
        executor = PhaseExecutor(
            allowed_tools=allowed_tools,
            phase_purpose=phase_config.get("purpose", ""),
            max_iterations=10
        )

        return await executor.run(context, **kwargs)
```

---

## Tool Masking by Phase

```python
class PhaseExecutor:
    """
    Executor that only exposes tools allowed in current phase.
    """

    def __init__(self, allowed_tools: List[str], phase_purpose: str, max_iterations: int):
        self.allowed_tools = set(allowed_tools)
        self.phase_purpose = phase_purpose
        self.max_iterations = max_iterations

    def get_tool_definitions(self, all_tools: Dict) -> List[Dict]:
        """
        Filter tools based on phase policy.
        """
        return [
            tool_def for name, tool_def in all_tools.items()
            if name in self.allowed_tools
        ]

    def get_phase_prompt(self) -> str:
        """
        Add phase-specific instructions to system prompt.
        """
        return f"""
        ## Current Phase Purpose
        {self.phase_purpose}

        ## Available Tools (This Phase Only)
        You can ONLY use: {', '.join(self.allowed_tools)}

        ## Phase Completion
        Complete this phase before moving on.
        If you need tools not available in this phase,
        you must complete this phase first.
        """
```

---

## Schema-Driven Clarification Gate

```python
class SchemaDrivenGate:
    """
    Clarification gate that uses domain schema to determine required fields.
    """

    def check(self, context: TaskContext, schema: DomainSchema) -> GateResult:
        """
        Check if all required fields are present.
        """
        required = schema.intake.required_fields
        prompt_lower = context.prompt.lower()

        missing = []
        for field in required:
            if not self._field_present(field, prompt_lower):
                missing.append({
                    "name": field.name,
                    "question": field.question
                })

        if missing:
            return GateResult(
                passed=False,
                missing_fields=missing,
                message=self._format_questions(missing)
            )

        return GateResult(passed=True)

    def _field_present(self, field: FieldDef, prompt: str) -> bool:
        """
        Check if field is mentioned in prompt.
        Uses field-specific detection patterns.
        """
        # Could be keyword-based or use LLM for semantic matching
        patterns = field.detection_patterns or [field.name]
        return any(p in prompt for p in patterns)
```

---

## Why This Works

### 1. ReAct Engine Stays Universal
```
Think → Act → Observe → Loop
No domain knowledge in the engine itself.
```

### 2. Domain Knowledge is Declarative
```yaml
# Not code, just data
intake:
  required_fields:
    - name: departure_city
      question: "從哪裡出發？"
```

### 3. Tool Policy is Phase-Aware
```
Intake phase: Only ask_user (no searching yet)
Validation phase: Search for SPECIFIC data
Execution phase: Full tool access
```

### 4. Output Quality is Schema-Defined
```yaml
must_have:
  - budget_breakdown
  - daily_itinerary
  - logistics
```

---

## Implementation Roadmap

### Phase 1: Schema System (2-3 days)
- [ ] Define YAML schema format
- [ ] Create schema loader
- [ ] Implement 2-3 domain schemas (travel, code, research)

### Phase 2: Phase Controller (2-3 days)
- [ ] Implement PhaseController class
- [ ] Integrate with existing Orchestrator
- [ ] Add phase-based tool masking

### Phase 3: Schema-Driven Gate (1-2 days)
- [ ] Replace hardcoded clarification logic
- [ ] Use schema to determine required fields
- [ ] Field detection (keyword or semantic)

### Phase 4: Output Validation (1-2 days)
- [ ] Schema-driven output checking
- [ ] Integrate with Reviewer agent
- [ ] Quality score based on schema requirements

---

## Trade-offs

### Pros
- Truly universal ReAct engine
- Domain knowledge is config, not code
- Easy to add new domains (just add schema)
- Consistent behavior across domains

### Cons
- More complex initial setup
- Schema design requires domain expertise
- May over-constrain creative tasks
- Performance overhead for schema validation

---

## Linus's Take

```
"Make the common case simple, make the rare case possible."

Common case: Standard domain (travel, code, research)
→ Use pre-defined schema, works out of box

Rare case: New domain or creative task
→ Provide minimal schema, let model figure out more

The goal is NOT "one prompt fits all"
The goal is "one STRUCTURE fits all, content is pluggable"
```

---

## Example: How a Request Flows

```
User: "規劃旅遊 4天3夜 喜歡冒險"

1. Domain Detection
   → Matches "travel_planning" schema

2. Intake Phase (tools: ask_user only)
   → Schema says: need departure_city, travel_dates, budget_scope
   → Missing all three
   → ask_user: "請問：1. 從哪裡出發？2. 什麼時候？3. 預算多少（含機票嗎）？"

3. User provides: "台北出發 3/15-18 總預算4000美金含機票"

4. Validation Phase (tools: websearch, ask_user)
   → Search: "flight TPE to [candidate destinations] March 15 price"
   → Search: "adventure activities [destination] March weather"
   → Validate: Is $4000 enough for flight + hotel + activities?

5. Execution Phase (tools: all)
   → Generate detailed itinerary with:
     - Budget breakdown (per schema requirement)
     - Daily schedule (per schema requirement)
     - Booking instructions (per schema requirement)

6. Review Phase
   → Check against schema.output_requirements
   → Check against schema.review.hard_fail criteria
   → Pass or request revision
```

---

## Conclusion

**是否可行？** 是的，但不是「讓 ReAct 無限迭代」，而是「讓 ReAct 在正確的方向上迭代」。

**關鍵洞察：**
- Engine (ReAct) 可以通用
- Fuel (Domain Schema) 必須領域特定
- 但 Fuel 可以是 YAML config，不需要寫 code

這樣就達到了「通用架構 + 領域適配」的平衡。
