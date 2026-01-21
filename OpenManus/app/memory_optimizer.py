"""
Memory Optimizer for OpenManus Agent
整合 Token 優化到 Agent 記憶管理系統
"""

from typing import List, Dict, Optional, Any
import json
import hashlib
from dataclasses import dataclass
from enum import Enum

from app.schema import Message, Role


class OptimizationStrategy(Enum):
    """優化策略"""
    AGGRESSIVE = "aggressive"  # 激進壓縮（保留最少內容）
    BALANCED = "balanced"      # 平衡模式（預設）
    CONSERVATIVE = "conservative"  # 保守模式（保留更多內容）


@dataclass
class OptimizationConfig:
    """優化配置"""
    strategy: OptimizationStrategy = OptimizationStrategy.BALANCED
    max_tokens: int = 2000
    max_messages: int = 10
    preserve_system: bool = True
    preserve_errors: bool = True
    summary_threshold: int = 500


class MemoryOptimizer:
    """記憶優化器 - 減少 Token 使用"""

    def __init__(self, config: Optional[OptimizationConfig] = None):
        """初始化優化器"""
        self.config = config or OptimizationConfig()
        self._summary_cache = {}
        self._token_cache = {}

    def optimize_memory(self, messages: List[Message]) -> List[Message]:
        """
        優化記憶中的訊息列表

        Args:
            messages: 原始訊息列表

        Returns:
            優化後的訊息列表
        """
        if not messages:
            return messages

        # 根據策略選擇優化方法
        if self.config.strategy == OptimizationStrategy.AGGRESSIVE:
            return self._aggressive_optimization(messages)
        elif self.config.strategy == OptimizationStrategy.CONSERVATIVE:
            return self._conservative_optimization(messages)
        else:
            return self._balanced_optimization(messages)

    def _aggressive_optimization(self, messages: List[Message]) -> List[Message]:
        """激進優化 - 只保留關鍵信息"""
        optimized = []

        # 保留系統訊息
        system_msgs = [m for m in messages if m.role == Role.SYSTEM]
        optimized.extend(system_msgs[:1])  # 只保留第一個系統訊息

        # 保留最後的用戶訊息
        user_msgs = [m for m in messages if m.role == Role.USER]
        if user_msgs:
            optimized.append(user_msgs[-1])

        # 保留錯誤訊息
        if self.config.preserve_errors:
            error_msgs = [
                m for m in messages
                if m.role == Role.TOOL and m.content and "error" in m.content.lower()
            ]
            optimized.extend(error_msgs[-2:])  # 只保留最後2個錯誤

        # 保留最後的結果
        recent = messages[-3:]
        for msg in recent:
            if msg not in optimized:
                optimized.append(msg)

        return self._compress_messages(optimized)

    def _balanced_optimization(self, messages: List[Message]) -> List[Message]:
        """平衡優化 - 保留重要信息，壓縮冗餘"""
        optimized = []

        # 分類訊息
        system_msgs = []
        user_msgs = []
        assistant_msgs = []
        tool_msgs = []

        for msg in messages:
            if msg.role == Role.SYSTEM:
                system_msgs.append(msg)
            elif msg.role == Role.USER:
                user_msgs.append(msg)
            elif msg.role == Role.ASSISTANT:
                assistant_msgs.append(msg)
            elif msg.role == Role.TOOL:
                tool_msgs.append(msg)

        # 保留系統訊息
        if self.config.preserve_system and system_msgs:
            optimized.append(system_msgs[0])

        # 保留重要的用戶訊息（第一個和最後幾個）
        if user_msgs:
            optimized.append(user_msgs[0])  # 初始請求
            if len(user_msgs) > 1:
                optimized.extend(user_msgs[-2:])  # 最近的互動

        # 壓縮工具訊息
        compressed_tools = self._compress_tool_messages(tool_msgs)
        optimized.extend(compressed_tools[-5:])  # 保留最近5個

        # 保留重要的助手訊息
        important_assistant = [
            m for m in assistant_msgs
            if m.tool_calls or (m.content and len(m.content) < 200)
        ]
        optimized.extend(important_assistant[-3:])

        return self._apply_sliding_window(optimized)

    def _conservative_optimization(self, messages: List[Message]) -> List[Message]:
        """保守優化 - 保留更多內容"""
        # 只壓縮工具訊息，保留其他所有訊息
        optimized = []

        for msg in messages:
            if msg.role == Role.TOOL and msg.content and len(msg.content) > self.config.summary_threshold:
                optimized.append(self._summarize_message(msg))
            else:
                optimized.append(msg)

        # 應用滑動視窗（但視窗更大）
        window_size = self.config.max_messages * 2
        return optimized[-window_size:]

    def _compress_tool_messages(self, tool_msgs: List[Message]) -> List[Message]:
        """壓縮工具訊息"""
        compressed = []

        for msg in tool_msgs:
            if not msg.content:
                compressed.append(msg)
                continue

            # 檢查是否需要壓縮
            if len(msg.content) > self.config.summary_threshold:
                compressed.append(self._summarize_message(msg))
            else:
                compressed.append(msg)

        return compressed

    def _summarize_message(self, message: Message) -> Message:
        """摘要單個訊息"""
        if not message.content:
            return message

        # 檢查緩存
        content_hash = hashlib.md5(message.content.encode()).hexdigest()
        if content_hash in self._summary_cache:
            summary = self._summary_cache[content_hash]
        else:
            summary = self._create_summary(message.content)
            self._summary_cache[content_hash] = summary

        # 創建摘要訊息
        summarized = Message(
            role=message.role,
            content=f"[Summarized] {summary}",
            tool_calls=message.tool_calls,
            name=message.name,
            tool_call_id=message.tool_call_id
        )

        return summarized

    def _create_summary(self, content: str, max_length: int = 200) -> str:
        """創建內容摘要"""
        if len(content) <= max_length:
            return content

        lines = content.split('\n')

        # 優先保留的關鍵字
        keywords = ["error", "failed", "success", "result", "complete", "found"]

        important_lines = []
        other_lines = []

        for line in lines:
            if any(kw in line.lower() for kw in keywords):
                important_lines.append(line.strip()[:100])
            else:
                other_lines.append(line.strip()[:50])

        # 構建摘要
        summary = []

        # 添加重要行
        summary.extend(important_lines[:3])

        # 添加統計信息
        if len(lines) > 5:
            summary.append(f"... ({len(lines)} lines total)")

        return '\n'.join(summary)[:max_length]

    def _compress_messages(self, messages: List[Message]) -> List[Message]:
        """批量壓縮訊息"""
        compressed = []

        for msg in messages:
            if msg.role == Role.TOOL:
                compressed.append(self._summarize_message(msg))
            else:
                compressed.append(msg)

        return compressed

    def _apply_sliding_window(self, messages: List[Message]) -> List[Message]:
        """應用滑動視窗"""
        if len(messages) <= self.config.max_messages:
            return messages

        # 分離系統訊息和其他訊息
        system_msgs = [m for m in messages if m.role == Role.SYSTEM]
        other_msgs = [m for m in messages if m.role != Role.SYSTEM]

        # 保留系統訊息 + 最近的其他訊息
        result = []
        if self.config.preserve_system:
            result.extend(system_msgs[:1])

        remaining_slots = self.config.max_messages - len(result)
        result.extend(other_msgs[-remaining_slots:])

        return result

    def estimate_tokens(self, messages: List[Message]) -> int:
        """估算訊息列表的 token 數量"""
        # 簡單估算：每4個字符約1個token
        total_chars = 0

        for msg in messages:
            if msg.content:
                total_chars += len(msg.content)
            if msg.tool_calls:
                total_chars += len(json.dumps([tc.dict() for tc in msg.tool_calls]))

            # 角色和結構開銷
            total_chars += 20

        return total_chars // 4

    def get_optimization_stats(self, original: List[Message], optimized: List[Message]) -> Dict:
        """獲取優化統計"""
        original_tokens = self.estimate_tokens(original)
        optimized_tokens = self.estimate_tokens(optimized)

        return {
            "original_messages": len(original),
            "optimized_messages": len(optimized),
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "reduction_rate": 1 - (optimized_tokens / original_tokens) if original_tokens > 0 else 0,
            "messages_dropped": len(original) - len(optimized)
        }


