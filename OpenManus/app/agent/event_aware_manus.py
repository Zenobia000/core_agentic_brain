"""
Event-aware Manus agent that emits structured events during execution
"""
from typing import Optional, List, Dict, Any, Callable
import json
import asyncio
import uuid
from pathlib import Path

from app.agent.manus import Manus
from app.events import (
    EventBus,
    StepEvent,
    EventPhase,
    EventRole,
    ToolInfo,
    Artifact,
    ArtifactType,
    ThinkingUpdate,
    TaskUpdate,
    event_bus
)
from app.schema import Message, ToolCall, AgentState
from app.logger import logger


class EventAwareManus(Manus):
    """
    Extended Manus agent that emits structured events for UI visualization
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_bus: EventBus = event_bus
        self.current_run_id: str = str(uuid.uuid4())
        self.step_counter: int = 0
        self.event_handlers: List[Callable] = []

        # Reset event bus for new run
        self.event_bus.reset()
        self.event_bus.current_run_id = self.current_run_id

    def add_event_handler(self, handler: Callable):
        """Add a handler for events (e.g., WebSocket send)"""
        self.event_handlers.append(handler)
        self.event_bus.register_handler("*", handler)

    def emit_event(self, phase: EventPhase, **kwargs):
        """Helper to emit structured events"""
        return self.event_bus.create_event(
            phase=phase,
            **kwargs
        )

    async def think(self) -> bool:
        """Process current state with event emission"""
        # Emit thinking start event
        self.emit_event(
            EventPhase.THINK,
            role=EventRole.AGENT,
            message="Agent is analyzing the current situation and planning next actions",
            thinking=self.next_step_prompt if self.next_step_prompt else None
        )

        # Call parent think method
        result = await super().think()

        # Extract and emit thinking content
        if self.tool_calls:
            tool_names = [call.function.name for call in self.tool_calls]
            self.emit_event(
                EventPhase.THINK,
                role=EventRole.AGENT,
                message=f"Decided to use tools: {', '.join(tool_names)}",
                thinking=self.messages[-1].content if self.messages else None,
                metadata={"tool_count": len(self.tool_calls)}
            )

        return result

    async def act(self) -> str:
        """Execute tool calls with structured event emission"""
        if not self.tool_calls:
            # No tools to execute
            if self.tool_choices == "required":
                self.emit_event(
                    EventPhase.ERROR,
                    role=EventRole.SYSTEM,
                    message="Tool calls required but none provided",
                    error="No tool calls available"
                )
                raise ValueError("Tool calls required but none provided")

            # Return last message content
            content = self.messages[-1].content or "No content or commands to execute"
            return content

        results = []

        for command in self.tool_calls:
            tool_name = command.function.name
            tool_args = command.function.arguments

            # Parse arguments
            try:
                args_dict = json.loads(tool_args) if isinstance(tool_args, str) else tool_args
            except:
                args_dict = {"raw": tool_args}

            # Emit tool start event
            tool_info = ToolInfo(
                name=tool_name,
                input=args_dict,
                status="running"
            )

            self.emit_event(
                EventPhase.ACT,
                role=EventRole.TOOL,
                message=f"Executing tool: {tool_name}",
                tool=tool_info
            )

            # Execute tool
            import time
            start_time = time.time()

            try:
                # Get tool from available_tools
                tool = self.available_tools.get_tool(tool_name)
                if not tool:
                    raise ValueError(f"Tool '{tool_name}' not found")

                # Execute tool
                result = await tool.arun(**args_dict)

                # Calculate duration
                duration_ms = int((time.time() - start_time) * 1000)

                # Update tool info
                tool_info.status = "success"
                tool_info.output = str(result)[:500]  # Truncate for events
                tool_info.duration_ms = duration_ms

                # Check for artifacts
                artifacts = self._extract_artifacts(result, tool_name)

                # Emit tool success event
                self.emit_event(
                    EventPhase.OBSERVE,
                    role=EventRole.TOOL,
                    message=f"Tool {tool_name} completed successfully",
                    tool=tool_info,
                    artifacts=artifacts
                )

                results.append(str(result))

                # Add tool result to memory
                self.memory.add_message(Message.tool_message(
                    content=str(result),
                    name=tool_name,
                    tool_call_id=command.id
                ))

                # Handle special tools
                if tool_name in self.special_tool_names:
                    if tool_name == "Terminate":
                        self.state = AgentState.FINISHED
                        # Emit final answer
                        self.emit_event(
                            EventPhase.FINAL,
                            role=EventRole.AGENT,
                            message=str(result)
                        )

            except Exception as e:
                # Update tool info with error
                tool_info.status = "failed"
                tool_info.error = str(e)
                tool_info.duration_ms = int((time.time() - start_time) * 1000)

                # Emit tool error event
                self.emit_event(
                    EventPhase.ERROR,
                    role=EventRole.TOOL,
                    message=f"Tool {tool_name} failed: {str(e)}",
                    tool=tool_info,
                    error=str(e),
                    error_type=type(e).__name__
                )

                error_msg = f"Error executing {tool_name}: {str(e)}"
                results.append(error_msg)
                logger.error(error_msg)

                # Add error message to memory
                self.memory.add_message(Message.tool_message(
                    content=error_msg,
                    name=tool_name,
                    tool_call_id=command.id
                ))

        # Add results to memory (don't add here, already added per tool)
        observation = "\n\n".join(results)

        return observation

    def _extract_artifacts(self, result: Any, tool_name: str) -> List[Artifact]:
        """Extract artifacts from tool results"""
        artifacts = []

        # Convert result to string for analysis
        result_str = str(result)

        # Check for file paths
        if tool_name == "StrReplaceEditor" and "successfully" in result_str.lower():
            # Extract file path from editor results
            import re
            path_match = re.search(r'File\s+"([^"]+)"', result_str)
            if path_match:
                file_path = path_match.group(1)
                artifacts.append(Artifact(
                    type=ArtifactType.FILE,
                    path=file_path,
                    preview=self._get_file_preview(file_path)
                ))

        # Check for created files in Python execution
        elif tool_name == "PythonExecute":
            # Look for file operations in the result
            import re
            file_patterns = [
                r"wrote.*?to\s+([^\s]+)",
                r"created.*?file\s+([^\s]+)",
                r"saved.*?as\s+([^\s]+)",
                r"output.*?to\s+([^\s]+)"
            ]

            for pattern in file_patterns:
                matches = re.findall(pattern, result_str, re.IGNORECASE)
                for match in matches:
                    if match and Path(match).exists():
                        artifacts.append(Artifact(
                            type=ArtifactType.FILE,
                            path=match,
                            preview=self._get_file_preview(match)
                        ))

        # Check for URLs in browser results
        elif tool_name == "BrowserUseTool" and "http" in result_str:
            import re
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls = re.findall(url_pattern, result_str)
            for url in urls[:3]:  # Limit to first 3 URLs
                artifacts.append(Artifact(
                    type=ArtifactType.URL,
                    url=url
                ))

        # Check for markdown content
        if "```" in result_str or result_str.count("#") > 3:
            # Likely contains markdown
            if len(result_str) > 500:
                artifacts.append(Artifact(
                    type=ArtifactType.MARKDOWN,
                    preview=result_str[:500] + "..."
                ))

        return artifacts

    def _get_file_preview(self, file_path: str, lines: int = 10) -> str:
        """Get preview of file content"""
        try:
            path = Path(file_path)
            if not path.exists():
                return "File not found"

            # Check file size
            size = path.stat().st_size
            if size > 1_000_000:  # 1MB
                return f"Large file ({size:,} bytes)"

            # Read first N lines
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                preview_lines = []
                for i, line in enumerate(f):
                    if i >= lines:
                        preview_lines.append("...")
                        break
                    preview_lines.append(line.rstrip())

                return "\n".join(preview_lines)
        except Exception as e:
            return f"Could not read file: {e}"

    async def observe(self, observation: str) -> None:
        """Process observation with event emission"""
        # Emit observation event
        self.emit_event(
            EventPhase.OBSERVE,
            role=EventRole.AGENT,
            message="Processing tool results and observations",
            metadata={"observation_length": len(observation)}
        )

        await super().observe(observation)

    async def run(self, task: str) -> str:
        """Run the agent with event tracking"""
        # Emit task start
        self.emit_event(
            EventPhase.THINK,
            role=EventRole.USER,
            message=f"Starting task: {task[:100]}..." if len(task) > 100 else f"Starting task: {task}"
        )

        # Run the agent
        result = await super().run(task)

        # Emit final answer if not already emitted
        if self.state == AgentState.FINISHED:
            # Check if we already have a final event
            has_final = any(
                e.phase == EventPhase.FINAL
                for e in self.event_bus.event_history
            )

            if not has_final:
                self.emit_event(
                    EventPhase.FINAL,
                    role=EventRole.AGENT,
                    message=result
                )

        return result

    def emit_thinking_update(self, summary: str, steps: List[str] = None, detail: str = None):
        """Emit a thinking update for the UI"""
        update = ThinkingUpdate(
            summary=summary,
            detail=detail,
            steps=steps or [],
            current_step=self.step_counter,
            total_steps=self.max_steps
        )

        # Send via event handlers
        for handler in self.event_handlers:
            asyncio.create_task(handler(update.to_ws_message()))

    def emit_task_update(self, name: str, current: int, total: int, phase_name: str):
        """Emit a task progress update"""
        update = TaskUpdate(
            name=name,
            current_phase=current,
            total_phases=total,
            phase_name=phase_name,
            progress_percentage=(current / total * 100) if total > 0 else 0
        )

        # Send via event handlers
        for handler in self.event_handlers:
            asyncio.create_task(handler(update.to_ws_message()))

    @classmethod
    async def create(cls, **kwargs) -> "EventAwareManus":
        """Factory method to create and properly initialize an EventAwareManus instance."""
        instance = cls(**kwargs)
        await instance.initialize_mcp_servers()
        instance._initialized = True
        return instance