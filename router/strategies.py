"""Routing strategies for different task types."""

import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from core.types import TaskContext, RoutingDecision, ExecutionResult
from core.simple_logger import log


class RoutingStrategy(ABC):
    """Abstract base class for routing strategies."""

    @abstractmethod
    async def route(self, context: TaskContext) -> RoutingDecision:
        """Route the task based on strategy."""
        pass

    @abstractmethod
    async def execute(self, decision: RoutingDecision, context: TaskContext) -> ExecutionResult:
        """Execute the routing decision."""
        pass


class SimpleRoutingStrategy(RoutingStrategy):
    """Simple routing for basic tasks."""

    async def route(self, context: TaskContext) -> RoutingDecision:
        """Route simple tasks directly to executor."""
        from core.types import TaskComplexity, AgentRole

        log('debug', summary="Applying simple routing strategy")
        return RoutingDecision(
            strategy="direct",
            agents=[AgentRole.EXECUTOR],
            complexity=TaskComplexity.SIMPLE,
            reasoning="Simple task routed directly to executor"
        )

    async def execute(self, decision: RoutingDecision, context: TaskContext) -> ExecutionResult:
        """Execute simple task directly."""
        log('debug', summary="Executing simple routing")
        # Implementation delegated to executor
        return ExecutionResult(
            success=True,
            response="Simple execution placeholder",
            metadata={"strategy": "simple"}
        )


class AdaptiveRoutingStrategy(RoutingStrategy):
    """Adaptive routing that learns from past executions."""

    def __init__(self):
        """Initialize adaptive strategy."""
        self.history: List[Dict[str, Any]] = []
        self.patterns: Dict[str, str] = {}

    async def route(self, context: TaskContext) -> RoutingDecision:
        """Route based on learned patterns."""
        from core.types import TaskComplexity, AgentRole

        log('debug', summary="Applying adaptive routing strategy")

        # Check if we've seen similar tasks
        pattern = self._identify_pattern(context)
        if pattern in self.patterns:
            strategy = self.patterns[pattern]
            log('info', summary=f"Found matching pattern, using {strategy} strategy")
        else:
            # Default to moderate complexity for unknown patterns
            strategy = "sequential"

        return RoutingDecision(
            strategy=strategy,
            agents=[AgentRole.PLANNER, AgentRole.EXECUTOR],
            complexity=TaskComplexity.MODERATE,
            reasoning=f"Adaptive routing selected {strategy} based on task pattern"
        )

    async def execute(self, decision: RoutingDecision, context: TaskContext) -> ExecutionResult:
        """Execute and learn from the result."""
        log('debug', summary="Executing adaptive routing")

        # Record execution for learning
        self.history.append({
            "context": context.prompt,
            "decision": decision.strategy,
            "timestamp": time.time()
        })

        return ExecutionResult(
            success=True,
            response="Adaptive execution placeholder",
            metadata={"strategy": "adaptive", "history_size": len(self.history)}
        )

    def _identify_pattern(self, context: TaskContext) -> str:
        """Identify task pattern for routing."""
        # Simple pattern: first word of prompt
        words = context.prompt.split()
        return words[0].lower() if words else "unknown"


class PriorityRoutingStrategy(RoutingStrategy):
    """Priority-based routing for urgent tasks."""

    def __init__(self, priority_threshold: float = 0.7):
        """Initialize priority strategy."""
        self.priority_threshold = priority_threshold

    async def route(self, context: TaskContext) -> RoutingDecision:
        """Route based on task priority."""
        from core.types import TaskComplexity, AgentRole

        log('debug', summary="Applying priority routing strategy")

        # Determine priority
        priority = self._calculate_priority(context)
        log('info', summary=f"Task priority: {priority}")

        if priority > self.priority_threshold:
            # High priority: use orchestrated approach
            strategy = "orchestrated"
            agents = [AgentRole.ORCHESTRATOR, AgentRole.PLANNER,
                     AgentRole.EXECUTOR, AgentRole.REVIEWER]
            complexity = TaskComplexity.COMPLEX
        else:
            # Normal priority: sequential approach
            strategy = "sequential"
            agents = [AgentRole.PLANNER, AgentRole.EXECUTOR]
            complexity = TaskComplexity.MODERATE

        return RoutingDecision(
            strategy=strategy,
            agents=agents,
            complexity=complexity,
            reasoning=f"Priority routing ({priority:.2f}) selected {strategy}"
        )

    async def execute(self, decision: RoutingDecision, context: TaskContext) -> ExecutionResult:
        """Execute with priority handling."""
        log('debug', summary="Executing priority routing")
        return ExecutionResult(
            success=True,
            response="Priority execution placeholder",
            metadata={"strategy": "priority"}
        )

    def _calculate_priority(self, context: TaskContext) -> float:
        """Calculate task priority score."""
        priority_keywords = ["urgent", "critical", "important", "asap", "emergency"]
        prompt_lower = context.prompt.lower()

        score = 0.5  # Base priority
        for keyword in priority_keywords:
            if keyword in prompt_lower:
                score += 0.2

        return min(score, 1.0)  # Cap at 1.0