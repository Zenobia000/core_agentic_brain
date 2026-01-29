"""Task executor for routing decisions."""

import asyncio
import time
from typing import Any, Dict, List, Optional
from core.types import ExecutionResult, RoutingDecision, TaskContext, AgentRole
from core.simple_logger import log


class RoutingExecutor:
    """Executes routing decisions by coordinating agents."""

    def __init__(self, agents: Optional[Dict[str, Any]] = None):
        """Initialize the routing executor."""
        self.agents = agents or {}
        self.strategies = {
            "direct": self._execute_direct,
            "sequential": self._execute_sequential,
            "orchestrated": self._execute_orchestrated
        }

    async def execute(self, decision: RoutingDecision, context: TaskContext) -> ExecutionResult:
        """Execute a routing decision."""
        start_time = time.time()
        log('info', summary="Executing routing decision", strategy=decision.strategy)

        try:
            # Get the appropriate strategy
            strategy_func = self.strategies.get(decision.strategy, self._execute_direct)

            # Execute the strategy
            result = await strategy_func(decision, context)

            # Add execution metadata
            execution_time = (time.time() - start_time) * 1000
            result.metadata["execution_time_ms"] = execution_time
            result.metadata["routing_strategy"] = decision.strategy

            log('info', summary="Routing execution complete ✓",
                       success=result.success,
                       execution_time_ms=execution_time)
            return result

        except Exception as e:
            log('error', summary="Routing execution failed", error=str(e))
            return ExecutionResult(
                success=False,
                response="",
                error=str(e),
                metadata={"strategy": decision.strategy}
            )

    async def _execute_direct(
        self, decision: RoutingDecision, context: TaskContext
    ) -> ExecutionResult:
        """Execute task directly with single agent."""
        log('debug', summary="Executing direct strategy")

        # Get the executor agent
        agent_role = decision.agents[0] if decision.agents else AgentRole.EXECUTOR
        agent = self._get_agent(agent_role)

        if not agent:
            return ExecutionResult(
                success=False,
                response="",
                error=f"Agent {agent_role.value} not available"
            )

        # Execute with the agent
        return await self._execute_with_agent(agent, context)

    async def _execute_sequential(
        self, decision: RoutingDecision, context: TaskContext
    ) -> ExecutionResult:
        """Execute task sequentially through multiple agents."""
        log('debug', summary="Executing sequential strategy")

        results = []
        current_context = context

        for agent_role in decision.agents:
            agent = self._get_agent(agent_role)
            if not agent:
                log('warning', summary=f"Agent {agent_role.value} not available, skipping")
                continue

            # Execute with current agent
            result = await self._execute_with_agent(agent, current_context)
            results.append(result)

            if not result.success:
                return result

            # Update context for next agent
            current_context.metadata["previous_result"] = result.response

        # Return the final result
        return results[-1] if results else ExecutionResult(
            success=False,
            response="",
            error="No agents executed"
        )

    async def _execute_orchestrated(
        self, decision: RoutingDecision, context: TaskContext
    ) -> ExecutionResult:
        """Execute task with orchestrated agent coordination."""
        log('debug', summary="Executing orchestrated strategy")

        # Get orchestrator if available
        orchestrator = self._get_agent(AgentRole.ORCHESTRATOR)

        if orchestrator:
            # Let orchestrator coordinate
            return await self._execute_with_agent(orchestrator, context)
        else:
            # Fall back to sequential execution
            log('warning', summary="Orchestrator not available, falling back to sequential")
            return await self._execute_sequential(decision, context)

    def _get_agent(self, role: AgentRole) -> Optional[Any]:
        """Get agent by role."""
        return self.agents.get(role.value)

    async def _execute_with_agent(self, agent: Any, context: TaskContext) -> ExecutionResult:
        """Execute task with a specific agent."""
        try:
            # Check if agent has execute method
            if hasattr(agent, 'execute'):
                if asyncio.iscoroutinefunction(agent.execute):
                    result = await agent.execute(context)
                else:
                    result = agent.execute(context)

                # If agent already returns ExecutionResult, return it directly
                if isinstance(result, ExecutionResult):
                    return result
                else:
                    # Otherwise wrap it
                    response = result
            else:
                # Fallback to calling agent directly
                response = str(agent(context.prompt))

            return ExecutionResult(
                success=True,
                response=response,
                metadata={"agent": str(agent.__class__.__name__)}
            )
        except Exception as e:
            log('error', summary="Agent execution failed", error=str(e))
            return ExecutionResult(
                success=False,
                response="",
                error=str(e)
            )