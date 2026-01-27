# core/memory.py
from typing import List, Dict, Any

class Memory:
    """
    A simple class to manage the agent's conversational history and thoughts.
    """
    def __init__(self, max_history: int = 10):
        self.messages: List[Dict[str, Any]] = []
        self.max_history = max_history

    def add_message(self, role: str, content: str):
        """
        Adds a message to the history.

        Args:
            role: The role of the speaker (e.g., "user", "assistant", "system").
            content: The content of the message.
        """
        message = {"role": role, "content": content}
        self.messages.append(message)
        self._enforce_max_history()

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Retrieves the current conversational history.

        Returns:
            A list of message dictionaries.
        """
        return self.messages

    def _enforce_max_history(self):
        """
        Ensures the message history does not exceed the maximum size.
        It preserves the system message (if any) and trims from the oldest messages.
        """
        if len(self.messages) > self.max_history:
            # Find the first message (usually the system prompt)
            system_message = None
            if self.messages and self.messages[0]["role"] == "system":
                system_message = self.messages[0]
            
            # Get the most recent messages
            relevant_messages = self.messages[-self.max_history:]
            
            # If there was a system message and it's not in the recent list, add it back
            if system_message and system_message not in relevant_messages:
                self.messages = [system_message] + relevant_messages[1:]
            else:
                self.messages = relevant_messages
                
    def clear(self):
        """Clears the message history."""
        self.messages = []

if __name__ == "__main__":
    print("Testing Memory class...")
    memory = Memory(max_history=5)
    memory.add_message("system", "You are a helpful assistant.")
    for i in range(10):
        memory.add_message("user", f"This is message {i+1}")
        memory.add_message("assistant", f"This is my response to message {i+1}")

    print(f"Current history size: {len(memory.get_history())}")
    print("Current history:")
    for msg in memory.get_history():
        print(f"- {msg['role']}: {msg['content']}")

    # Expected: System message + last 4 user/assistant messages
    assert len(memory.get_history()) <= 5
    assert memory.get_history()[0]["role"] == "system"
    assert "message 10" in memory.get_history()[-2]["content"]
    print("\nMemory test passed!")
