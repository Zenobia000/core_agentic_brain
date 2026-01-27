"""
Task analyzer for routing decisions.
Analyzes task complexity and determines execution strategy.
"""

import re
from typing import Dict, List, Optional
from core.types import TaskComplexity, RouterDecision


class TaskAnalyzer:
    """Analyze tasks to determine routing strategy"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._init_patterns()

    def _init_patterns(self):
        """Initialize complexity detection patterns"""
        self.simple_patterns = [
            r"^(list|show|display|get)\s+",
            r"^(calculate|compute)\s+\d+",
            r"^(read|write|save)\s+file",
            r"^execute\s+(python|code)",
            r"^what\s+(is|are)\s+",
        ]

        self.complex_patterns = [
            r"(analyze|research|investigate)",
            r"(design|architect|plan)\s+system",
            r"(multiple|several|various)\s+",
            r"(coordinate|orchestrate|manage)",
            r"step[s]?\s+\d+",
        ]

    def analyze(self, task: str, context: Optional[List] = None) -> RouterDecision:
        """
        Analyze task and return routing decision.

        Args:
            task: User task description
            context: Optional conversation context

        Returns:
            RouterDecision with complexity and strategy
        """
        task_lower = task.lower().strip()

        # Check for simple patterns
        if self._is_simple_task(task_lower):
            return RouterDecision(
                complexity=TaskComplexity.SIMPLE,
                strategy="fast_path",
                reasoning="Direct tool execution sufficient"
            )

        # Check for complex patterns
        if self._is_complex_task(task_lower):
            return RouterDecision(
                complexity=TaskComplexity.COMPLEX,
                strategy="agent_path",
                agents=["planner", "executor", "reviewer"],
                reasoning="Multi-agent coordination required"
            )

        # Default to moderate complexity
        return RouterDecision(
            complexity=TaskComplexity.MODERATE,
            strategy="agent_path",
            agents=["executor"],
            reasoning="Single agent execution"
        )

    def _is_simple_task(self, task: str) -> bool:
        """Check if task matches simple patterns"""
        return any(re.match(pattern, task) for pattern in self.simple_patterns)

    def _is_complex_task(self, task: str) -> bool:
        """Check if task matches complex patterns"""
        return any(re.search(pattern, task) for pattern in self.complex_patterns)

    def get_required_tools(self, task: str) -> List[str]:
        """Determine required tools for task"""
        tools = []
        task_lower = task.lower()

        if "python" in task_lower or "code" in task_lower:
            tools.append("python")
        if "file" in task_lower or "read" in task_lower or "write" in task_lower:
            tools.append("files")
        if "browse" in task_lower or "web" in task_lower:
            tools.append("browser")
        if "shell" in task_lower or "command" in task_lower:
            tools.append("shell")

        return tools if tools else ["python"]  # Default to python tool