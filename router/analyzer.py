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
                "display", "tell", "explain", "describe", "誰", "什麼", "列出"
            ],
            TaskComplexity.MODERATE: [
                "analyze", "compare", "summarize", "calculate",
                "create", "generate", "modify", "update", "build",
                "implement", "分析", "比較", "創建", "計算"
            ],
            TaskComplexity.COMPLEX: [
                "design", "architect", "optimize", "refactor",
                "integrate", "debug", "troubleshoot", "migrate",
                "scale", "orchestrate", "設計", "優化", "整合", "調試"
            ]
        }

    async def analyze(self, context: TaskContext) -> RoutingDecision:
        """Analyze task context and return routing decision."""
        log('info', summary="Analyzing task", prompt=context.prompt[:100] if len(context.prompt) > 100 else context.prompt)

        # Determine complexity
        complexity = self._determine_complexity(context)
        log('info', summary=f"Task complexity: {complexity.value}",
            prompt_length=len(context.prompt),
            tools_count=len(context.tools))

        # Select strategy based on complexity
        strategy = self._select_strategy(complexity)
        log('info', summary=f"Routing strategy: {strategy}")

        # Determine required agents
        agents = self._determine_agents(complexity, context)
        agent_names = [a.value for a in agents]
        log('info', summary=f"Selected agents: {', '.join(agent_names)}",
            agent_count=len(agents))

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

        # Count keyword matches for each complexity level
        complex_matches = [kw for kw in self.complexity_keywords[TaskComplexity.COMPLEX]
                          if kw in prompt_lower]
        moderate_matches = [kw for kw in self.complexity_keywords[TaskComplexity.MODERATE]
                           if kw in prompt_lower]
        simple_matches = [kw for kw in self.complexity_keywords[TaskComplexity.SIMPLE]
                         if kw in prompt_lower]

        # Log keyword matches
        if complex_matches:
            log('debug', summary=f"Complex keywords found: {complex_matches}")
        if moderate_matches:
            log('debug', summary=f"Moderate keywords found: {moderate_matches}")
        if simple_matches:
            log('debug', summary=f"Simple keywords found: {simple_matches}")

        # Prioritize complex indicators
        if complex_matches:
            return TaskComplexity.COMPLEX

        # Then moderate indicators
        if moderate_matches:
            return TaskComplexity.MODERATE

        # Check task length and structure for complexity
        if len(context.prompt) > 200 or context.prompt.count('\n') > 3:
            log('debug', summary="Long or structured prompt detected, elevating to moderate")
            return TaskComplexity.MODERATE

        # Check if multiple tools are needed
        if len(context.tools) > 2:
            log('debug', summary=f"Multiple tools needed ({len(context.tools)}), elevating to moderate")
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