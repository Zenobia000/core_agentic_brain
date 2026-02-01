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

    def _find_cached_answer(
        self,
        question: str,
        context: Optional["TaskContext"]
    ) -> Optional[str]:
        """Check if a similar question was already answered.

        Uses keyword matching to detect duplicate questions.
        """
        if not context or not context.metadata:
            return None

        collected_info = context.metadata.get("collected_user_info", [])
        if not collected_info:
            return None

        # Keywords to match for common question types
        question_lower = question.lower()

        # Define topic keywords
        topic_keywords = {
            "dates": ["date", "when", "日期", "時間", "april", "march", "mid-"],
            "travelers": ["traveler", "people", "person", "人數", "幾個人", "how many"],
            "budget": ["budget", "cost", "money", "預算", "花費", "twd", "台幣"],
            "location": ["city", "depart", "from", "出發", "where", "taipei", "airport"],
            "accommodation": ["hotel", "stay", "accommodation", "住宿", "farmstay", "homestay"],
        }

        # Determine the topic of the current question
        current_topic = None
        for topic, keywords in topic_keywords.items():
            if any(kw in question_lower for kw in keywords):
                current_topic = topic
                break

        if not current_topic:
            return None

        # Check if we already have an answer for this topic
        for item in collected_info:
            prev_question = item.get("question", "").lower()
            for kw in topic_keywords.get(current_topic, []):
                if kw in prev_question:
                    # Found a cached answer for this topic
                    return item.get("answer")

        return None

    def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional["TaskContext"] = None
    ) -> Dict:
        """Execute ask_user - prompt user for input.

        In interactive mode, prompts user directly.
        In non-interactive mode, returns error with the question.

        Includes duplicate detection - if a similar question was already
        answered, returns the cached answer instead of asking again.
        """
        question = parameters.get("question", "")
        ctx = parameters.get("context", "")
        options = parameters.get("options", [])

        # Check for duplicate question
        cached_answer = self._find_cached_answer(question, context)
        if cached_answer:
            print(f"\n[ask_user] Using cached answer for similar question: {cached_answer}")
            return {
                "success": True,
                "response": cached_answer,
                "question": question,
                "from_cache": True,
                "note": "This question was already answered. Using cached response."
            }

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
