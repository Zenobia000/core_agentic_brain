"""
Agent Runtime - 增強的 Agent 執行引擎
====================================

提供標準化的執行循環和狀態機。
- Loop Engine: Plan → Decide → Act → Observe → Reflect
- Task Spec: 標準化任務規格
- Verifier: 任務驗證器
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TaskState(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_HUMAN = "waiting_human"


class TaskSpec(BaseModel):
    """任務規格 - 標準化任務輸入"""
    goal: str
    constraints: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    budget: Dict[str, Any] = Field(default_factory=lambda: {
        "max_tokens": 10000,
        "max_time_seconds": 300,
        "max_tool_calls": 50,
    })
    expected_output_type: str = "text"
    context: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 5
    deadline: Optional[datetime] = None


class StepResult(BaseModel):
    """步驟執行結果"""
    step_number: int
    step_type: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Any] = None
    success: bool = True
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    tokens_used: int = 0
    
    def complete(self, output: Any = None, error: Optional[str] = None) -> None:
        self.completed_at = datetime.now()
        if error:
            self.success = False
            self.error = error
        else:
            self.output_data = output


class VerificationResult(BaseModel):
    """驗證結果"""
    passed: bool = False
    criteria_results: Dict[str, bool] = Field(default_factory=dict)
    feedback: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)
    recommended_action: str = "continue"


class Verifier(ABC):
    """驗證器基類"""
    @abstractmethod
    async def verify(self, task_spec: TaskSpec, result: Any, context: Dict[str, Any]) -> VerificationResult:
        pass


class CriteriaBasedVerifier(Verifier):
    """基於標準的驗證器"""
    async def verify(self, task_spec: TaskSpec, result: Any, context: Dict[str, Any]) -> VerificationResult:
        verification = VerificationResult()
        
        if not task_spec.success_criteria:
            verification.passed = True
            return verification
        
        for criterion in task_spec.success_criteria:
            passed = False
            if isinstance(result, str):
                words = criterion.lower().split()
                passed = any(w in result.lower() for w in words if len(w) > 3)
            elif result is not None:
                passed = True
            verification.criteria_results[criterion] = passed
        
        verification.passed = all(verification.criteria_results.values())
        if not verification.passed:
            failed = [c for c, p in verification.criteria_results.items() if not p]
            verification.feedback = f"Failed criteria: {failed}"
            verification.recommended_action = "retry"
        
        return verification


class LoopEngine(BaseModel):
    """循環引擎 - 驅動 Plan → Act → Verify → Reflect"""
    
    current_state: TaskState = TaskState.CREATED
    current_step: int = 0
    task_spec: Optional[TaskSpec] = None
    steps: List[StepResult] = Field(default_factory=list)
    max_steps: int = 50
    max_retries: int = 3
    verifier: Optional[Verifier] = None
    on_state_change: Optional[Callable] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def _change_state(self, new_state: TaskState) -> None:
        old_state = self.current_state
        self.current_state = new_state
        if self.on_state_change:
            try:
                self.on_state_change(old_state, new_state)
            except Exception:
                pass
    
    def _record_step(self, step_type: str, input_data: Optional[Dict] = None) -> StepResult:
        self.current_step += 1
        step = StepResult(step_number=self.current_step, step_type=step_type, input_data=input_data)
        self.steps.append(step)
        return step
    
    async def run(
        self,
        task_spec: TaskSpec,
        plan_fn: Callable,
        act_fn: Callable,
        reflect_fn: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """執行任務循環"""
        self.task_spec = task_spec
        self.current_step = 0
        self.steps = []
        result = None
        retries = 0
        
        try:
            # 1. 規劃
            self._change_state(TaskState.PLANNING)
            plan_step = self._record_step("plan", {"goal": task_spec.goal})
            plan = await plan_fn(task_spec)
            plan_step.complete(plan)
            
            # 2. 執行循環
            self._change_state(TaskState.EXECUTING)
            
            while self.current_step < self.max_steps:
                act_step = self._record_step("act", {"plan": plan})
                try:
                    result = await act_fn(task_spec, plan)
                    act_step.complete(result)
                except Exception as e:
                    act_step.complete(error=str(e))
                    retries += 1
                    if retries >= self.max_retries:
                        self._change_state(TaskState.FAILED)
                        return {"success": False, "error": f"Max retries exceeded", "steps": [s.model_dump() for s in self.steps]}
                    continue
                
                # 驗證
                self._change_state(TaskState.VERIFYING)
                verification = await self._verify(result)
                
                if verification.passed:
                    break
                
                # 反思
                if reflect_fn:
                    self._change_state(TaskState.REFLECTING)
                    reflect_step = self._record_step("reflect")
                    reflection = await reflect_fn(task_spec, result, verification)
                    reflect_step.complete(reflection)
                    if isinstance(reflection, dict) and "updated_plan" in reflection:
                        plan = reflection["updated_plan"]
                
                if verification.recommended_action == "abort":
                    self._change_state(TaskState.FAILED)
                    return {"success": False, "error": "Verification aborted", "steps": [s.model_dump() for s in self.steps]}
                
                retries += 1
                if retries >= self.max_retries:
                    break
                
                self._change_state(TaskState.EXECUTING)
            
            self._change_state(TaskState.COMPLETED)
            return {"success": True, "result": result, "steps": [s.model_dump() for s in self.steps], "total_steps": self.current_step}
            
        except Exception as e:
            self._change_state(TaskState.FAILED)
            return {"success": False, "error": str(e), "steps": [s.model_dump() for s in self.steps]}
    
    async def _verify(self, result: Any) -> VerificationResult:
        if not self.verifier or not self.task_spec:
            return VerificationResult(passed=True)
        return await self.verifier.verify(self.task_spec, result, {"steps": self.steps})


class AgentRuntime(BaseModel):
    """Agent Runtime - 整合所有組件"""
    
    loop_engine: LoopEngine = Field(default_factory=LoopEngine)
    context_manager: Optional[Any] = None
    policy_engine: Optional[Any] = None
    ops_plane: Optional[Any] = None
    tool_gateway: Optional[Any] = None
    skill_registry: Optional[Any] = None
    name: str = "agent_runtime"
    
    class Config:
        arbitrary_types_allowed = True
    
    async def execute_task(self, task_spec: TaskSpec, agent: Any) -> Dict[str, Any]:
        """執行任務"""
        trace = None
        if self.ops_plane:
            trace = self.ops_plane.start_trace(name=f"task_{task_spec.goal[:30]}")
        
        try:
            async def plan_fn(spec: TaskSpec):
                return {"goal": spec.goal, "steps": []}
            
            async def act_fn(spec: TaskSpec, plan: Dict):
                if hasattr(agent, "run"):
                    return await agent.run(spec.goal)
                return None
            
            result = await self.loop_engine.run(task_spec=task_spec, plan_fn=plan_fn, act_fn=act_fn)
            
            if self.ops_plane:
                self.ops_plane.log_audit(
                    event_type="task_execution",
                    event_name=task_spec.goal[:50],
                    actor=self.name,
                    success=result.get("success", False),
                )
            
            return result
        finally:
            if self.ops_plane and trace:
                self.ops_plane.end_trace(trace.trace_id)


__all__ = [
    "TaskState", "TaskSpec", "StepResult", "VerificationResult",
    "Verifier", "CriteriaBasedVerifier", "LoopEngine", "AgentRuntime",
]