class SmartContextManager:
    """智能上下文管理器"""

    def __init__(self):
        """初始化管理器"""
        self.optimizer = MemoryOptimizer()
        self.context_history = []
        self.task_type = "general"

    def set_task_type(self, task_type: str):
        """設置任務類型以調整優化策略"""
        self.task_type = task_type

        # 根據任務類型調整配置
        if task_type == "simple_query":
            self.optimizer.config.strategy = OptimizationStrategy.AGGRESSIVE
            self.optimizer.config.max_messages = 5
        elif task_type == "complex_analysis":
            self.optimizer.config.strategy = OptimizationStrategy.CONSERVATIVE
            self.optimizer.config.max_messages = 15
        else:
            self.optimizer.config.strategy = OptimizationStrategy.BALANCED
            self.optimizer.config.max_messages = 10

    def add_message(self, message: Message):
        """添加新訊息到上下文"""
        self.context_history.append(message)

    def get_optimized_context(self) -> List[Message]:
        """獲取優化後的上下文"""
        optimized = self.optimizer.optimize_memory(self.context_history)

        # 打印優化統計（調試用）
        stats = self.optimizer.get_optimization_stats(self.context_history, optimized)
        if stats["reduction_rate"] > 0.3:
            print(f"Context optimized: {stats['original_tokens']} → {stats['optimized_tokens']} tokens "
                  f"({stats['reduction_rate']:.1%} reduction)")

        return optimized

    def clear_context(self):
        """清除上下文"""
        self.context_history = []

    def get_context_summary(self) -> str:
        """獲取上下文摘要"""
        if not self.context_history:
            return "Empty context"

        summary_parts = []

        # 統計各類訊息
        role_counts = {}
        for msg in self.context_history:
            role_counts[msg.role] = role_counts.get(msg.role, 0) + 1

        summary_parts.append(f"Context: {len(self.context_history)} messages")
        for role, count in role_counts.items():
            summary_parts.append(f"- {role}: {count}")

        # 估算 token
        tokens = self.optimizer.estimate_tokens(self.context_history)
        summary_parts.append(f"Estimated tokens: {tokens}")

        return "\n".join(summary_parts)