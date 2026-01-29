"""
Terminate tool - Signals end of ReAct loop
Linus: Simple tools that do one thing well
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from ..pure_base import PureTool

if TYPE_CHECKING:
    from core.types import TaskContext


class Tool(PureTool):
    """Terminate tool - signals the agent to end the ReAct loop."""

    def __init__(self):
        """Initialize terminate tool."""
        super().__init__()
        self.name = "terminate"

    @property
    def definition(self) -> Dict:
        """Tool definition - OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": "terminate",
                "description": "Signal that the task is complete and end the execution loop. Use this when you have finished the task or have provided a final answer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Brief reason for terminating (e.g., 'task completed', 'answer provided')"
                        }
                    },
                    "required": []
                }
            }
        }

    def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional["TaskContext"] = None
    ) -> Dict:
        """Execute terminate - simply returns success.
        
        The actual termination logic is in ExecutorAgent._execute_react().
        This tool just needs to exist and return a result.
        """
        reason = parameters.get("reason", "Task completed")
        return {
            "success": True,
            "message": f"Terminating: {reason}",
            "terminated": True
        }
