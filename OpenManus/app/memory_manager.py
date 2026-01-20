"""
Memory Manager for OpenManus Agent System
Implements Principle 1: KV-Cache Optimization with Sliding Window and Summarization
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.schema import Message, Memory
from app.logger import logger
from app.llm import LLM


class MemoryWindow(BaseModel):
    """Sliding window for memory management"""

    window_size: int = Field(default=20, description="Number of recent messages to keep in active memory")
    summary_threshold: int = Field(default=30, description="Threshold for triggering summarization")


class MemorySummary(BaseModel):
    """Summary of older conversation history"""

    summary: str = Field(default="", description="Summarized content of older messages")
    message_count: int = Field(default=0, description="Number of messages summarized")
    created_at: datetime = Field(default_factory=datetime.now)
    important_facts: List[str] = Field(default_factory=list, description="Key facts extracted from history")


class EnhancedMemory(Memory):
    """
    Enhanced Memory with KV-Cache optimization
    Implements sliding window and automatic summarization
    """

    window: MemoryWindow = Field(default_factory=MemoryWindow)
    summary: Optional[MemorySummary] = None
    archived_messages: List[Message] = Field(default_factory=list, description="Archived messages for reference")
    llm: Optional[LLM] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.llm is None:
            self.llm = LLM()

    def add_message(self, message: Message) -> None:
        """Add a message with automatic memory management"""
        self.messages.append(message)

        # Check if we need to compress memory
        if len(self.messages) > self.window.summary_threshold:
            asyncio.create_task(self._compress_memory())

    async def _compress_memory(self) -> None:
        """Compress older messages into a summary"""
        try:
            # Get messages to summarize (older than window size)
            messages_to_summarize = self.messages[:-self.window.window_size]

            if not messages_to_summarize:
                return

            # Archive the messages
            self.archived_messages.extend(messages_to_summarize)

            # Create summarization prompt
            conversation_text = "\n".join([
                f"{msg.role}: {msg.content}"
                for msg in messages_to_summarize
                if msg.content
            ])

            summarization_prompt = f"""Summarize the following conversation history concisely.
Extract and list any important facts, decisions, or context that should be remembered.

Conversation:
{conversation_text}

Provide:
1. A brief summary (2-3 sentences)
2. List of important facts or decisions made
"""

            # Get summary from LLM
            summary_response = await self.llm.ask(
                messages=[Message.user_message(summarization_prompt)],
                system_msgs=[Message.system_message("You are a helpful assistant that creates concise summaries.")]
            )

            if summary_response and summary_response.content:
                # Parse and store summary
                self.summary = MemorySummary(
                    summary=summary_response.content,
                    message_count=len(messages_to_summarize),
                    important_facts=self._extract_facts(summary_response.content)
                )

                # Keep only recent messages
                self.messages = self.messages[-self.window.window_size:]

                logger.info(f"📝 Memory compressed: {len(messages_to_summarize)} messages summarized")

        except Exception as e:
            logger.error(f"Failed to compress memory: {e}")

    def _extract_facts(self, summary_text: str) -> List[str]:
        """Extract important facts from summary text"""
        facts = []
        lines = summary_text.split('\n')

        # Simple extraction: look for bullet points or numbered lists
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*') or
                        (len(line) > 2 and line[0].isdigit() and line[1] in '.)')):
                facts.append(line.lstrip('-*0123456789.) '))

        return facts[:5]  # Keep top 5 facts

    def get_context_messages(self) -> List[Message]:
        """
        Get messages for LLM context with summary prepended
        Optimized for KV-Cache utilization
        """
        context_messages = []

        # Add summary as system message if exists
        if self.summary:
            summary_msg = Message.system_message(
                f"Previous conversation summary ({self.summary.message_count} messages): "
                f"{self.summary.summary}\n"
                f"Key facts: {', '.join(self.summary.important_facts)}"
            )
            context_messages.append(summary_msg)

        # Add recent messages from sliding window
        context_messages.extend(self.messages[-self.window.window_size:])

        return context_messages

    def clear_with_summary_retention(self) -> None:
        """Clear messages but retain summary for context continuity"""
        self.archived_messages.extend(self.messages)
        self.messages.clear()
        # Summary is retained


class MemoryManager:
    """
    Manager for different memory strategies
    Allows switching between standard and enhanced memory
    """

    @staticmethod
    def create_memory(
        strategy: str = "enhanced",
        window_size: int = 20,
        summary_threshold: int = 30,
        max_messages: int = 100
    ) -> Memory:
        """
        Factory method to create appropriate memory instance

        Args:
            strategy: "standard" or "enhanced"
            window_size: Size of sliding window for enhanced memory
            summary_threshold: Threshold for triggering summarization
            max_messages: Maximum messages for standard memory
        """
        if strategy == "enhanced":
            return EnhancedMemory(
                window=MemoryWindow(
                    window_size=window_size,
                    summary_threshold=summary_threshold
                ),
                max_messages=max_messages
            )
        else:
            return Memory(max_messages=max_messages)

    @staticmethod
    def migrate_memory(old_memory: Memory) -> EnhancedMemory:
        """
        Migrate from standard Memory to EnhancedMemory
        Preserves existing messages
        """
        enhanced = EnhancedMemory()
        enhanced.messages = old_memory.messages.copy()

        # Trigger compression if needed
        if len(enhanced.messages) > enhanced.window.summary_threshold:
            asyncio.create_task(enhanced._compress_memory())

        return enhanced