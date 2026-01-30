"""
Ask User tool - Allows agent to request clarification from user.
Linus: Simple tools that do one thing well
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from ..pure_base import PureTool

if TYPE_CHECKING:
    from core.types import TaskContext


class Tool(PureTool):
    """Ask User tool - request clarification when information is missing."""

    def __init__(self):
        """Initialize ask_user tool."""
        super().__init__()
        self.name = "ask_user"

    @property
    def definition(self) -> Dict:
        """Tool definition - OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": "ask_user",
                "description": "Ask user for clarification when information is missing or ambiguous. Use instead of guessing or making assumptions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The question to ask the user"
                        },
                        "context": {
                            "type": "string",
                            "description": "Why this information is needed"
                        },
                        "options": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Suggested answer options (if applicable)"
                        }
                    },
                    "required": ["question"]
                }
            }
        }

    def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional["TaskContext"] = None
    ) -> Dict:
        """Execute ask_user - prompt user for input.

        In interactive mode, prompts user directly.
        In non-interactive mode, returns error with the question.
        """
        question = parameters.get("question", "")
        ctx = parameters.get("context", "")
        options = parameters.get("options", [])

        try:
            # Display question to user
            print(f"\n{'='*50}")
            print(f"[Agent Question] {question}")
            if ctx:
                print(f"Context: {ctx}")
            if options:
                print("Suggested options:")
                for i, opt in enumerate(options, 1):
                    print(f"  {i}. {opt}")

            # Get user response
            response = input("Your answer: ").strip()
            print(f"{'='*50}\n")

            return {
                "success": True,
                "response": response,
                "question": question
            }

        except EOFError:
            # Non-interactive mode - provide guidance to LLM
            return {
                "success": False,
                "error": "NON-INTERACTIVE MODE",
                "instruction": (
                    "User input not available. You MUST proceed with reasonable assumptions. "
                    "Do NOT call ask_user again. Instead, make a sensible default choice and continue the task. "
                    "If critical info is truly missing, call `terminate` with reason explaining what info is needed."
                ),
                "question": question,
                "context": ctx,
                "options": options
            }
