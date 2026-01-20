# OpenManus Complete Agent Development Guide

**Version**: 2.0
**Date**: 2026-01-20
**Purpose**: Comprehensive guide for agent development, architecture, and advanced patterns

---

## 📚 Table of Contents

### Part I: Foundation
1. [System Overview](#system-overview)
2. [Architecture Foundation](#architecture-foundation)
3. [Core Components](#core-components)

### Part II: Agent Development
4. [Creating Your First Agent](#creating-your-first-agent)
5. [Tool Integration](#tool-integration)
6. [MCP Integration](#mcp-integration)
7. [Prompt Engineering](#prompt-engineering)

### Part III: Advanced Patterns
8. [Multi-Agent Flow Patterns](#multi-agent-flow-patterns)
9. [Custom Flow Control](#custom-flow-control)
10. [State Management](#state-management)
11. [Multi-Agent Orchestration](#multi-agent-orchestration)

### Part IV: Ready-to-Use Templates
12. [Agent Template Library](#agent-template-library)
13. [Implementation Examples](#implementation-examples)

### Part V: Production
14. [Testing Strategies](#testing-strategies)
15. [Performance Optimization](#performance-optimization)
16. [Best Practices](#best-practices)
17. [Troubleshooting](#troubleshooting)

---

## Part I: Foundation

## 1. System Overview {#system-overview}

OpenManus is a powerful AI agent framework based on the **ReAct (Reason-Act) paradigm**, providing flexible architecture for creating custom agents with tool execution capabilities.

### Key Concepts

- **ReAct Loop**: Think → Act → Observe cycle for decision-making
- **Tool-Driven**: Agents accomplish tasks through tool execution
- **Memory-Based**: Maintains conversation context and state
- **LLM-Powered**: Uses language models for reasoning
- **MCP-Enabled**: Supports remote tool execution via Model Context Protocol
- **Flow-Flexible**: Not limited to ReAct, supports multiple flow patterns

### When to Create Custom Agents

Create custom agents when you need:
- Specialized domain expertise
- Custom tool combinations
- Specific prompt strategies
- Unique context management
- Alternative flow patterns
- Performance optimizations

---

## 2. Architecture Foundation {#architecture-foundation}

### Three-Layer Inheritance Hierarchy

```
┌─────────────────────────────────────────────┐
│              BaseAgent (Abstract)            │
│  • Execution loop (run)                      │
│  • State management (IDLE/RUNNING/FINISHED)  │
│  • Memory management                         │
└─────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────┐
│             ReActAgent (Abstract)            │
│  • ReAct pattern definition                  │
│  • step() = think() + act()                 │
│  • Abstract think() and act()               │
└─────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────┐
│           ToolCallAgent (Concrete)           │
│  • LLM integration                          │
│  • Tool execution implementation            │
│  • Observation recording                    │
│  • Default think() and act()                │
└─────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────┐
│          Your Custom Agent                   │
│  • Domain-specific logic                    │
│  • Custom tools                             │
│  • Specialized prompts                      │
│  • Override think()/act() as needed         │
└─────────────────────────────────────────────┘
```

### Complete System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     OpenManus System                      │
├──────────────────────────────────────────────────────────┤
│                      Agent Layer                          │
│  ┌────────────────────────────────────────────────┐      │
│  │               Custom Agents                     │      │
│  │  (Manus, SWE, Research, DataAnalysis, etc.)   │      │
│  └────────────────────────────────────────────────┘      │
│                           ↓                               │
│  ┌────────────────────────────────────────────────┐      │
│  │              ToolCallAgent                      │      │
│  │         (Default ReAct Implementation)          │      │
│  └────────────────────────────────────────────────┘      │
├──────────────────────────────────────────────────────────┤
│                    Integration Layer                      │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │   Prompts   │ │     Tools     │ │    Memory    │      │
│  │  • System   │ │  • Local      │ │  • Standard  │      │
│  │  • Context  │ │  • MCP Remote │ │  • Enhanced  │      │
│  │  • Dynamic  │ │  • Custom     │ │  • Sliding   │      │
│  └─────────────┘ └──────────────┘ └──────────────┘      │
├──────────────────────────────────────────────────────────┤
│                      LLM Layer                            │
│  ┌────────────────────────────────────────────────┐      │
│  │          Language Model Interface               │      │
│  │     (OpenAI, Anthropic, Local Models)          │      │
│  └────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────┘
```

---

## 3. Core Components {#core-components}

### Component Reference Table

| Component | Purpose | Key Methods | Location |
|-----------|---------|-------------|----------|
| **BaseAgent** | Execution loop & state | `run()`, `step()` | `app/agent/base.py` |
| **ReActAgent** | ReAct pattern | `think()`, `act()` | `app/agent/react.py` |
| **ToolCallAgent** | Tool execution | `execute_tool()` | `app/agent/toolcall.py` |
| **Memory** | Context management | `add_message()` | `app/schema.py` |
| **ToolCollection** | Tool registry | `to_params()` | `app/tool/tool_collection.py` |
| **MCPClients** | Remote tools | `connect_*()` | `app/tool/mcp.py` |
| **LLM** | Model interface | `ask_tool()` | `app/llm.py` |

### Memory System

```python
# Standard Memory
Memory(
    messages: List[Message],
    max_messages: int = 100
)

# Enhanced Memory (with optimization)
EnhancedMemory(
    window: MemoryWindow,
    summary: MemorySummary,
    archived_messages: List[Message]
)
```

### Tool System

```python
# Tool hierarchy
BaseTool
├── LocalTool (PythonExecute, Bash, etc.)
├── MCPClientTool (Remote tool proxy)
└── CustomTool (Your implementations)

# Tool Collection
ToolCollection(
    tools: Tuple[BaseTool],
    tool_map: Dict[str, BaseTool]
)
```

---

## Part II: Agent Development

## 4. Creating Your First Agent {#creating-your-first-agent}

### Step-by-Step Guide

#### Step 1: Basic Agent Structure

```python
# app/agent/my_agent.py
from typing import List, Optional
from pydantic import Field

from app.agent.toolcall import ToolCallAgent
from app.tool import ToolCollection, Terminate
from app.schema import Message

class MyAgent(ToolCallAgent):
    """Your agent's description"""

    # === METADATA ===
    name: str = "my_agent"
    description: str = "An agent specialized in [your domain]"

    # === PROMPTS ===
    system_prompt: str = """
    You are a helpful assistant specialized in [domain].

    Your capabilities:
    - [Capability 1]
    - [Capability 2]

    Guidelines:
    - [Guideline 1]
    - [Guideline 2]
    """

    next_step_prompt: str = ""  # Optional guidance

    # === TOOLS ===
    available_tools: ToolCollection = ToolCollection(
        # Add your tools here
        Terminate()  # Always include
    )

    # === CONFIGURATION ===
    max_steps: int = 30
    max_observe: int = 2000  # Max chars for tool output

    # === CUSTOM ATTRIBUTES ===
    domain_specific_attr: str = "value"
```

#### Step 2: Add Tools

```python
from app.tool import PythonExecute, WebSearch, BrowserUseTool

class MyAgent(ToolCallAgent):
    available_tools: ToolCollection = ToolCollection(
        PythonExecute(),      # Code execution
        WebSearch(),          # Web searching
        BrowserUseTool(),     # Browser automation
        Terminate()           # Graceful exit
    )

    # Mark special tools (like Terminate)
    special_tool_names: List[str] = Field(
        default_factory=lambda: [Terminate().name]
    )
```

#### Step 3: Override Core Methods (Optional)

```python
class MyAgent(ToolCallAgent):

    async def initialize(self):
        """Custom initialization"""
        logger.info(f"Initializing {self.name}")
        # Setup resources, connections, etc.
        await super().initialize() if hasattr(super(), 'initialize') else None

    async def think(self) -> bool:
        """Enhanced thinking process"""
        # Pre-thinking: Add context
        if self.needs_special_context():
            self.inject_special_context()

        # Call parent's think
        result = await super().think()

        # Post-thinking: Analyze decisions
        if result:
            self.analyze_tool_selection()

        return result

    async def act(self) -> str:
        """Enhanced action execution"""
        # Pre-action: Validate
        if not self.validate_actions():
            return "Action validation failed"

        # Execute actions
        result = await super().act()

        # Post-action: Update state
        self.update_domain_state(result)

        return result

    def inject_special_context(self):
        """Add domain-specific context"""
        context = f"Current state: {self.get_state()}"
        self.next_step_prompt = f"{context}\n{self.next_step_prompt}"
```

#### Step 4: Implement Domain Logic

```python
class MyAgent(ToolCallAgent):

    # Domain-specific state
    task_queue: List[Task] = Field(default_factory=list)
    completed_tasks: List[Task] = Field(default_factory=list)

    def analyze_task(self, user_input: str) -> List[Task]:
        """Break down user input into tasks"""
        # Your domain logic
        tasks = []
        if "analyze" in user_input:
            tasks.append(Task("analysis", priority=1))
        if "report" in user_input:
            tasks.append(Task("reporting", priority=2))
        return tasks

    def prioritize_tasks(self):
        """Sort tasks by priority"""
        self.task_queue.sort(key=lambda t: t.priority)

    async def process_next_task(self) -> str:
        """Process highest priority task"""
        if not self.task_queue:
            return "No tasks to process"

        task = self.task_queue.pop(0)
        result = await self.execute_task(task)
        self.completed_tasks.append(task)

        return result
```

---

## 5. Tool Integration {#tool-integration}

### Tool Integration Patterns

#### Pattern 1: Static Tool Set
```python
class StaticToolAgent(ToolCallAgent):
    """Agent with fixed tool set"""

    available_tools: ToolCollection = ToolCollection(
        Tool1(),
        Tool2(),
        Tool3(),
        Terminate()
    )
```

#### Pattern 2: Dynamic Tool Loading
```python
class DynamicToolAgent(ToolCallAgent):
    """Agent that loads tools based on context"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_tools_for_task()

    def load_tools_for_task(self):
        """Load tools dynamically"""
        task_type = self.analyze_task()

        if task_type == "web_research":
            self.add_tool(WebSearch())
            self.add_tool(BrowserUseTool())
        elif task_type == "code_generation":
            self.add_tool(PythonExecute())
            self.add_tool(StrReplaceEditor())

    def add_tool(self, tool: BaseTool):
        """Add tool to collection"""
        self.available_tools.add_tools(tool)
```

#### Pattern 3: Tool Composition
```python
class CompositeToolAgent(ToolCallAgent):
    """Agent that combines tools into higher-level operations"""

    async def execute_composite_action(self, action: str):
        """Execute multiple tools in sequence"""
        if action == "analyze_and_report":
            # Step 1: Gather data
            data = await self.execute_tool_by_name(
                "web_search",
                query="latest trends"
            )

            # Step 2: Process data
            analysis = await self.execute_tool_by_name(
                "python_execute",
                code=f"analyze_data({data})"
            )

            # Step 3: Generate report
            report = await self.execute_tool_by_name(
                "create_report",
                content=analysis
            )

            return report

    async def execute_tool_by_name(self, name: str, **kwargs):
        """Helper to execute tool by name"""
        tool = self.available_tools.get_tool(name)
        if tool:
            return await tool.execute(**kwargs)
        return f"Tool {name} not found"
```

#### Pattern 4: Custom Tool Creation
```python
from app.tool.base import BaseTool, ToolResult

class CustomAnalysisTool(BaseTool):
    """Custom tool for specialized analysis"""

    name: str = "custom_analysis"
    description: str = "Performs domain-specific analysis"

    parameters: dict = {
        "type": "object",
        "properties": {
            "data": {"type": "string", "description": "Data to analyze"},
            "method": {"type": "string", "enum": ["quick", "deep"]}
        },
        "required": ["data"]
    }

    async def execute(self, data: str, method: str = "quick") -> ToolResult:
        """Execute the analysis"""
        try:
            if method == "quick":
                result = self.quick_analysis(data)
            else:
                result = self.deep_analysis(data)

            return ToolResult(output=result)
        except Exception as e:
            return ToolResult(error=f"Analysis failed: {str(e)}")

    def quick_analysis(self, data: str) -> str:
        # Implementation
        return f"Quick analysis of {len(data)} characters"

    def deep_analysis(self, data: str) -> str:
        # Implementation
        return f"Deep analysis completed"

# Use in agent
class AnalysisAgent(ToolCallAgent):
    available_tools: ToolCollection = ToolCollection(
        CustomAnalysisTool(),
        Terminate()
    )
```

---

## 6. MCP Integration {#mcp-integration}

### Understanding MCP Architecture

MCP (Model Context Protocol) enables remote tool execution. **MCP is integrated through the Tool system**, not as a separate component.

```
Agent → ToolCollection → MCPClientTool → Remote MCP Server
                ↓                ↓
           Local Tools      (Acts as proxy)
```

### How MCP Works

1. **Connection**: Agent connects to MCP server
2. **Discovery**: Server lists available tools
3. **Wrapping**: Each remote tool wrapped in `MCPClientTool`
4. **Registration**: MCPClientTools added to agent's `available_tools`
5. **Execution**: Transparent remote execution via proxy

### MCP Integration Patterns

#### Pattern 1: Basic MCP Connection
```python
from app.tool.mcp import MCPClients

class MCPEnabledAgent(ToolCallAgent):
    """Agent with MCP support"""

    mcp_clients: MCPClients = Field(default_factory=MCPClients)

    async def initialize(self):
        """Initialize MCP connections"""
        # Connect via stdio
        await self.mcp_clients.connect_stdio(
            command="node",
            args=["servers/filesystem.js"],
            server_id="filesystem"
        )

        # Connect via SSE
        await self.mcp_clients.connect_sse(
            server_url="https://api.example.com/mcp",
            server_id="api_gateway"
        )

        # Add MCP tools to available tools
        for tool in self.mcp_clients.tools:
            self.available_tools.add(tool)
```

#### Pattern 2: Dynamic MCP Server Selection
```python
class DynamicMCPAgent(ToolCallAgent):
    """Agent that connects to MCP servers on demand"""

    mcp_registry = {
        "file_operations": {
            "server_id": "filesystem",
            "command": "node servers/fs.js",
            "capabilities": ["read", "write", "list"]
        },
        "database": {
            "server_id": "database",
            "command": "python servers/db.py",
            "capabilities": ["query", "update"]
        },
        "external_apis": {
            "server_id": "api_gateway",
            "url": "https://api.example.com/mcp",
            "capabilities": ["rest", "graphql"]
        }
    }

    async def connect_for_capability(self, capability: str):
        """Connect to servers providing specific capability"""
        for name, config in self.mcp_registry.items():
            if capability in config.get("capabilities", []):
                if config["server_id"] not in self.mcp_clients.sessions:
                    if "command" in config:
                        await self.mcp_clients.connect_stdio(
                            command=config["command"],
                            args=config.get("args", []),
                            server_id=config["server_id"]
                        )
                    elif "url" in config:
                        await self.mcp_clients.connect_sse(
                            server_url=config["url"],
                            server_id=config["server_id"]
                        )

    async def think(self) -> bool:
        """Think with dynamic MCP connection"""
        # Analyze what capabilities are needed
        needed_capabilities = self.analyze_task_requirements()

        # Connect to required servers
        for capability in needed_capabilities:
            await self.connect_for_capability(capability)

        # Update available tools
        self.refresh_mcp_tools()

        # Continue with normal thinking
        return await super().think()
```

#### Pattern 3: MCP Server Pool Management
```python
class MCPPoolAgent(ToolCallAgent):
    """Agent with MCP server pool management"""

    class MCPServerPool:
        """Manages pool of MCP connections"""

        def __init__(self, max_connections: int = 5):
            self.max_connections = max_connections
            self.active_connections: Dict[str, ClientSession] = {}
            self.connection_queue: List[str] = []

        async def get_connection(self, server_id: str) -> ClientSession:
            """Get or create connection with pooling"""
            if server_id in self.active_connections:
                return self.active_connections[server_id]

            if len(self.active_connections) >= self.max_connections:
                # Remove least recently used
                lru_id = self.connection_queue.pop(0)
                await self.disconnect(lru_id)

            # Create new connection
            session = await self.connect(server_id)
            self.active_connections[server_id] = session
            self.connection_queue.append(server_id)

            return session

    server_pool: MCPServerPool = Field(
        default_factory=lambda: MCPServerPool(max_connections=5)
    )
```

### MCP Tool Namespacing

```python
class NamespacedMCPAgent(ToolCallAgent):
    """Agent with organized MCP tools"""

    def organize_tools_by_namespace(self):
        """Organize tools into logical namespaces"""
        self.tool_namespaces = {
            "local": [],
            "mcp": {}
        }

        for tool in self.available_tools.tools:
            if isinstance(tool, MCPClientTool):
                server_id = tool.server_id
                if server_id not in self.tool_namespaces["mcp"]:
                    self.tool_namespaces["mcp"][server_id] = []
                self.tool_namespaces["mcp"][server_id].append(tool)
            else:
                self.tool_namespaces["local"].append(tool)

    def list_available_namespaces(self) -> List[str]:
        """List all available namespaces"""
        namespaces = ["local"]
        namespaces.extend(self.tool_namespaces["mcp"].keys())
        return namespaces
```

---

## 7. Prompt Engineering {#prompt-engineering}

### Prompt System Architecture

```
┌─────────────────────────────────────┐
│         System Prompt               │ ← Core identity & capabilities
├─────────────────────────────────────┤
│      Context Prompts (Dynamic)      │ ← Runtime state injection
├─────────────────────────────────────┤
│       Task Prompt (User Input)      │ ← What the user wants
├─────────────────────────────────────┤
│    Next Step Prompt (Guidance)      │ ← How to proceed
├─────────────────────────────────────┤
│     Few-Shot Examples (Optional)    │ ← Learning from examples
└─────────────────────────────────────┘
```

### Prompt Design Patterns

#### Pattern 1: Static System Prompt
```python
SPECIALIZED_SYSTEM_PROMPT = """
You are {agent_name}, a specialized AI assistant for {domain}.

Core Identity:
- Role: {role}
- Expertise: {expertise}
- Personality: {personality}

Capabilities:
{capabilities}

Operating Principles:
{principles}

Constraints:
{constraints}
"""

class SpecializedAgent(ToolCallAgent):
    system_prompt: str = SPECIALIZED_SYSTEM_PROMPT.format(
        agent_name="DataWizard",
        domain="data analysis and visualization",
        role="Senior Data Scientist",
        expertise="Statistical analysis, ML, visualization",
        personality="Analytical, detail-oriented, helpful",
        capabilities="""
        - Statistical hypothesis testing
        - Machine learning model development
        - Data visualization and storytelling
        - Big data processing
        """,
        principles="""
        1. Always validate data quality first
        2. Choose appropriate statistical methods
        3. Communicate insights clearly
        4. Consider ethical implications
        """,
        constraints="""
        - Never expose sensitive data
        - Respect privacy regulations
        - Acknowledge uncertainty in predictions
        """
    )
```

#### Pattern 2: Dynamic Context Injection
```python
class ContextAwareAgent(ToolCallAgent):
    """Agent with sophisticated context management"""

    base_system_prompt: str = "You are a helpful assistant."

    def build_dynamic_context(self) -> Dict[str, str]:
        """Build context components"""
        return {
            "temporal": f"Current time: {datetime.now()}",
            "environment": f"Environment: {self.environment}",
            "state": f"Current state: {self.current_state}",
            "progress": self.get_progress_context(),
            "history": self.get_history_summary(),
            "constraints": self.get_active_constraints()
        }

    def inject_context(self, context_type: str = "all"):
        """Inject specific context types"""
        contexts = self.build_dynamic_context()

        if context_type == "all":
            context_str = "\n".join(contexts.values())
        else:
            context_str = contexts.get(context_type, "")

        # Update prompts with context
        self.system_prompt = f"{self.base_system_prompt}\n\n{context_str}"

    async def think(self) -> bool:
        """Think with dynamic context"""
        self.inject_context("all")
        return await super().think()
```

#### Pattern 3: Conditional Prompting
```python
class ConditionalPromptAgent(ToolCallAgent):
    """Agent with phase-based prompts"""

    prompt_library = {
        "exploration": """
        You are in exploration mode.
        - Gather broad information
        - Ask clarifying questions
        - Identify constraints
        - Map the problem space
        """,

        "planning": """
        You are in planning mode.
        - Create detailed action plans
        - Identify dependencies
        - Estimate resources
        - Set success criteria
        """,

        "execution": """
        You are in execution mode.
        - Follow the plan precisely
        - Handle errors gracefully
        - Optimize for efficiency
        - Report progress clearly
        """,

        "validation": """
        You are in validation mode.
        - Verify against requirements
        - Test edge cases
        - Check quality standards
        - Document findings
        """,

        "optimization": """
        You are in optimization mode.
        - Identify bottlenecks
        - Improve performance
        - Reduce resource usage
        - Enhance user experience
        """
    }

    current_phase: str = "exploration"

    def transition_to_phase(self, phase: str):
        """Transition to new phase with appropriate prompt"""
        if phase in self.prompt_library:
            self.current_phase = phase
            self.system_prompt = self.prompt_library[phase]
            logger.info(f"Transitioned to {phase} phase")
```

#### Pattern 4: Role-Based Prompting
```python
class RoleBasedAgent(ToolCallAgent):
    """Agent that can switch between roles"""

    roles = {
        "architect": {
            "prompt": """
            You are a Software Architect.
            Focus: System design, patterns, scalability
            Approach: Big picture, strategic thinking
            """,
            "preferred_tools": ["diagram_tool", "architecture_analyzer"],
            "decision_style": "deliberative"
        },

        "developer": {
            "prompt": """
            You are a Senior Developer.
            Focus: Clean code, performance, testing
            Approach: Practical, hands-on implementation
            """,
            "preferred_tools": ["python_execute", "str_replace_editor"],
            "decision_style": "pragmatic"
        },

        "reviewer": {
            "prompt": """
            You are a Code Reviewer.
            Focus: Quality, security, best practices
            Approach: Critical analysis, constructive feedback
            """,
            "preferred_tools": ["code_analyzer", "security_scanner"],
            "decision_style": "analytical"
        }
    }

    current_role: str = "developer"

    def switch_role(self, role: str, reason: str = ""):
        """Switch to different role"""
        if role in self.roles:
            self.current_role = role
            role_config = self.roles[role]

            # Update prompt
            self.system_prompt = role_config["prompt"]

            # Adjust tool preferences
            self.preferred_tools = role_config["preferred_tools"]

            # Log role switch
            logger.info(f"Switched to {role} role: {reason}")
```

#### Pattern 5: Few-Shot Learning
```python
class FewShotAgent(ToolCallAgent):
    """Agent with example-based learning"""

    examples = [
        {
            "input": "Analyze the sales data for Q1",
            "thinking": "I need to load Q1 data and perform analysis",
            "actions": [
                ("python_execute", "df = load_data('q1_sales.csv')"),
                ("python_execute", "analysis = analyze_sales(df)"),
                ("create_report", "Q1 Sales Analysis: ...")
            ],
            "output": "Q1 showed 15% growth..."
        },
        {
            "input": "Create a visualization of trends",
            "thinking": "I'll create charts showing trend patterns",
            "actions": [
                ("python_execute", "import matplotlib.pyplot as plt"),
                ("python_execute", "create_trend_charts(data)"),
                ("save_file", "trends.png")
            ],
            "output": "Trend visualization saved"
        }
    ]

    def build_few_shot_prompt(self) -> str:
        """Build prompt with examples"""
        prompt = self.system_prompt + "\n\nExamples:\n"

        for i, example in enumerate(self.examples, 1):
            prompt += f"""
Example {i}:
User: {example['input']}
Thinking: {example['thinking']}
Actions: {', '.join(f"{a[0]}({a[1][:30]}...)" for a in example['actions'])}
Result: {example['output']}
"""

        return prompt

    async def think(self) -> bool:
        """Think with few-shot examples"""
        self.system_prompt = self.build_few_shot_prompt()
        return await super().think()
```

---

## Part III: Advanced Patterns

## 8. Multi-Agent Flow Patterns {#multi-agent-flow-patterns}

### Beyond ReAct: Alternative Flow Patterns

The OpenManus architecture supports multiple flow patterns beyond the default ReAct pattern:

#### 1. Plan-Execute Pattern
```python
class PlanExecuteAgent(BaseAgent):
    """Separates planning from execution"""

    plan: List[Step] = Field(default_factory=list)
    execution_index: int = 0

    async def step(self) -> str:
        """Plan then execute pattern"""
        if not self.plan:
            # Planning phase
            self.plan = await self.create_plan()
            return f"Created plan with {len(self.plan)} steps"

        if self.execution_index < len(self.plan):
            # Execution phase
            step = self.plan[self.execution_index]
            result = await self.execute_plan_step(step)
            self.execution_index += 1
            return f"Step {self.execution_index}: {result}"

        return "Plan execution complete"

    async def create_plan(self) -> List[Step]:
        """Create execution plan using LLM"""
        planning_prompt = """
        Create a detailed plan for: {task}
        Break it down into specific, executable steps.
        """
        response = await self.llm.ask(planning_prompt.format(task=self.task))
        return self.parse_plan(response)
```

#### 2. Hierarchical Task Network (HTN)
```python
class HTNAgent(BaseAgent):
    """Hierarchical task decomposition"""

    task_hierarchy: Dict[str, List[str]] = {
        "build_app": ["design", "implement", "test", "deploy"],
        "design": ["requirements", "architecture", "ui_design"],
        "implement": ["backend", "frontend", "integration"],
        "test": ["unit_tests", "integration_tests", "e2e_tests"]
    }

    async def decompose_task(self, task: str) -> List[str]:
        """Recursively decompose tasks"""
        if task not in self.task_hierarchy:
            # Primitive task
            return [task]

        subtasks = []
        for subtask in self.task_hierarchy[task]:
            subtasks.extend(await self.decompose_task(subtask))

        return subtasks

    async def step(self) -> str:
        """Execute hierarchical plan"""
        if not self.task_queue:
            # Decompose main task
            self.task_queue = await self.decompose_task(self.main_task)

        if self.task_queue:
            task = self.task_queue.pop(0)
            result = await self.execute_primitive_task(task)
            return f"Completed: {task}"

        return "All tasks complete"
```

#### 3. Belief-Desire-Intention (BDI)
```python
class BDIAgent(BaseAgent):
    """BDI cognitive architecture"""

    beliefs: Dict[str, Any] = Field(default_factory=dict)
    desires: List[Goal] = Field(default_factory=list)
    intentions: List[Plan] = Field(default_factory=list)

    async def step(self) -> str:
        """BDI reasoning cycle"""
        # Sense: Update beliefs from environment
        await self.update_beliefs()

        # Deliberate: Generate desires from beliefs
        self.desires = self.generate_desires()

        # Means-end reasoning: Select intentions
        self.intentions = self.select_intentions()

        # Act: Execute current intention
        if self.intentions:
            plan = self.intentions[0]
            action = plan.get_next_action()
            result = await self.execute_action(action)

            if plan.is_complete():
                self.intentions.pop(0)

            return f"Executed: {action}"

        return "No active intentions"

    async def update_beliefs(self):
        """Update beliefs from perception"""
        self.beliefs["time"] = datetime.now()
        self.beliefs["resources"] = await self.check_resources()
        self.beliefs["task_state"] = await self.assess_task_state()
```

#### 4. State Machine Pattern
```python
from enum import Enum, auto

class AgentState(Enum):
    IDLE = auto()
    ANALYZING = auto()
    PLANNING = auto()
    EXECUTING = auto()
    VALIDATING = auto()
    ERROR_RECOVERY = auto()
    COMPLETE = auto()

class StateMachineAgent(BaseAgent):
    """Explicit state machine control"""

    state: AgentState = AgentState.IDLE

    state_transitions = {
        AgentState.IDLE: [AgentState.ANALYZING],
        AgentState.ANALYZING: [AgentState.PLANNING, AgentState.ERROR_RECOVERY],
        AgentState.PLANNING: [AgentState.EXECUTING, AgentState.ERROR_RECOVERY],
        AgentState.EXECUTING: [AgentState.VALIDATING, AgentState.ERROR_RECOVERY],
        AgentState.VALIDATING: [AgentState.COMPLETE, AgentState.EXECUTING],
        AgentState.ERROR_RECOVERY: [AgentState.ANALYZING, AgentState.IDLE],
        AgentState.COMPLETE: []
    }

    state_handlers = {
        AgentState.ANALYZING: "analyze_problem",
        AgentState.PLANNING: "create_plan",
        AgentState.EXECUTING: "execute_plan",
        AgentState.VALIDATING: "validate_results",
        AgentState.ERROR_RECOVERY: "recover_from_error"
    }

    async def step(self) -> str:
        """Execute state machine step"""
        # Execute current state
        handler_name = self.state_handlers.get(self.state)
        if handler_name:
            handler = getattr(self, handler_name)
            result = await handler()
        else:
            result = "No handler for state"

        # Determine next state
        next_state = self.determine_next_state(result)

        # Validate transition
        if next_state in self.state_transitions[self.state]:
            logger.info(f"State transition: {self.state} → {next_state}")
            self.state = next_state
        else:
            raise ValueError(f"Invalid transition: {self.state} → {next_state}")

        return f"[{self.state}] {result}"
```

#### 5. Pipeline Pattern
```python
class PipelineAgent(BaseAgent):
    """Sequential pipeline processing"""

    pipeline = [
        ("validate", validate_input),
        ("preprocess", preprocess_data),
        ("analyze", analyze_data),
        ("postprocess", postprocess_results),
        ("report", generate_report)
    ]

    stage_index: int = 0
    pipeline_data: Any = None

    async def step(self) -> str:
        """Execute pipeline stage"""
        if self.stage_index >= len(self.pipeline):
            return "Pipeline complete"

        stage_name, stage_func = self.pipeline[self.stage_index]

        # Execute stage
        self.pipeline_data = await stage_func(self.pipeline_data)

        self.stage_index += 1

        return f"Completed stage {stage_name}"
```

#### 6. Blackboard Pattern
```python
class BlackboardAgent(BaseAgent):
    """Collaborative problem solving with blackboard"""

    class Blackboard:
        """Shared knowledge space"""
        def __init__(self):
            self.facts: Dict[str, Any] = {}
            self.hypotheses: List[Hypothesis] = []
            self.solutions: List[Solution] = []
            self.constraints: List[Constraint] = []

    blackboard: Blackboard = Field(default_factory=Blackboard)
    knowledge_sources: List[KnowledgeSource] = []

    async def step(self) -> str:
        """Blackboard problem-solving step"""
        # Find applicable knowledge source
        applicable_ks = self.find_applicable_knowledge_source()

        if applicable_ks:
            # Apply knowledge source to blackboard
            contribution = await applicable_ks.contribute(self.blackboard)

            # Update blackboard
            self.update_blackboard(contribution)

            return f"Applied {applicable_ks.name}"

        # Check if solution found
        if self.is_solution_complete():
            return "Solution found"

        return "No applicable knowledge source"
```

---

## 9. Custom Flow Control {#custom-flow-control}

### Creating Your Own Flow Pattern

#### Base Template for Custom Flow
```python
from abc import ABC, abstractmethod

class CustomFlowAgent(BaseAgent, ABC):
    """Base template for custom flow patterns"""

    flow_state: Dict[str, Any] = Field(default_factory=dict)

    @abstractmethod
    async def initialize_flow(self) -> None:
        """Initialize flow-specific state"""
        pass

    @abstractmethod
    async def get_next_action(self) -> Optional[Action]:
        """Determine next action based on flow logic"""
        pass

    @abstractmethod
    async def process_result(self, action: Action, result: Any) -> None:
        """Process action result and update flow state"""
        pass

    @abstractmethod
    def is_complete(self) -> bool:
        """Check if flow is complete"""
        pass

    async def step(self) -> str:
        """Generic step for custom flows"""
        # Initialize on first step
        if not self.flow_state.get("initialized"):
            await self.initialize_flow()
            self.flow_state["initialized"] = True

        # Check completion
        if self.is_complete():
            return "Flow complete"

        # Get and execute next action
        action = await self.get_next_action()
        if action:
            result = await self.execute_action(action)
            await self.process_result(action, result)
            return f"Executed: {action.name}"

        return "No action available"
```

#### Example: Event-Driven Flow
```python
class EventDrivenAgent(CustomFlowAgent):
    """Event-driven flow pattern"""

    event_queue: List[Event] = Field(default_factory=list)
    event_handlers: Dict[str, Callable] = Field(default_factory=dict)

    async def initialize_flow(self) -> None:
        """Register event handlers"""
        self.event_handlers = {
            "data_received": self.handle_data_received,
            "error_occurred": self.handle_error,
            "user_input": self.handle_user_input,
            "timeout": self.handle_timeout
        }

    async def get_next_action(self) -> Optional[Action]:
        """Process next event from queue"""
        if not self.event_queue:
            # Wait for events or generate them
            await self.poll_for_events()

        if self.event_queue:
            event = self.event_queue.pop(0)
            handler = self.event_handlers.get(event.type)

            if handler:
                action = await handler(event)
                return action

        return None

    async def process_result(self, action: Action, result: Any) -> None:
        """Generate new events based on results"""
        if "error" in str(result):
            self.event_queue.append(
                Event("error_occurred", {"result": result})
            )
        elif action.triggers_event:
            self.event_queue.append(
                Event(action.triggered_event, {"data": result})
            )
```

---

## 10. State Management {#state-management}

### Advanced State Management Patterns

#### Pattern 1: Persistent State
```python
class PersistentStateAgent(ToolCallAgent):
    """Agent with persistent state across sessions"""

    state_file: str = "agent_state.json"

    async def save_state(self):
        """Save state to disk"""
        state = {
            "memory": self.memory.to_dict_list(),
            "completed_tasks": self.completed_tasks,
            "configuration": self.get_config(),
            "timestamp": datetime.now().isoformat()
        }

        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    async def load_state(self) -> bool:
        """Load state from disk"""
        if not os.path.exists(self.state_file):
            return False

        with open(self.state_file, "r") as f:
            state = json.load(f)

        # Restore memory
        for msg_dict in state["memory"]:
            self.memory.add_message(Message.from_dict(msg_dict))

        self.completed_tasks = state["completed_tasks"]

        return True

    async def run(self) -> str:
        """Run with state persistence"""
        # Try to restore previous state
        restored = await self.load_state()

        if restored:
            logger.info("Restored from previous state")

        result = await super().run()

        # Save state after execution
        await self.save_state()

        return result
```

#### Pattern 2: Distributed State
```python
class DistributedStateAgent(ToolCallAgent):
    """Agent with distributed state management"""

    redis_client: Optional[Redis] = None
    state_namespace: str = "agent_state"

    async def initialize(self):
        """Initialize distributed state"""
        self.redis_client = Redis(
            host="localhost",
            port=6379,
            decode_responses=True
        )

    async def get_shared_state(self, key: str) -> Any:
        """Get state from distributed store"""
        value = await self.redis_client.get(
            f"{self.state_namespace}:{key}"
        )
        return json.loads(value) if value else None

    async def set_shared_state(self, key: str, value: Any):
        """Set state in distributed store"""
        await self.redis_client.set(
            f"{self.state_namespace}:{key}",
            json.dumps(value),
            ex=3600  # 1 hour expiry
        )

    async def coordinate_with_peers(self):
        """Coordinate with other agent instances"""
        # Register self
        await self.redis_client.sadd(
            "active_agents",
            self.agent_id
        )

        # Get peer list
        peers = await self.redis_client.smembers("active_agents")

        # Share state
        await self.broadcast_state(peers)
```

---

## 11. Multi-Agent Orchestration {#multi-agent-orchestration}

### Orchestration Patterns

#### Pattern 1: Sequential Orchestration
```python
class SequentialOrchestrator:
    """Run agents in sequence"""

    agents: List[BaseAgent]

    async def run(self) -> List[str]:
        """Execute agents sequentially"""
        results = []
        context = {}

        for i, agent in enumerate(self.agents):
            logger.info(f"Running agent {i+1}/{len(self.agents)}: {agent.name}")

            # Pass context from previous agent
            if results:
                agent.set_context(context)

            # Run agent
            result = await agent.run()
            results.append(result)

            # Extract context for next agent
            context = agent.get_output_context()

        return results
```

#### Pattern 2: Parallel Orchestration
```python
class ParallelOrchestrator:
    """Run agents in parallel"""

    agents: List[BaseAgent]
    max_concurrency: int = 5

    async def run(self) -> List[str]:
        """Execute agents in parallel with concurrency limit"""
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def run_with_limit(agent: BaseAgent) -> str:
            async with semaphore:
                return await agent.run()

        tasks = [run_with_limit(agent) for agent in self.agents]
        results = await asyncio.gather(*tasks)

        return results
```

#### Pattern 3: Graph-Based Orchestration
```python
class GraphOrchestrator:
    """DAG-based agent orchestration"""

    agent_graph = {
        "analyzer": {
            "agent": AnalyzerAgent(),
            "depends_on": [],
            "outputs_to": ["planner", "validator"]
        },
        "planner": {
            "agent": PlannerAgent(),
            "depends_on": ["analyzer"],
            "outputs_to": ["executor"]
        },
        "executor": {
            "agent": ExecutorAgent(),
            "depends_on": ["planner"],
            "outputs_to": ["validator"]
        },
        "validator": {
            "agent": ValidatorAgent(),
            "depends_on": ["analyzer", "executor"],
            "outputs_to": []
        }
    }

    async def run(self) -> Dict[str, Any]:
        """Execute DAG-based workflow"""
        results = {}
        completed = set()

        while len(completed) < len(self.agent_graph):
            # Find ready agents
            ready = []
            for name, node in self.agent_graph.items():
                if name not in completed:
                    deps_met = all(
                        dep in completed
                        for dep in node["depends_on"]
                    )
                    if deps_met:
                        ready.append(name)

            # Run ready agents in parallel
            if ready:
                tasks = []
                for name in ready:
                    agent = self.agent_graph[name]["agent"]

                    # Set inputs from dependencies
                    for dep in self.agent_graph[name]["depends_on"]:
                        agent.set_input(results[dep])

                    tasks.append(self.run_agent(name, agent))

                # Execute and collect results
                batch_results = await asyncio.gather(*tasks)

                for name, result in batch_results:
                    results[name] = result
                    completed.add(name)
            else:
                raise ValueError("Circular dependency detected")

        return results
```

#### Pattern 4: Hierarchical Orchestration
```python
class HierarchicalOrchestrator:
    """Multi-level agent hierarchy"""

    class TeamLead(ToolCallAgent):
        """Coordinates team of agents"""

        team: List[BaseAgent] = Field(default_factory=list)

        async def delegate_task(self, task: Task) -> Any:
            """Delegate to team member"""
            # Select best agent for task
            agent = self.select_agent_for_task(task)

            # Delegate and monitor
            result = await agent.run()

            # Review result
            if not self.approve_result(result):
                # Request revision
                agent.revise(self.feedback)
                result = await agent.run()

            return result

    ceo: BaseAgent  # Top-level coordinator
    directors: List[TeamLead]  # Department heads
    managers: List[TeamLead]  # Team leads
    workers: List[BaseAgent]  # Individual contributors

    async def run(self, objective: str) -> str:
        """Execute hierarchical organization"""
        # CEO creates strategy
        strategy = await self.ceo.create_strategy(objective)

        # Directors create plans
        plans = []
        for director in self.directors:
            plan = await director.create_plan(strategy)
            plans.append(plan)

        # Managers execute with teams
        results = []
        for manager, plan in zip(self.managers, plans):
            result = await manager.execute_plan(plan)
            results.append(result)

        # CEO reviews and integrates
        final = await self.ceo.integrate_results(results)

        return final
```

---

## Part IV: Ready-to-Use Templates

## 12. Agent Template Library {#agent-template-library}

### Research Agent Template

```python
class ResearchAgent(ToolCallAgent):
    """Complete research agent implementation"""

    name: str = "research_agent"
    description: str = "Expert researcher for information gathering"

    system_prompt: str = """
    You are a professional research assistant with expertise in:
    - Information gathering from multiple sources
    - Fact-checking and verification
    - Synthesizing complex information
    - Creating comprehensive reports

    Research methodology:
    1. Start with broad searches
    2. Identify credible sources
    3. Deep dive into specifics
    4. Cross-reference information
    5. Synthesize findings

    Always cite sources and distinguish facts from opinions.
    """

    available_tools: ToolCollection = ToolCollection(
        WebSearch(),
        BrowserUseTool(),
        Crawl4aiTool(),
        PythonExecute(),  # For data analysis
        FileOperations(), # For saving results
        Terminate()
    )

    # Research-specific configuration
    max_steps: int = 50
    max_observe: int = 5000
    require_citations: bool = True
    fact_check: bool = True

    # Research state
    sources: List[Source] = Field(default_factory=list)
    findings: List[Finding] = Field(default_factory=list)

    async def research_topic(self, topic: str) -> ResearchReport:
        """Complete research workflow"""
        # Phase 1: Broad search
        await self.broad_search(topic)

        # Phase 2: Source evaluation
        credible_sources = await self.evaluate_sources()

        # Phase 3: Deep analysis
        for source in credible_sources:
            findings = await self.analyze_source(source)
            self.findings.extend(findings)

        # Phase 4: Fact checking
        if self.fact_check:
            await self.verify_facts()

        # Phase 5: Synthesis
        report = await self.synthesize_report()

        return report
```

### Code Development Agent Template

```python
class CodeDevelopmentAgent(ToolCallAgent):
    """Complete code development agent"""

    name: str = "code_dev_agent"
    description: str = "Expert software developer"

    system_prompt: str = """
    You are an expert software developer with deep knowledge of:
    - Multiple programming languages
    - Design patterns and architecture
    - Testing and debugging
    - Performance optimization
    - Security best practices

    Development process:
    1. Understand requirements
    2. Design before implementing
    3. Write clean, tested code
    4. Optimize and refactor
    5. Document thoroughly
    """

    available_tools: ToolCollection = ToolCollection(
        PythonExecute(),
        StrReplaceEditor(),
        Bash(),
        FileOperations(),
        GitOperations(),
        TestRunner(),
        Terminate()
    )

    # Development configuration
    language: str = "python"
    style_guide: str = "pep8"
    test_coverage_target: float = 80.0

    async def develop_feature(self, spec: FeatureSpec) -> str:
        """Complete feature development"""
        # Design
        design = await self.design_solution(spec)

        # Implementation
        code = await self.implement_design(design)

        # Testing
        tests = await self.write_tests(code)
        coverage = await self.run_tests(tests)

        # Optimization
        if coverage < self.test_coverage_target:
            tests = await self.improve_tests(tests, coverage)

        optimized = await self.optimize_code(code)

        # Documentation
        docs = await self.document_code(optimized)

        return "Feature complete"
```

### Data Analysis Agent Template

```python
class DataAnalysisAgent(ToolCallAgent):
    """Complete data analysis agent"""

    name: str = "data_analysis_agent"
    description: str = "Expert data scientist"

    system_prompt: str = """
    You are a data scientist with expertise in:
    - Statistical analysis
    - Machine learning
    - Data visualization
    - Business intelligence

    Analysis workflow:
    1. Understand the question
    2. Explore and clean data
    3. Perform analysis
    4. Create visualizations
    5. Draw insights

    Use pandas, numpy, sklearn, matplotlib, seaborn.
    """

    available_tools: ToolCollection = ToolCollection(
        PythonExecute(),
        FileOperations(),
        DataVisualization(),
        StatisticalTests(),
        MLModeling(),
        Terminate()
    )

    # Analysis configuration
    auto_eda: bool = True
    visualization_style: str = "seaborn"

    async def analyze_dataset(self, data_path: str, question: str):
        """Complete data analysis workflow"""
        # Load and explore
        df = await self.load_data(data_path)

        if self.auto_eda:
            eda_report = await self.perform_eda(df)

        # Clean and prepare
        cleaned = await self.clean_data(df)

        # Analysis based on question
        if "predict" in question:
            result = await self.build_ml_model(cleaned)
        elif "correlat" in question:
            result = await self.correlation_analysis(cleaned)
        elif "trend" in question:
            result = await self.trend_analysis(cleaned)
        else:
            result = await self.general_analysis(cleaned)

        # Visualize
        visuals = await self.create_visualizations(result)

        # Report
        report = await self.generate_report(result, visuals)

        return report
```

### DevOps Agent Template

```python
class DevOpsAgent(ToolCallAgent):
    """Complete DevOps automation agent"""

    name: str = "devops_agent"
    description: str = "DevOps and infrastructure expert"

    system_prompt: str = """
    You are a senior DevOps engineer with expertise in:
    - Container orchestration (Docker, K8s)
    - CI/CD pipelines
    - Infrastructure as Code
    - Cloud platforms
    - Monitoring and observability

    Principles:
    - Automate everything
    - Ensure high availability
    - Security first
    - Cost optimization
    """

    available_tools: ToolCollection = ToolCollection(
        Bash(),
        DockerOperations(),
        KubernetesOperations(),
        TerraformOperations(),
        AWSOperations(),
        FileOperations(),
        Terminate()
    )

    # DevOps configuration
    environment: str = "staging"
    cloud_provider: str = "aws"
    require_approval: bool = True

    async def deploy_application(
        self,
        app_spec: AppSpec,
        target_env: str
    ):
        """Complete deployment workflow"""
        # Pre-deployment checks
        health = await self.health_check()

        if not health.is_healthy:
            await self.fix_issues(health.issues)

        # Build
        image = await self.build_container(app_spec)

        # Test
        test_result = await self.test_container(image)

        # Deploy
        if target_env == "production" and self.require_approval:
            approval = await self.request_approval()
            if not approval:
                return "Deployment cancelled"

        deployment = await self.deploy_to_environment(
            image,
            target_env
        )

        # Verify
        await self.verify_deployment(deployment)

        # Monitor
        await self.setup_monitoring(deployment)

        return f"Deployed to {target_env}"
```

### QA Testing Agent Template

```python
class QATestingAgent(ToolCallAgent):
    """Complete QA and testing agent"""

    name: str = "qa_testing_agent"
    description: str = "Quality assurance expert"

    system_prompt: str = """
    You are a senior QA engineer with expertise in:
    - Test strategy and planning
    - Automated testing
    - Performance testing
    - Security testing
    - Bug tracking

    Testing principles:
    - Test early and often
    - Automate repetitive tests
    - Focus on user scenarios
    - Consider edge cases
    """

    available_tools: ToolCollection = ToolCollection(
        PythonExecute(),  # For test scripts
        Bash(),           # For test runners
        BrowserUseTool(), # For UI testing
        APITester(),      # For API testing
        PerformanceTester(),
        SecurityScanner(),
        Terminate()
    )

    test_types: List[str] = [
        "unit", "integration", "e2e", "performance", "security"
    ]

    async def test_application(self, app: Application) -> TestReport:
        """Complete testing workflow"""
        report = TestReport()

        for test_type in self.test_types:
            # Generate test cases
            test_cases = await self.generate_test_cases(
                app,
                test_type
            )

            # Execute tests
            results = await self.execute_tests(
                test_cases,
                test_type
            )

            # Analyze results
            analysis = await self.analyze_test_results(results)

            # Report bugs
            bugs = await self.identify_bugs(analysis)

            for bug in bugs:
                bug_report = await self.create_bug_report(bug)
                report.add_bug(bug_report)

            report.add_test_results(test_type, results)

        return report
```

---

## 13. Implementation Examples {#implementation-examples}

### Example 1: Complete Research Pipeline

```python
class ResearchPipelineImplementation:
    """End-to-end research pipeline"""

    async def run_research_pipeline(self, topic: str) -> str:
        """Execute complete research workflow"""

        # Stage 1: Initial Research
        researcher = ResearchAgent()
        research_data = await researcher.research_topic(topic)

        # Stage 2: Data Analysis
        if research_data.has_quantitative_data:
            analyst = DataAnalysisAgent()
            analysis = await analyst.analyze_dataset(
                research_data.data,
                research_data.research_question
            )
        else:
            analysis = None

        # Stage 3: Report Generation
        reporter = DocumentationAgent()
        report = await reporter.generate_report({
            "research": research_data,
            "analysis": analysis,
            "topic": topic
        })

        # Stage 4: Quality Review
        reviewer = QATestingAgent()
        review = await reviewer.review_document(report)

        if review.needs_revision:
            report = await reporter.revise_report(
                report,
                review.feedback
            )

        return report
```

### Example 2: Full-Stack Development Workflow

```python
class FullStackDevelopmentWorkflow:
    """Complete application development"""

    async def develop_application(self, requirements: Requirements):
        """Build complete application"""

        # Architecture Design
        architect = ArchitectureAgent()
        design = await architect.design_system(requirements)

        # Backend Development
        backend_dev = CodeDevelopmentAgent(language="python")
        backend_code = await backend_dev.develop_feature(
            design.backend_spec
        )

        # Frontend Development
        frontend_dev = CodeDevelopmentAgent(language="typescript")
        frontend_code = await frontend_dev.develop_feature(
            design.frontend_spec
        )

        # Integration
        integrator = IntegrationAgent()
        integrated_app = await integrator.integrate_components({
            "backend": backend_code,
            "frontend": frontend_code
        })

        # Testing
        tester = QATestingAgent()
        test_report = await tester.test_application(integrated_app)

        # Deployment
        devops = DevOpsAgent()
        deployment = await devops.deploy_application(
            integrated_app,
            "staging"
        )

        return deployment
```

### Example 3: Dynamic MCP Integration

```python
class DynamicMCPWorkflow:
    """Workflow with dynamic MCP tool loading"""

    async def process_with_mcp(self, task: Task):
        """Process task with dynamic MCP tools"""

        agent = DynamicMCPAgent()

        # Analyze task requirements
        requirements = agent.analyze_task_requirements(task)

        # Connect to required MCP servers
        for capability in requirements.capabilities:
            await agent.connect_for_capability(capability)

        # Execute task with full toolset
        result = await agent.run()

        # Cleanup connections
        await agent.cleanup_mcp_connections()

        return result
```

---

## Part V: Production

## 14. Testing Strategies {#testing-strategies}

### Unit Testing

```python
import pytest
from unittest.mock import Mock, patch

class TestAgent:
    """Comprehensive agent testing"""

    @pytest.fixture
    def agent(self):
        """Create test agent"""
        return MyAgent()

    @pytest.mark.asyncio
    async def test_initialization(self, agent):
        """Test agent initialization"""
        assert agent.name == "my_agent"
        assert len(agent.available_tools.tools) > 0
        assert agent.max_steps == 30

    @pytest.mark.asyncio
    async def test_thinking_process(self, agent):
        """Test think method"""
        agent.memory.add_message(
            Message.user_message("Test task")
        )

        with patch.object(agent.llm, 'ask_tool') as mock_ask:
            mock_ask.return_value = Mock(
                tool_calls=[],
                content="Test response"
            )

            result = await agent.think()

            assert result is True
            assert len(agent.memory.messages) > 1

    @pytest.mark.asyncio
    async def test_tool_execution(self, agent):
        """Test tool execution"""
        with patch.object(agent, 'execute_tool') as mock_exec:
            mock_exec.return_value = "Tool executed"

            agent.tool_calls = [Mock(function=Mock(name="test_tool"))]
            result = await agent.act()

            assert mock_exec.called
            assert "Tool executed" in result
```

### Integration Testing

```python
class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete workflow"""
        agent = MyAgent()

        # Add initial task
        agent.memory.add_message(
            Message.user_message("Complete test task")
        )

        # Run agent
        result = await agent.run()

        # Verify results
        assert result is not None
        assert agent.state == AgentState.FINISHED
        assert len(agent.memory.messages) > 2

    @pytest.mark.asyncio
    async def test_mcp_integration(self):
        """Test MCP server integration"""
        agent = MCPEnabledAgent()

        # Mock MCP server
        with patch('app.tool.mcp.stdio_client') as mock_stdio:
            mock_stdio.return_value = Mock()

            await agent.initialize()

            assert len(agent.mcp_clients.sessions) > 0
```

### Performance Testing

```python
class TestPerformance:
    """Performance benchmarks"""

    @pytest.mark.asyncio
    async def test_response_time(self):
        """Test agent response time"""
        agent = MyAgent()

        start = time.time()
        await agent.run()
        duration = time.time() - start

        assert duration < 30  # Should complete within 30s

    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test memory consumption"""
        agent = MyAgent()

        # Measure initial memory
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Run agent
        await agent.run()

        # Check memory growth
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory

        assert memory_growth < 100 * 1024 * 1024  # Less than 100MB
```

---

## 15. Performance Optimization {#performance-optimization}

### Memory Optimization

```python
class OptimizedMemoryAgent(ToolCallAgent):
    """Agent with memory optimizations"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Use enhanced memory with sliding window
        from app.memory_manager import MemoryManager

        self.memory = MemoryManager.create_memory(
            strategy="enhanced",
            window_size=20,
            summary_threshold=30
        )

    async def think(self) -> bool:
        """Think with memory optimization"""
        # Get optimized context
        messages = self.memory.get_context_messages()

        # Log optimization stats
        logger.info(f"Context size: {len(messages)} messages")

        return await super().think()
```

### Tool Optimization

```python
class OptimizedToolAgent(ToolCallAgent):
    """Agent with tool optimizations"""

    # Cache tool results
    tool_cache: Dict[str, Any] = Field(default_factory=dict)

    async def execute_tool(self, tool_call) -> str:
        """Execute with caching"""
        # Generate cache key
        cache_key = f"{tool_call.function.name}:{tool_call.function.arguments}"

        # Check cache
        if cache_key in self.tool_cache:
            logger.info(f"Using cached result for {tool_call.function.name}")
            return self.tool_cache[cache_key]

        # Execute tool
        result = await super().execute_tool(tool_call)

        # Cache result
        self.tool_cache[cache_key] = result

        return result
```

### Parallel Execution

```python
class ParallelExecutionAgent(ToolCallAgent):
    """Agent with parallel tool execution"""

    async def act(self) -> str:
        """Execute tools in parallel when possible"""
        if not self.tool_calls:
            return "No tools to execute"

        # Group independent tools
        independent_tools = self.identify_independent_tools()

        # Execute in parallel
        results = []
        for group in independent_tools:
            if len(group) > 1:
                # Parallel execution
                tasks = [
                    self.execute_tool(tool)
                    for tool in group
                ]
                group_results = await asyncio.gather(*tasks)
                results.extend(group_results)
            else:
                # Sequential execution
                result = await self.execute_tool(group[0])
                results.append(result)

        return " | ".join(results)
```

---

## 16. Best Practices {#best-practices}

### Design Principles

#### ✅ DO:
- **Start Simple**: Begin with basic agent, add complexity gradually
- **Use Composition**: Combine simple agents for complex tasks
- **Test Thoroughly**: Write tests for all critical paths
- **Document Well**: Clear documentation helps maintenance
- **Monitor Performance**: Track metrics in production
- **Handle Errors**: Graceful error handling and recovery
- **Version Control**: Track agent versions and changes

#### ❌ DON'T:
- **Overload Tools**: Too many tools confuse the LLM
- **Ignore Limits**: Respect rate limits and quotas
- **Hardcode Secrets**: Use environment variables
- **Skip Validation**: Always validate inputs and outputs
- **Create Monoliths**: Keep agents focused and modular
- **Forget Cleanup**: Release resources properly

### Code Organization

```python
# Recommended project structure
project/
├── agents/
│   ├── __init__.py
│   ├── base/
│   │   ├── custom_base.py
│   │   └── custom_flow.py
│   ├── specialized/
│   │   ├── research_agent.py
│   │   ├── code_agent.py
│   │   └── data_agent.py
│   └── orchestrators/
│       ├── sequential.py
│       └── parallel.py
├── tools/
│   ├── __init__.py
│   ├── custom_tools.py
│   └── tool_factories.py
├── prompts/
│   ├── __init__.py
│   ├── system_prompts.py
│   └── templates.py
├── tests/
│   ├── test_agents.py
│   ├── test_tools.py
│   └── test_integration.py
└── config/
    ├── __init__.py
    └── agent_config.yaml
```

### Error Handling

```python
class RobustAgent(ToolCallAgent):
    """Agent with comprehensive error handling"""

    max_retries: int = 3
    retry_delay: float = 1.0

    async def execute_tool_with_retry(self, tool_call) -> str:
        """Execute tool with retry logic"""
        for attempt in range(self.max_retries):
            try:
                result = await self.execute_tool(tool_call)
                return result

            except ToolExecutionError as e:
                logger.warning(f"Tool execution failed (attempt {attempt+1}): {e}")

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    return self.handle_tool_failure(tool_call, e)

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return f"Unexpected error: {str(e)}"

    def handle_tool_failure(self, tool_call, error):
        """Handle tool failures gracefully"""
        fallback_strategies = {
            "web_search": "Try different search terms",
            "python_execute": "Check code syntax",
            "browser_use": "Try alternative browser action"
        }

        strategy = fallback_strategies.get(
            tool_call.function.name,
            "Skip this step and continue"
        )

        return f"Tool failed: {error}. Strategy: {strategy}"
```

### Logging and Monitoring

```python
class MonitoredAgent(ToolCallAgent):
    """Agent with comprehensive monitoring"""

    metrics: Dict[str, Any] = Field(default_factory=dict)

    async def think(self) -> bool:
        """Think with monitoring"""
        start_time = time.time()

        # Log start
        logger.info(f"[{self.name}] Starting think phase")

        # Execute
        result = await super().think()

        # Calculate metrics
        duration = time.time() - start_time

        # Update metrics
        self.metrics["think_duration"] = duration
        self.metrics["think_count"] = self.metrics.get("think_count", 0) + 1

        # Log completion
        logger.info(f"[{self.name}] Think completed in {duration:.2f}s")

        # Send to monitoring system
        await self.send_metrics()

        return result

    async def send_metrics(self):
        """Send metrics to monitoring system"""
        # Example: Send to Prometheus, DataDog, etc.
        pass
```

---

## 17. Troubleshooting {#troubleshooting}

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| **Agent doesn't respond** | No tools available | Ensure tools are initialized |
| **Infinite loops** | No termination | Add step limits and Terminate tool |
| **High token usage** | Long context | Use memory optimization |
| **Tool failures** | Missing dependencies | Check tool requirements |
| **Slow performance** | Inefficient prompts | Optimize prompts |
| **Memory errors** | Memory leak | Implement cleanup |
| **MCP connection fails** | Server not running | Verify server status |
| **Tests fail** | Mock issues | Update mocks for new behavior |

### Debugging Techniques

```python
class DebuggableAgent(ToolCallAgent):
    """Agent with debugging capabilities"""

    debug_mode: bool = True

    async def think(self) -> bool:
        """Think with debug output"""
        if self.debug_mode:
            # Log state before
            logger.debug(f"Memory: {len(self.memory.messages)} messages")
            logger.debug(f"Tools: {[t.name for t in self.available_tools.tools]}")
            logger.debug(f"State: {self.state}")

        # Execute
        result = await super().think()

        if self.debug_mode:
            # Log state after
            logger.debug(f"Think result: {result}")
            logger.debug(f"Tool calls: {self.tool_calls}")

            # Dump full state if needed
            if os.environ.get("DEBUG_DUMP"):
                self.dump_debug_state()

        return result

    def dump_debug_state(self):
        """Dump complete state for debugging"""
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "state": self.state.value,
            "memory": self.memory.to_dict_list(),
            "tool_calls": [
                {
                    "name": tc.function.name,
                    "args": tc.function.arguments
                }
                for tc in self.tool_calls
            ] if self.tool_calls else [],
            "metrics": getattr(self, 'metrics', {})
        }

        with open(f"debug_{self.name}_{time.time()}.json", "w") as f:
            json.dump(debug_info, f, indent=2)
```

### Performance Profiling

```python
import cProfile
import pstats
from io import StringIO

def profile_agent(agent: BaseAgent):
    """Profile agent performance"""
    profiler = cProfile.Profile()

    # Start profiling
    profiler.enable()

    # Run agent
    result = asyncio.run(agent.run())

    # Stop profiling
    profiler.disable()

    # Generate report
    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions

    print(stream.getvalue())

    return result
```

---

## Summary

This comprehensive guide covers:

### ✅ Covered Topics
- Complete architecture overview
- Step-by-step agent creation
- Tool integration patterns
- MCP remote tool integration
- Advanced prompt engineering
- Multiple flow patterns beyond ReAct
- Custom flow control
- State management strategies
- Multi-agent orchestration
- Ready-to-use templates
- Testing strategies
- Performance optimization
- Best practices
- Troubleshooting guide

### 🚀 Quick Start Path

1. **Understand Architecture** → Section 2
2. **Create Basic Agent** → Section 4
3. **Add Tools** → Section 5
4. **Design Prompts** → Section 7
5. **Choose Flow Pattern** → Section 8
6. **Test & Deploy** → Section 14-16

### 📚 Key Takeaways

1. **Flexibility**: OpenManus supports multiple agent patterns, not just ReAct
2. **Tool Integration**: MCP seamlessly integrates through the tool system
3. **Prompt Engineering**: Dynamic, conditional, and role-based prompts
4. **Orchestration**: Agents can be composed and orchestrated in various ways
5. **Production Ready**: Comprehensive testing and optimization strategies

### 🔗 Resources

- [OpenManus Repository](https://github.com/openManus/openManus)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Example Implementations](./examples/)
- [API Documentation](./api/)

---

*Last Updated: 2026-01-20*
*Version: 2.0*
*Complete Guide - 17 Sections*