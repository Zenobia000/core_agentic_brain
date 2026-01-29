"""
Multi-Agent Orchestration - ReAct 架構實現
參考 CrewAI 和 LangChain 的設計理念
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from core.types import TaskContext, ExecutionResult, AgentRole, TaskComplexity
from core.communication import Message, MessageType
from core.simple_logger import log, timer
import json


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
        log('info', summary="Sequential execution starting")

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
                log('info', summary="Planning complete", plan_length=len(plan_result.response))

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
        """協調執行 - Planner -> Executor -> Reviewer"""
        log('info', summary="Orchestrated execution starting")

        execution_chain = []

        # Step 1: Planning
        if AgentRole.PLANNER in agents:
            planner = self.kernel.get_or_create_agent("planner")
            with timer('orchestration.planning'):
                plan_result = await planner.handle(Message(
                    type=MessageType.PROMPT,
                    content=context.prompt,
                    source="orchestrator",
                    target="agent.planner",
                    metadata={"context": context}
                ))

            execution_chain.append({
                "agent": "planner",
                "result": plan_result.response if hasattr(plan_result, 'response') else str(plan_result)
            })
            context.metadata["plan"] = plan_result.response if hasattr(plan_result, 'response') else str(plan_result)
            log('info', summary="Planning phase complete")

        # Step 2: Execution
        executor = self.kernel.get_or_create_agent("executor")
        with timer('orchestration.executing'):
            exec_result = await executor.handle(Message(
                type=MessageType.PROMPT,
                content=context.prompt,
                source="orchestrator",
                target="agent.executor",
                metadata={"context": context}
            ))

        execution_chain.append({
            "agent": "executor",
            "result": exec_result.response if hasattr(exec_result, 'response') else str(exec_result)
        })
        log('info', summary="Execution phase complete")

        # Step 3: Review
        if AgentRole.REVIEWER in agents:
            reviewer = self.kernel.get_or_create_agent("reviewer")
            review_context = context.copy() if hasattr(context, 'copy') else context
            review_context.metadata["execution_result"] = exec_result

            with timer('orchestration.reviewing'):
                review_result = await reviewer.handle(Message(
                    type=MessageType.PROMPT,
                    content=f"Review this execution: {exec_result.response if hasattr(exec_result, 'response') else exec_result}",
                    source="orchestrator",
                    target="agent.reviewer",
                    metadata={"context": review_context}
                ))

            execution_chain.append({
                "agent": "reviewer",
                "result": review_result.response if hasattr(review_result, 'response') else str(review_result)
            })
            log('info', summary="Review phase complete")

            # 如果審查發現問題，可以迭代
            if hasattr(review_result, 'metadata') and review_result.metadata.get('needs_improvement'):
                log('info', summary="Review suggests improvement needed")
                # 這裡可以實現迭代邏輯

        # 構建最終結果
        return ExecutionResult(
            success=True,
            response=exec_result.response if hasattr(exec_result, 'response') else str(exec_result),
            metadata={
                "strategy": "orchestrated",
                "execution_chain": execution_chain,
                "agents_used": [a.value for a in agents]
            }
        )

    async def _execute_react(
        self,
        context: TaskContext,
        agents: List[AgentRole]
    ) -> ExecutionResult:
        """ReAct 模式執行 - 思考-行動-觀察循環"""
        log('info', summary="ReAct execution starting")

        react_chain = []
        current_context = context
        final_result = None

        for iteration in range(self.max_iterations):
            log('info', summary=f"ReAct iteration {iteration + 1}")

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
                log('debug', summary=f"Thought: {thought[:100]}...")

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
                log('debug', summary=f"Action: {action[:100]}...")

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
                    log('debug', summary=f"Observation: {observation[:100]}...")

                    # 記錄 ReAct 鏈
                    react_chain.append({
                        "iteration": iteration + 1,
                        "thought": thought,
                        "action": action,
                        "observation": observation
                    })

                    # 檢查是否完成
                    if "task completed" in observation.lower() or "success" in observation.lower():
                        log('info', summary=f"Task completed in iteration {iteration + 1}")
                        final_result = action
                        break
                else:
                    # 沒有 Reviewer，直接使用 Action 結果
                    react_chain.append({
                        "iteration": iteration + 1,
                        "thought": thought,
                        "action": action
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
        log('info', summary=f"Delegating task from {from_agent} to {to_agent}")

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
        log('info', summary="Chain of Thought execution")

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