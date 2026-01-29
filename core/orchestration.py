"""
Multi-Agent Orchestration - ReAct 架構實現
參考 CrewAI 和 LangChain 的設計理念
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from core.types import TaskContext, ExecutionResult, AgentRole, TaskComplexity
from core.communication import Message, MessageType
from core.logger import logger, timer
import json


def log(level: str, summary: str = "", **kwargs):
    """Compatibility wrapper for old log function."""
    msg = f"[Orchestrator] {summary}"
    if kwargs:
        details = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{msg} ({details})" if summary else f"[Orchestrator] {details}"
    getattr(logger, level)(msg)


@dataclass
class AgentMessage:
    """代理間的訊息"""
    from_agent: str
    to_agent: str
    content: Any
    message_type: str  # thought, action, observation, result
    metadata: Dict = None


class ExecutionStrategy(Enum):
    """執行策略"""
    DIRECT = "direct"  # 直接執行
    SEQUENTIAL = "sequential"  # 順序執行
    ORCHESTRATED = "orchestrated"  # 協調執行
    PARALLEL = "parallel"  # 並行執行
    REACT = "react"  # ReAct 模式


class MultiAgentOrchestrator:
    """多代理協調器 - 實現 ReAct 架構

    ReAct 架構：
    1. Thought (思考) - Planner 分析任務
    2. Action (行動) - Executor 執行任務
    3. Observation (觀察) - Reviewer 審查結果
    4. Iterate (迭代) - 根據觀察決定是否需要重新規劃
    """

    def __init__(self, kernel):
        """初始化協調器

        Args:
            kernel: 系統核心，用於獲取代理和工具
        """
        self.kernel = kernel
        self.execution_history = []
        self.max_iterations = 3  # 最大迭代次數

    async def orchestrate(
        self,
        context: TaskContext,
        strategy: ExecutionStrategy,
        agents: List[AgentRole]
    ) -> ExecutionResult:
        """協調多代理執行任務

        Args:
            context: 任務上下文
            strategy: 執行策略
            agents: 參與的代理列表

        Returns:
            執行結果
        """
        log('info', summary=f"Orchestrating with strategy: {strategy.value}",
            agents=[a.value for a in agents])

        # 根據策略選擇執行方法
        if strategy == ExecutionStrategy.DIRECT:
            return await self._execute_direct(context, agents)
        elif strategy == ExecutionStrategy.SEQUENTIAL:
            return await self._execute_sequential(context, agents)
        elif strategy == ExecutionStrategy.ORCHESTRATED:
            return await self._execute_orchestrated(context, agents)
        elif strategy == ExecutionStrategy.REACT:
            return await self._execute_react(context, agents)
        else:
            return await self._execute_direct(context, agents)

    async def _execute_direct(
        self,
        context: TaskContext,
        agents: List[AgentRole]
    ) -> ExecutionResult:
        """直接執行 - 只使用 Executor"""
        executor = self.kernel.get_or_create_agent("executor")
        with timer('execution.direct'):
            result = await executor.handle(Message(
                type=MessageType.PROMPT,
                content=context.prompt,
                source="orchestrator",
                target="agent.executor",
                metadata={"context": context}
            ))
        return result

    async def _execute_sequential(
        self,
        context: TaskContext,
        agents: List[AgentRole]
    ) -> ExecutionResult:
        """順序執行 - Planner -> Executor"""
        logger.info("=" * 50)
        logger.info(f"[Orchestrator] Starting sequential execution: {[a.value for a in agents]}")

        # Step 1: Planning
        if AgentRole.PLANNER in agents:
            planner = self.kernel.get_or_create_agent("planner")
            with timer('execution.planning'):
                plan_result = await planner.handle(Message(
                    type=MessageType.PROMPT,
                    content=context.prompt,
                    source="orchestrator",
                    target="agent.planner",
                    metadata={"context": context}
                ))

            # 將計劃添加到上下文
            if hasattr(plan_result, 'response'):
                context.metadata["plan"] = plan_result.response
                logger.info(f"[Orchestrator] Planning complete (plan_length={len(plan_result.response)})")

        # Step 2: Execution
        executor = self.kernel.get_or_create_agent("executor")
        with timer('execution.executing'):
            result = await executor.handle(Message(
                type=MessageType.PROMPT,
                content=context.prompt,
                source="orchestrator",
                target="agent.executor",
                metadata={"context": context}
            ))

        return result

    async def _execute_orchestrated(
        self,
        context: TaskContext,
        agents: List[AgentRole]
    ) -> ExecutionResult:
        """協調執行 - Planner -> Executor -> Reviewer (with iteration)"""
        logger.info("=" * 50)
        logger.info("[Orchestrator] Starting orchestrated execution (Planner -> Executor -> Reviewer)")
        logger.info(f"[Orchestrator] Agents: {[a.value for a in agents]}")

        execution_chain = []
        max_revisions = 2  # Maximum revision iterations
        current_revision = 0

        # Step 1: Planning
        if AgentRole.PLANNER in agents:
            logger.info("-" * 30)
            logger.info("[Step 1/3] PLANNER - Creating execution plan")
            planner = self.kernel.get_or_create_agent("planner")
            with timer('orchestration.planning'):
                plan_result = await planner.handle(Message(
                    type=MessageType.PROMPT,
                    content=context.prompt,
                    source="orchestrator",
                    target="agent.planner",
                    metadata={"context": context}
                ))

            plan_text = plan_result.response if hasattr(plan_result, 'response') else str(plan_result)
            execution_chain.append({
                "agent": "planner",
                "status": "completed",
                "summary": plan_text[:100] + "..." if len(plan_text) > 100 else plan_text
            })
            context.metadata["plan"] = plan_result.response if hasattr(plan_result, 'response') else str(plan_result)
            logger.info("[Step 1/3] PLANNER - Plan created successfully")

        # Step 2 & 3: Execution -> Review -> (Iterate if needed)
        exec_result = None
        final_approved = False

        while current_revision <= max_revisions and not final_approved:
            iteration_label = f"(revision {current_revision})" if current_revision > 0 else "(initial)"

            # Step 2: Execution
            logger.info("-" * 30)
            logger.info(f"[Step 2/3] EXECUTOR - Executing task {iteration_label}")
            executor = self.kernel.get_or_create_agent("executor")

            # If this is a revision, add reviewer feedback to context
            if current_revision > 0 and "reviewer_feedback" in context.metadata:
                logger.info(f"[Step 2/3] EXECUTOR - Applying reviewer feedback for revision {current_revision}")
                context.metadata["revision_instructions"] = (
                    f"Previous execution was reviewed and needs improvement.\n"
                    f"Feedback: {context.metadata['reviewer_feedback']}\n"
                    f"Please address the issues and provide an improved response."
                )

            with timer(f'orchestration.executing{iteration_label}'):
                exec_result = await executor.handle(Message(
                    type=MessageType.PROMPT,
                    content=context.prompt,
                    source="orchestrator",
                    target="agent.executor",
                    metadata={"context": context}
                ))

            exec_text = exec_result.response if hasattr(exec_result, 'response') else str(exec_result)
            execution_chain.append({
                "agent": "executor",
                "status": "completed",
                "iteration": current_revision,
                "summary": exec_text[:100] + "..." if len(exec_text) > 100 else exec_text
            })
            logger.info(f"[Step 2/3] EXECUTOR - Execution completed {iteration_label}")

            # Step 3: Review
            if AgentRole.REVIEWER in agents:
                logger.info("-" * 30)
                logger.info(f"[Step 3/3] REVIEWER - Reviewing execution {iteration_label}")
                reviewer = self.kernel.get_or_create_agent("reviewer")
                review_context = context.copy() if hasattr(context, 'copy') else context
                review_context.metadata["execution_result"] = exec_result

                with timer(f'orchestration.reviewing{iteration_label}'):
                    review_result = await reviewer.handle(Message(
                        type=MessageType.PROMPT,
                        content=f"Review this execution: {exec_result.response if hasattr(exec_result, 'response') else exec_result}",
                        source="orchestrator",
                        target="agent.reviewer",
                        metadata={"context": review_context}
                    ))

                review_text = review_result.response if hasattr(review_result, 'response') else str(review_result)

                # Check if revision is needed
                needs_revision = False
                if hasattr(review_result, 'metadata'):
                    needs_revision = review_result.metadata.get('needs_revision', False) or \
                                    review_result.metadata.get('needs_improvement', False)
                    verdict = review_result.metadata.get('verdict', 'UNKNOWN')
                    quality_score = review_result.metadata.get('quality_score', 'N/A')
                else:
                    verdict = 'UNKNOWN'
                    quality_score = 'N/A'

                execution_chain.append({
                    "agent": "reviewer",
                    "status": "completed",
                    "iteration": current_revision,
                    "verdict": verdict,
                    "needs_revision": needs_revision,
                    "summary": review_text[:100] + "..." if len(review_text) > 100 else review_text
                })

                verdict_emoji = "✅" if verdict == "APPROVED" else "🔄" if verdict == "REVISION_NEEDED" else "❌"
                logger.info(f"[Step 3/3] REVIEWER - Verdict: {verdict_emoji} {verdict} (Quality: {quality_score})")

                if needs_revision and current_revision < max_revisions:
                    logger.info(f"[Step 3/3] REVIEWER - Revision required, starting revision {current_revision + 1}/{max_revisions}")
                    context.metadata["reviewer_feedback"] = review_text
                    current_revision += 1
                else:
                    final_approved = True
                    if needs_revision:
                        logger.warning(f"[Step 3/3] REVIEWER - Still suggests improvement but max revisions ({max_revisions}) reached")
            else:
                # No reviewer, just mark as complete
                logger.info("[Step 3/3] REVIEWER - Skipped (no reviewer in agent list)")
                final_approved = True

        # 構建最終結果
        logger.info("=" * 50)
        logger.info(f"[Orchestrator] Execution completed: revisions={current_revision}, approved={final_approved}")

        return ExecutionResult(
            success=True,
            response=exec_result.response if hasattr(exec_result, 'response') else str(exec_result),
            metadata={
                "strategy": "orchestrated",
                "execution_chain": execution_chain,
                "agents_used": [a.value for a in agents],
                "total_revisions": current_revision,
                "final_approved": final_approved
            }
        )

    async def _execute_react(
        self,
        context: TaskContext,
        agents: List[AgentRole]
    ) -> ExecutionResult:
        """ReAct 模式執行 - 思考-行動-觀察循環"""
        logger.info("=" * 50)
        logger.info(f"[Orchestrator] Starting ReAct execution (max {self.max_iterations} iterations)")

        react_chain = []
        current_context = context
        final_result = None

        for iteration in range(self.max_iterations):
            logger.info("-" * 30)
            logger.info(f"[ReAct] Iteration {iteration + 1}/{self.max_iterations}")

            # Thought: 使用 Planner 思考
            if AgentRole.PLANNER in agents:
                planner = self.kernel.get_or_create_agent("planner")
                thought_prompt = f"""
                Iteration {iteration + 1}:
                Task: {context.prompt}
                Previous actions: {json.dumps(react_chain, indent=2) if react_chain else 'None'}

                What should we do next?
                """

                with timer(f'react.thought.{iteration}'):
                    thought_result = await planner.handle(Message(
                        type=MessageType.PROMPT,
                        content=thought_prompt,
                        source="orchestrator",
                        target="agent.planner",
                        metadata={"context": current_context}
                    ))

                thought = thought_result.response if hasattr(thought_result, 'response') else str(thought_result)
                thought_preview = thought[:100] + "..." if len(thought) > 100 else thought
                logger.info(f"[ReAct] Thought: {thought_preview}")

                # Action: 使用 Executor 執行
                executor = self.kernel.get_or_create_agent("executor")
                with timer(f'react.action.{iteration}'):
                    action_result = await executor.handle(Message(
                        type=MessageType.PROMPT,
                        content=thought,
                        source="orchestrator",
                        target="agent.executor",
                        metadata={"context": current_context, "plan": thought}
                    ))

                action = action_result.response if hasattr(action_result, 'response') else str(action_result)
                action_preview = action[:100] + "..." if len(action) > 100 else action
                logger.info(f"[ReAct] Action: {action_preview}")

                # Observation: 使用 Reviewer 觀察
                if AgentRole.REVIEWER in agents:
                    reviewer = self.kernel.get_or_create_agent("reviewer")
                    with timer(f'react.observation.{iteration}'):
                        observation_result = await reviewer.handle(Message(
                            type=MessageType.PROMPT,
                            content=f"Observe and evaluate: {action}",
                            source="orchestrator",
                            target="agent.reviewer",
                            metadata={"context": current_context, "action": action}
                        ))

                    observation = observation_result.response if hasattr(observation_result, 'response') else str(observation_result)
                    observation_preview = observation[:100] + "..." if len(observation) > 100 else observation
                    logger.info(f"[ReAct] Observation: {observation_preview}")

                    # 記錄 ReAct 鏈（使用摘要避免過長輸出）
                    react_chain.append({
                        "iteration": iteration + 1,
                        "thought_summary": thought[:100] + "..." if len(thought) > 100 else thought,
                        "action_summary": action[:100] + "..." if len(action) > 100 else action,
                        "observation_summary": observation[:100] + "..." if len(observation) > 100 else observation
                    })

                    # 檢查是否完成
                    if "task completed" in observation.lower() or "success" in observation.lower():
                        logger.info(f"[ReAct] Task completed in iteration {iteration + 1}")
                        final_result = action
                        break
                else:
                    # 沒有 Reviewer，直接使用 Action 結果
                    react_chain.append({
                        "iteration": iteration + 1,
                        "thought_summary": thought[:100] + "..." if len(thought) > 100 else thought,
                        "action_summary": action[:100] + "..." if len(action) > 100 else action
                    })
                    final_result = action
                    break
            else:
                # 沒有 Planner，退化到直接執行
                return await self._execute_direct(context, agents)

        # 構建最終結果
        return ExecutionResult(
            success=True,
            response=final_result or "ReAct execution completed",
            metadata={
                "strategy": "react",
                "react_chain": react_chain,
                "iterations": len(react_chain),
                "agents_used": [a.value for a in agents]
            }
        )


class CrewStyleOrchestrator(MultiAgentOrchestrator):
    """CrewAI 風格的協調器

    特點：
    - 代理有明確的角色定義
    - 支持代理間的委派（delegation）
    - 任務可以分解為子任務
    """

    async def delegate_task(
        self,
        task: str,
        from_agent: str,
        to_agent: str,
        context: TaskContext
    ) -> Any:
        """委派任務給其他代理"""
        logger.info(f"[CrewOrchestrator] Delegating task from {from_agent} to {to_agent}")

        target_agent = self.kernel.get_or_create_agent(to_agent)
        result = await target_agent.handle(Message(
            type=MessageType.PROMPT,
            content=task,
            source=f"agent.{from_agent}",
            target=f"agent.{to_agent}",
            metadata={"context": context, "delegated": True}
        ))

        return result


class LangChainStyleOrchestrator(MultiAgentOrchestrator):
    """LangChain 風格的協調器

    特點：
    - Chain of Thought
    - 支持工具調用
    - Memory 管理
    """

    def __init__(self, kernel):
        super().__init__(kernel)
        self.memory = []  # 簡單的記憶體

    async def chain_of_thought(
        self,
        context: TaskContext,
        agents: List[AgentRole]
    ) -> ExecutionResult:
        """Chain of Thought 執行"""
        logger.info("[LangChainOrchestrator] Chain of Thought execution starting")

        chain = []
        current_output = context.prompt

        for agent_role in agents:
            agent = self.kernel.get_or_create_agent(agent_role.value.lower())

            # 將前一個輸出作為下一個輸入
            result = await agent.handle(Message(
                type=MessageType.PROMPT,
                content=current_output,
                source="orchestrator",
                target=f"agent.{agent_role.value.lower()}",
                metadata={"context": context, "chain": chain}
            ))

            output = result.response if hasattr(result, 'response') else str(result)
            chain.append({
                "agent": agent_role.value,
                "input": current_output,
                "output": output
            })

            current_output = output

        # 保存到記憶體
        self.memory.append({
            "task": context.prompt,
            "chain": chain,
            "result": current_output
        })

        return ExecutionResult(
            success=True,
            response=current_output,
            metadata={
                "strategy": "chain_of_thought",
                "chain": chain,
                "memory_size": len(self.memory)
            }
        )