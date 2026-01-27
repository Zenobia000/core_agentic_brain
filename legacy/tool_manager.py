# core/tool_manager.py
import inspect
import pkgutil
from typing import Dict, Any, Callable, List

# A registry for all available tools
_tool_registry: Dict[str, Callable] = {}

def register_tool(func: Callable) -> Callable:
    """
    A decorator to register a function as a tool.
    The function's name will be used as the tool's identifier.
    The function's docstring will be used as its description.
    """
    tool_name = func.__name__
    if tool_name in _tool_registry:
        raise ValueError(f"Tool '{tool_name}' is already registered.")
    
    _tool_registry[tool_name] = func
    return func

def discover_tools(tool_package):
    """
    Discovers and imports all modules in a given package to register tools.

    Args:
        tool_package: The package to search for tools (e.g., the 'tools' module).
    """
    # Use the package's __path__ to find modules
    for _, name, _ in pkgutil.iter_modules(tool_package.__path__):
        __import__(f"{tool_package.__name__}.{name}")

def get_tools() -> Dict[str, Callable]:
    """Returns a dictionary of all registered tools."""
    return _tool_registry

def get_tool_descriptions() -> str:
    """Returns a formatted string describing all available tools."""
    if not _tool_registry:
        return "No tools available."

    descriptions = ["Available tools:"]
    for name, func in _tool_registry.items():
        # Generate a schema from the function signature
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or "No description."
        
        params = []
        for param in sig.parameters.values():
            param_type = str(param.annotation).replace('typing.', '')
            params.append(f"{param.name}: {param_type}")
        
        param_str = ", ".join(params)
        descriptions.append(f"- {name}({param_str}): {doc}")
        
    return "\n".join(descriptions)

def execute_tool(name: str, **kwargs: Any) -> Any:
    """
    Executes a tool by its name with the given arguments.

    Args:
        name: The name of the tool to execute.
        **kwargs: The arguments to pass to the tool.

    Returns:
        The result of the tool's execution.
    """
    if name not in _tool_registry:
        return f"Error: Tool '{name}' not found."
    
    try:
        tool_func = _tool_registry[name]
        return tool_func(**kwargs)
    except Exception as e:
        return f"Error executing tool '{name}': {e}"

if __name__ == "__main__":
    # This is a dummy example. To make it work, you need the 'tools' package.
    print("Testing ToolManager...")

    # Create a dummy tool for testing
    @register_tool
    def say_hello(name: str = "World") -> str:
        """Says hello to someone."""
        return f"Hello, {name}!"

    print("Registered tools:")
    print(get_tool_descriptions())

    print("\nExecuting 'say_hello' with default name:")
    result = execute_tool("say_hello")
    print(f"Result: {result}")
    assert result == "Hello, World!"

    print("\nExecuting 'say_hello' with a specific name:")
    result = execute_tool("say_hello", name="Alice")
    print(f"Result: {result}")
    assert result == "Hello, Alice!"

    print("\nToolManager test passed!")
