"""Orchestrator agent for coordinating complex multi-agent tasks."""

from typing import List, Dict, Any, Optional
from agents.base import BaseAgent
from core.types import TaskContext, ExecutionResult, AgentRole
from core.logger import logger


class OrchestratorAgent(BaseAgent):
    """Agent responsible for orchestrating complex multi-agent workflows."""

    def __init__(self):
        """Initialize orchestrator agent."""
        super().__init__("Orchestrator")
        self.agent_registry: Dict[str, Any] = {}

    def get_system_prompt(self) -> str:
        """Get orchestration-specific system prompt."""
        return """You are an orchestration specialist. Your role is to:
1. Coordinate multiple agents to achieve complex goals
2. Manage dependencies and sequencing between agents
3. Handle error recovery and retries
4. Optimize agent utilization and performance
5. Ensure end-to-end task completion

When orchestrating:
- Analyze the overall goal and break it into agent-specific tasks
- Determine optimal agent execution order
- Monitor progress and adjust strategy as needed
- Handle inter-agent communication
- Provide comprehensive progress updates

Format your orchestration plan with clear agent assignments and sequencing."""

    async def execute(self, context: TaskContext) -> ExecutionResult:
        """Orchestrate complex task execution across multiple agents."""
        logger.info("Orchestrating complex task", prompt=context.prompt[:50])

        try:
            # Create orchestration plan
            plan = await self._create_orchestration_plan(context)

            # Execute orchestration
            result = await self._execute_orchestration(plan, context)

            logger.info("Orchestration complete",
                       success=result["success"],
                       agents_used=len(result.get("agents_executed", [])))

            return ExecutionResult(
                success=result["success"],
                response=result["summary"],
                metadata={
                    "agent": "orchestrator",
                    "plan": plan,
                    "agents_executed": result.get("agents_executed", []),
                    "execution_time_ms": result.get("total_time_ms", 0)
                }
            )

        except Exception as e:
            logger.error("Orchestration failed", error=str(e))
            return ExecutionResult(
                success=False,
                response="",
                error=f"Orchestration failed: {str(e)}"
            )

    async def _create_orchestration_plan(self, context: TaskContext) -> Dict[str, Any]:
        """Create an orchestration plan for the task."""
        # Analyze task complexity and requirements
        plan_prompt = f"""Create an orchestration plan for this complex task:

Task: {context.prompt}

Please provide:
1. Overall strategy
2. Required agents and their roles:
   - Planner: For task decomposition
   - Executor: For implementation
   - Reviewer: For quality assurance
3. Execution sequence with dependencies
4. Success criteria
5. Risk mitigation strategies

Structure the plan for optimal parallel execution where possible."""

        plan_response = await self._call_llm(plan_prompt, context)

        # Parse into structured plan
        return self._parse_orchestration_plan(plan_response)

    def _parse_orchestration_plan(self, plan_text: str) -> Dict[str, Any]:
        """Parse orchestration plan into structured format."""
        plan = {
            "strategy": "multi-agent-collaboration",
            "phases": [],
            "agents": [],
            "dependencies": [],
            "success_criteria": []
        }

        # Simple parsing logic
        lines = plan_text.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Identify sections
            if "strategy" in line.lower():
                current_section = "strategy"
            elif "agent" in line.lower() or "role" in line.lower():
                current_section = "agents"
            elif "phase" in line.lower() or "step" in line.lower():
                current_section = "phases"
            elif "success" in line.lower() or "criteria" in line.lower():
                current_section = "success_criteria"

            # Add to appropriate section
            if current_section == "phases" and (line[0].isdigit() or line.startswith('-')):
                plan["phases"].append({
                    "description": line,
                    "agents": self._extract_agents_from_line(line)
                })
            elif current_section == "agents" and line.startswith('-'):
                agent_info = line.lstrip('-').strip()
                if ':' in agent_info:
                    agent_name, role = agent_info.split(':', 1)
                    plan["agents"].append({
                        "name": agent_name.strip(),
                        "role": role.strip()
                    })
            elif current_section == "success_criteria" and line.startswith('-'):
                plan["success_criteria"].append(line.lstrip('-').strip())

        return plan

    def _extract_agents_from_line(self, line: str) -> List[str]:
        """Extract agent names from a phase description."""
        agents = []
        agent_keywords = ["planner", "executor", "reviewer", "orchestrator"]

        line_lower = line.lower()
        for keyword in agent_keywords:
            if keyword in line_lower:
                agents.append(keyword)

        return agents

    async def _execute_orchestration(
        self, plan: Dict[str, Any], context: TaskContext
    ) -> Dict[str, Any]:
        """Execute the orchestration plan."""
        import time
        start_time = time.time()

        result = {
            "success": True,
            "agents_executed": [],
            "phase_results": [],
            "summary": ""
        }

        # Execute phases
        for i, phase in enumerate(plan.get("phases", [])):
            logger.info(f"Executing phase {i+1}: {phase.get('description', '')[:50]}")

            # Execute agents for this phase
            phase_result = await self._execute_phase(phase, context)
            result["phase_results"].append(phase_result)
            result["agents_executed"].extend(phase.get("agents", []))

            if not phase_result.get("success", False):
                result["success"] = False
                logger.warning(f"Phase {i+1} failed")
                break

        # Calculate total time
        result["total_time_ms"] = (time.time() - start_time) * 1000

        # Generate summary
        result["summary"] = self._generate_summary(plan, result)

        return result

    async def _execute_phase(
        self, phase: Dict[str, Any], context: TaskContext
    ) -> Dict[str, Any]:
        """Execute a single phase of the orchestration."""
        phase_result = {
            "success": True,
            "agents": phase.get("agents", []),
            "outputs": []
        }

        # For now, simulate agent execution
        # In real implementation, this would call actual agents
        for agent in phase.get("agents", []):
            logger.debug(f"Would execute agent: {agent}")
            phase_result["outputs"].append(f"{agent} completed")

        return phase_result

    def _generate_summary(self, plan: Dict[str, Any], result: Dict[str, Any]) -> str:
        """Generate a summary of the orchestration execution."""
        if result["success"]:
            return (
                f"Successfully orchestrated task using {len(result['agents_executed'])} agents "
                f"across {len(plan.get('phases', []))} phases. "
                f"Total execution time: {result.get('total_time_ms', 0):.2f}ms"
            )
        else:
            failed_phase = len([r for r in result["phase_results"] if not r.get("success", False)])
            return (
                f"Orchestration partially completed. "
                f"Failed at phase {failed_phase} of {len(plan.get('phases', []))}. "
                f"Agents executed: {', '.join(result['agents_executed'])}"
            )

    def register_agent(self, role: AgentRole, agent: Any):
        """Register an agent for orchestration."""
        self.agent_registry[role.value] = agent
        logger.info(f"Registered agent: {role.value}")

    def get_registered_agents(self) -> List[str]:
        """Get list of registered agents."""
        return list(self.agent_registry.keys())