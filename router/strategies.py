"""
Routing strategies for different task types.
Defines how tasks are routed and executed.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.types import RouterDecision, TaskComplexity


class RoutingStrategy(ABC):
    """Abstract base class for routing strategies"""

    @abstractmethod
    def route(self, task: str, context: Optional[Dict] = None) -> RouterDecision:
        """Determine routing for task"""
        pass

    @abstractmethod
    def should_apply(self, task: str) -> bool:
        """Check if strategy applies to task"""
        pass


class SimpleTaskStrategy(RoutingStrategy):
    """Strategy for simple, direct tasks"""

    def route(self, task: str, context: Optional[Dict] = None) -> RouterDecision:
        """Route simple tasks to fast path"""
        return RouterDecision(
            complexity=TaskComplexity.SIMPLE,
            strategy="fast_path",
            reasoning="Simple task - direct tool execution"
        )

    def should_apply(self, task: str) -> bool:
        """Check if task is simple"""
        simple_keywords = ["list", "show", "get", "calculate", "what is"]
        return any(keyword in task.lower() for keyword in simple_keywords)


class ComplexTaskStrategy(RoutingStrategy):
    """Strategy for complex, multi-step tasks"""

    def route(self, task: str, context: Optional[Dict] = None) -> RouterDecision:
        """Route complex tasks to agent orchestration"""
        return RouterDecision(
            complexity=TaskComplexity.COMPLEX,
            strategy="agent_path",
            agents=["planner", "executor", "reviewer"],
            reasoning="Complex task requiring orchestration"
        )

    def should_apply(self, task: str) -> bool:
        """Check if task is complex"""
        complex_keywords = ["analyze", "design", "multiple", "coordinate", "research"]
        return any(keyword in task.lower() for keyword in complex_keywords)


class DataProcessingStrategy(RoutingStrategy):
    """Strategy for data processing tasks"""

    def route(self, task: str, context: Optional[Dict] = None) -> RouterDecision:
        """Route data tasks based on complexity"""
        if "large" in task.lower() or "batch" in task.lower():
            return RouterDecision(
                complexity=TaskComplexity.MODERATE,
                strategy="agent_path",
                agents=["executor"],
                reasoning="Data processing with single agent"
            )
        else:
            return RouterDecision(
                complexity=TaskComplexity.SIMPLE,
                strategy="fast_path",
                reasoning="Simple data operation"
            )

    def should_apply(self, task: str) -> bool:
        """Check if task involves data processing"""
        data_keywords = ["process", "transform", "convert", "parse", "extract"]
        return any(keyword in task.lower() for keyword in data_keywords)


class InteractiveStrategy(RoutingStrategy):
    """Strategy for interactive/conversational tasks"""

    def route(self, task: str, context: Optional[Dict] = None) -> RouterDecision:
        """Route interactive tasks"""
        return RouterDecision(
            complexity=TaskComplexity.SIMPLE,
            strategy="fast_path",
            reasoning="Interactive response - direct execution"
        )

    def should_apply(self, task: str) -> bool:
        """Check if task is interactive"""
        interactive_keywords = ["explain", "tell me", "help me", "how to"]
        return any(keyword in task.lower() for keyword in interactive_keywords)


class StrategyManager:
    """Manage and select routing strategies"""

    def __init__(self):
        self.strategies = [
            SimpleTaskStrategy(),
            ComplexTaskStrategy(),
            DataProcessingStrategy(),
            InteractiveStrategy()
        ]

    def select_strategy(self, task: str) -> RoutingStrategy:
        """Select appropriate strategy for task"""
        for strategy in self.strategies:
            if strategy.should_apply(task):
                return strategy

        # Default to simple strategy
        return SimpleTaskStrategy()

    def route(self, task: str, context: Optional[Dict] = None) -> RouterDecision:
        """Route task using selected strategy"""
        strategy = self.select_strategy(task)
        return strategy.route(task, context)