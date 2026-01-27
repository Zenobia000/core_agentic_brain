# tools/shell.py
import subprocess
import os
from core.tool_manager import register_tool

# Security warning: This tool is powerful and can be dangerous.
# In a real-world application, you should sandbox this environment
# or add strict validation to prevent malicious commands.
WORKSPACE_DIR = "workspace"

@register_tool
def execute_shell(command: str) -> str:
    """
    Executes a shell command inside the workspace directory.

    Args:
        command: The shell command to execute.
    
    Returns:
        The stdout and stderr of the command.
    """
    if not command:
        return "Error: No command provided."
    
    try:
        # Ensure the workspace directory exists
        if not os.path.exists(WORKSPACE_DIR):
            os.makedirs(WORKSPACE_DIR)

        # Execute the command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=WORKSPACE_DIR, # Run the command in the workspace directory
            check=False, # Do not raise an exception on non-zero exit codes
            timeout=30 # Add a timeout for safety
        )
        
        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
        
        if not output:
            return "Command executed with no output."
            
        return output.strip()

    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error executing command: {e}"
