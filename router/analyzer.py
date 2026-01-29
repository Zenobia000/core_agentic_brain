"""Task analyzer for intelligent routing."""

from typing import List, Optional
from core.types import TaskContext, TaskComplexity, RoutingDecision, AgentRole
from core.simple_logger import log


class TaskAnalyzer:
    """Analyzes tasks to determine complexity and routing strategy."""

    def __init__(self):
        """Initialize the task analyzer."""
        self.complexity_keywords = {
            TaskComplexity.SIMPLE: [
                "what", "when", "where", "who", "list", "show",
                "display", "tell", "explain", "describe"
            ],
            TaskComplexity.MODERATE: [
                "analyze", "compare", "summarize", "calculate",
                "create", "generate", "modify", "update"
            ],
            TaskComplexity.COMPLEX: [
                "design", "architect", "optimize", "refactor",
                "integrate", "debug", "troubleshoot", "migrate"
            ]
        }

    async def analyze(self, context: TaskContext) -> RoutingDecision:
        """Analyze task context and return routing decision."""
        log('info', summary="Analyzing task", prompt=context.prompt)

        # Determine complexity
        complexity = self._determine_complexity(context)
        log('debug', summary="Determined complexity", complexity=complexity.value)

        # Select strategy based on complexity
        strategy = self._select_strategy(complexity)
        log('debug', summary="Selected strategy", strategy=strategy)

        # Determine required agents
        agents = self._determine_agents(complexity, context)
        log('debug', summary="Selected agents", agents=[a.value for a in agents])

        # Generate reasoning
        reasoning = self._generate_reasoning(complexity, strategy, agents)

        decision = RoutingDecision(
            strategy=strategy,
            agents=agents,
            complexity=complexity,
            reasoning=reasoning,
            metadata={"analyzed_prompt": context.prompt}
        )

        log('info', summary="Task analysis complete", decision=str(decision))
        return decision

    def _determine_complexity(self, context: TaskContext) -> TaskComplexity:
        """Determine task complexity based on keywords and context."""
        prompt_lower = context.prompt.lower()

        # Check for complex indicators first
        if any(kw in prompt_lower for kw in self.complexity_keywords[TaskComplexity.COMPLEX]):
            return TaskComplexity.COMPLEX

        # Check for moderate indicators
        if any(kw in prompt_lower for kw in self.complexity_keywords[TaskComplexity.MODERATE]):
            return TaskComplexity.MODERATE

        # Check if multiple tools are needed
        if len(context.tools) > 2:
            return TaskComplexity.MODERATE

        # Default to simple
        return TaskComplexity.SIMPLE

    def _select_strategy(self, complexity: TaskComplexity) -> str:
        """Select routing strategy based on complexity."""
        strategies = {
            TaskComplexity.SIMPLE: "direct",
            TaskComplexity.MODERATE: "sequential",
            TaskComplexity.COMPLEX: "orchestrated"
        }
        return strategies.get(complexity, "direct")

    def _determine_agents(
        self, complexity: TaskComplexity, context: TaskContext
    ) -> List[AgentRole]:
        """Determine which agents are needed based on complexity."""
        if complexity == TaskComplexity.SIMPLE:
            return [AgentRole.EXECUTOR]
        elif complexity == TaskComplexity.MODERATE:
            return [AgentRole.PLANNER, AgentRole.EXECUTOR]
        else:  # COMPLEX
            agents = [
                AgentRole.PLANNER,
                AgentRole.EXECUTOR,
                AgentRole.REVIEWER
            ]
            # Add orchestrator for very complex tasks
            if "integrate" in context.prompt.lower() or "architect" in context.prompt.lower():
                agents.insert(0, AgentRole.ORCHESTRATOR)
            return agents

    def _generate_reasoning(
        self, complexity: TaskComplexity, strategy: str, agents: List[AgentRole]
    ) -> str:
        """Generate human-readable reasoning for the routing decision."""
        agent_names = [a.value for a in agents]
        return (
            f"Task classified as {complexity.value} complexity. "
            f"Using {strategy} routing strategy with agents: {', '.join(agent_names)}. "
            f"This approach ensures optimal task execution based on the requirements."
        )