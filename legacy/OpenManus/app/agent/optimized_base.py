"""
Optimized Base Agent with Token Management
整合 Token 優化的基礎 Agent
"""

from typing import List, Optional, Dict, Any
import asyncio
from contextlib import asynccontextmanager

from pydantic import Field

from app.agent.base import BaseAgent
from app.memory_optimizer import (
    MemoryOptimizer,
    OptimizationConfig,
    OptimizationStrategy,
    SmartContextManager
)
from app.schema import Message, Role, AgentState
from app.logger import logger


class OptimizedBaseAgent(BaseAgent):
    """優化版基礎 Agent - 自動管理 Token 使用"""

    # Token 優化器
    memory_optimizer: MemoryOptimizer = Field(
        default_factory=lambda: MemoryOptimizer(),
        description="Memory optimizer for token management"
    )

    # 智能上下文管理器
    context_manager: SmartContextManager = Field(
        default_factory=lambda: SmartContextManager(),
        description="Smart context manager"
    )

    # 優化配置
    optimization_config: OptimizationConfig = Field(
        default_factory=lambda: OptimizationConfig(),
        description="Optimization configuration"
    )

    # Token 使用統計
    token_stats: Dict[str, int] = Field(
        default_factory=dict,
        description="Token usage statistics"
    )

    # 是否啟用優化
    enable_optimization: bool = Field(
        default=True,
        description="Enable token optimization"
    )

    # 任務類型（用於自適應優化）
    task_type: str = Field(
        default="general",
        description="Task type for adaptive optimization"
    )

    def update_memory(
        self,
        role: str,
        content: str,
        base64_image: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        覆寫父類方法，添加優化邏輯

        Args:
            role: 訊息角色
            content: 訊息內容
            base64_image: 圖片數據
            **kwargs: 其他參數
        """
        # 創建訊息
        message = Message(
            role=role,
            content=content,
            base64_image=base64_image,
            **kwargs
        )

        # 添加到記憶
        self.memory.add_message(message)

        # 添加到上下文管理器
        self.context_manager.add_message(message)

        # 如果啟用優化，定期清理
        if self.enable_optimization:
            self._optimize_memory_if_needed()

    def _optimize_memory_if_needed(self):
        """根據需要優化記憶"""
        # 估算當前 token 使用
        current_tokens = self.memory_optimizer.estimate_tokens(self.memory.messages)

        # 如果超過閾值，執行優化
        if current_tokens > self.optimization_config.max_tokens:
            logger.info(f"Token threshold exceeded ({current_tokens}), optimizing memory...")
            self._perform_memory_optimization()

    def _perform_memory_optimization(self):
        """執行記憶優化"""
        original_messages = self.memory.messages.copy()

        # 優化訊息
        optimized_messages = self.memory_optimizer.optimize_memory(original_messages)

        # 更新記憶
        self.memory.messages = optimized_messages

        # 記錄統計
        stats = self.memory_optimizer.get_optimization_stats(original_messages, optimized_messages)
        self.token_stats["total_optimizations"] = self.token_stats.get("total_optimizations", 0) + 1
        self.token_stats["tokens_saved"] = self.token_stats.get("tokens_saved", 0) + \
                                          (stats["original_tokens"] - stats["optimized_tokens"])

        logger.info(
            f"Memory optimized: {stats['original_messages']} → {stats['optimized_messages']} messages, "
            f"{stats['reduction_rate']:.1%} token reduction"
        )

    def get_optimized_messages(self, include_system: bool = True) -> List[Dict]:
        """
        獲取優化後的訊息列表（用於 LLM 調用）

        Args:
            include_system: 是否包含系統訊息

        Returns:
            優化後的訊息字典列表
        """
        if not self.enable_optimization:
            # 不優化，直接返回
            return [msg.to_dict() for msg in self.memory.messages]

        # 獲取優化後的上下文
        optimized = self.context_manager.get_optimized_context()

        # 轉換為字典格式
        messages = []
        for msg in optimized:
            if not include_system and msg.role == Role.SYSTEM:
                continue
            messages.append(msg.to_dict())

        return messages

    def set_optimization_strategy(self, strategy: str):
        """
        設置優化策略

        Args:
            strategy: 優化策略 (aggressive/balanced/conservative)
        """
        try:
            self.optimization_config.strategy = OptimizationStrategy(strategy)
            self.memory_optimizer.config = self.optimization_config
            logger.info(f"Optimization strategy set to: {strategy}")
        except ValueError:
            logger.error(f"Invalid optimization strategy: {strategy}")

    def set_task_type(self, task_type: str):
        """
        設置任務類型以自適應優化

        Args:
            task_type: 任務類型 (simple_query/web_search/code_generation/analysis/general)
        """
        self.task_type = task_type
        self.context_manager.set_task_type(task_type)

        # 根據任務類型調整優化配置
        task_configs = {
            "simple_query": {
                "strategy": OptimizationStrategy.AGGRESSIVE,
                "max_tokens": 1500,
                "max_messages": 5
            },
            "web_search": {
                "strategy": OptimizationStrategy.BALANCED,
                "max_tokens": 2000,
                "max_messages": 8
            },
            "code_generation": {
                "strategy": OptimizationStrategy.CONSERVATIVE,
                "max_tokens": 3000,
                "max_messages": 15
            },
            "analysis": {
                "strategy": OptimizationStrategy.BALANCED,
                "max_tokens": 2500,
                "max_messages": 10
            },
            "general": {
                "strategy": OptimizationStrategy.BALANCED,
                "max_tokens": 2000,
                "max_messages": 10
            }
        }

        if task_type in task_configs:
            config = task_configs[task_type]
            self.optimization_config.strategy = config["strategy"]
            self.optimization_config.max_tokens = config["max_tokens"]
            self.optimization_config.max_messages = config["max_messages"]
            self.memory_optimizer.config = self.optimization_config

            logger.info(f"Task type set to: {task_type}, optimization adjusted")

    async def execute_with_optimization(self) -> Any:
        """
        執行 Agent 並自動優化 Token 使用

        Returns:
            執行結果
        """
        try:
            # 設置狀態
            async with self.state_context(AgentState.RUNNING):
                # 執行步驟
                while self.current_step < self.max_steps:
                    # 優化記憶（每步驟前）
                    if self.enable_optimization and self.current_step > 0:
                        self._optimize_memory_if_needed()

                    # 執行步驟
                    result = await self.step()

                    # 更新步驟計數
                    self.current_step += 1

                    # 檢查是否完成
                    if self.state == AgentState.SUCCESS:
                        break

                # 最終優化
                if self.enable_optimization:
                    self._perform_memory_optimization()

                # 返回結果
                return self._get_final_result()

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            self.state = AgentState.ERROR
            raise

    def _get_final_result(self) -> Dict:
        """獲取最終結果和統計"""
        # 獲取最後的助手訊息作為結果
        assistant_messages = [
            m for m in self.memory.messages
            if m.role == Role.ASSISTANT
        ]

        result = assistant_messages[-1].content if assistant_messages else "No result"

        return {
            "result": result,
            "token_stats": self.token_stats,
            "messages_count": len(self.memory.messages),
            "optimization_enabled": self.enable_optimization,
            "task_type": self.task_type,
            "final_state": self.state.value
        }

    def get_token_usage_report(self) -> str:
        """獲取 Token 使用報告"""
        report_lines = [
            "=== Token Usage Report ===",
            f"Task Type: {self.task_type}",
            f"Optimization: {'Enabled' if self.enable_optimization else 'Disabled'}",
            f"Strategy: {self.optimization_config.strategy.value}",
            f"",
            f"Current Messages: {len(self.memory.messages)}",
            f"Estimated Tokens: {self.memory_optimizer.estimate_tokens(self.memory.messages)}",
            f"Max Token Limit: {self.optimization_config.max_tokens}",
            f"",
            f"Statistics:",
            f"- Total Optimizations: {self.token_stats.get('total_optimizations', 0)}",
            f"- Tokens Saved: {self.token_stats.get('tokens_saved', 0)}",
            "========================"
        ]

        return "\n".join(report_lines)

    def clear_memory(self):
        """清除記憶和上下文"""
        super().clear_memory()
        self.context_manager.clear_context()
        self.token_stats = {}
        logger.info("Memory and context cleared")


class TokenAwareAgent(OptimizedBaseAgent):
    """Token 感知 Agent - 實時監控和優化 Token 使用"""

    # Token 預算
    token_budget: int = Field(
        default=4000,
        description="Total token budget for the task"
    )

    # 剩餘 Token
    remaining_tokens: int = Field(
        default=4000,
        description="Remaining tokens"
    )

    # Token 警告閾值
    warning_threshold: float = Field(
        default=0.8,
        description="Warning threshold (percentage of budget)"
    )

    async def step(self) -> Any:
        """覆寫步驟方法，添加 Token 監控"""
        # 檢查 Token 預算
        current_usage = self.memory_optimizer.estimate_tokens(self.memory.messages)
        self.remaining_tokens = self.token_budget - current_usage

        # 檢查是否超出預算
        if self.remaining_tokens <= 0:
            logger.error("Token budget exceeded! Stopping execution.")
            self.state = AgentState.ERROR
            return {"error": "Token budget exceeded"}

        # 檢查警告閾值
        usage_ratio = current_usage / self.token_budget
        if usage_ratio > self.warning_threshold:
            logger.warning(f"Token usage at {usage_ratio:.1%} of budget")

            # 自動切換到更激進的優化策略
            if self.optimization_config.strategy != OptimizationStrategy.AGGRESSIVE:
                logger.info("Switching to aggressive optimization due to high token usage")
                self.set_optimization_strategy("aggressive")
                self._perform_memory_optimization()

        # 執行原始步驟邏輯
        return await super().step()

    def adjust_budget(self, new_budget: int):
        """調整 Token 預算"""
        self.token_budget = new_budget
        self.remaining_tokens = new_budget - self.memory_optimizer.estimate_tokens(self.memory.messages)
        logger.info(f"Token budget adjusted to: {new_budget}")