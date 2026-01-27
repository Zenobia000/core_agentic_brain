# 系統設計文件 (System Design Document)
# Core Agentic Brain - 詳細設計規格

**文件版本:** 1.0
**日期:** 2026-01-27
**專案名稱:** Core Agentic Brain
**設計模式:** 漸進式分層設計

---

## 執行摘要

本文件詳細描述 Core Agentic Brain 的系統設計，包含模組設計、資料結構、演算法、介面定義及實作細節。基於系統架構文件（SA），提供可直接實作的技術規格。

---

## 1. 設計概覽

### 1.1 設計目標

| 目標 | 量化指標 | 驗證方法 |
|-----|---------|----------|
| **極簡實作** | 核心 < 500 行 | 程式碼行數統計 |
| **快速響應** | P95 < 1秒 | 性能測試 |
| **易於理解** | 新人 < 30分鐘 | 開發者調查 |
| **高度模組化** | 耦合度 < 0.3 | 依賴分析 |
| **零配置啟動** | 0 必需設定 | 整合測試 |

### 1.2 設計約束

```python
# 設計約束執行檢查
DESIGN_CONSTRAINTS = {
    "core_modules": {
        "agent.py": {"max_lines": 100, "max_complexity": 5},
        "llm.py": {"max_lines": 50, "max_complexity": 3},
        "tools.py": {"max_lines": 50, "max_complexity": 3}
    },
    "dependencies": {
        "production": ["pyyaml", "requests", "fastapi", "python-dotenv"],
        "development": ["pytest", "black", "mypy", "ruff"]
    },
    "performance": {
        "startup_time": 2.0,  # seconds
        "memory_limit": 100,  # MB
        "response_time": 1.0  # seconds
    }
}
```

---

## 2. 模組設計

### 2.1 核心模組 (Layer 0)

#### 2.1.1 Agent Core (core/agent.py)

```python
# 核心 Agent 設計
class Agent:
    """極簡 Agent 實作 - 核心處理邏輯"""

    def __init__(self, config: dict = None):
        """初始化 Agent
        Args:
            config: 配置字典，可選
        """
        self.config = config or self._default_config()
        self.llm = LLMWrapper(self.config.get("llm", {}))
        self.tools = ToolManager(self.config.get("tools", {}))
        self.context = []  # 對話歷史

    async def process(self, user_input: str) -> str:
        """處理用戶輸入
        Args:
            user_input: 用戶輸入文字
        Returns:
            AI 回應文字
        """
        # 1. 添加到上下文
        self.context.append({"role": "user", "content": user_input})

        # 2. 呼叫 LLM
        response = await self.llm.generate(
            messages=self.context,
            tools=self.tools.get_definitions()
        )

        # 3. 處理工具調用
        if response.tool_calls:
            tool_results = await self._execute_tools(response.tool_calls)
            response = await self.llm.generate(
                messages=self.context + tool_results
            )

        # 4. 更新上下文並返回
        self.context.append({"role": "assistant", "content": response.content})
        return response.content

    async def _execute_tools(self, tool_calls: list) -> list:
        """執行工具調用"""
        results = []
        for call in tool_calls:
            result = await self.tools.execute(
                name=call.name,
                parameters=call.parameters
            )
            results.append({
                "role": "tool",
                "content": result,
                "tool_call_id": call.id
            })
        return results

    def _default_config(self) -> dict:
        """預設配置"""
        return {
            "llm": {"provider": "openai", "model": "gpt-4"},
            "tools": {"enabled": ["python", "files", "browser"]}
        }
```

#### 2.1.2 LLM Wrapper (core/llm.py)

```python
# LLM 封裝器設計
class LLMWrapper:
    """統一的 LLM 介面封裝"""

    def __init__(self, config: dict):
        self.provider = self._init_provider(config)

    async def generate(self, messages: list, tools: list = None) -> LLMResponse:
        """生成 LLM 回應"""
        return await self.provider.complete(
            messages=messages,
            tools=tools,
            temperature=0.7,
            max_tokens=2000
        )

    def _init_provider(self, config: dict):
        """初始化提供者"""
        provider_map = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "local": LocalProvider
        }
        provider_class = provider_map.get(config.get("provider", "openai"))
        return provider_class(config)

# Response 資料結構
@dataclass
class LLMResponse:
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    usage: Optional[dict] = None
```

#### 2.1.3 Tool Manager (core/tools.py)

```python
# 工具管理器設計
class ToolManager:
    """工具註冊與執行管理"""

    def __init__(self, config: dict):
        self.tools = {}
        self._register_tools(config.get("enabled", []))

    def _register_tools(self, tool_names: list):
        """註冊啟用的工具"""
        for name in tool_names:
            if tool_module := self._load_tool(name):
                self.tools[name] = tool_module

    async def execute(self, name: str, parameters: dict) -> dict:
        """執行工具"""
        if tool := self.tools.get(name):
            return await tool.execute(parameters)
        return {"error": f"Tool {name} not found"}

    def get_definitions(self) -> list:
        """獲取工具定義（for LLM）"""
        return [tool.definition for tool in self.tools.values()]

    def _load_tool(self, name: str):
        """動態載入工具模組"""
        try:
            module = __import__(f"tools.{name}", fromlist=["Tool"])
            return module.Tool()
        except ImportError:
            return None
```

### 2.2 路由模組 (Layer 1)

#### 2.2.1 Task Analyzer (router/analyzer.py)

```python
# 任務分析器設計
class TaskAnalyzer:
    """分析任務複雜度並決定執行路徑"""

    def __init__(self):
        self.rules = self._init_rules()

    def analyze(self, task: str, context: dict = None) -> ExecutionPath:
        """分析任務
        Returns:
            ExecutionPath.FAST or ExecutionPath.AGENT
        """
        # 快速路徑檢查
        if self._is_simple_task(task, context):
            return ExecutionPath.FAST

        # 複雜任務檢查
        if self._needs_planning(task) or self._is_multi_step(task):
            return ExecutionPath.AGENT

        # 預設快速路徑
        return ExecutionPath.FAST

    def _is_simple_task(self, task: str, context: dict) -> bool:
        """判斷是否為簡單任務"""
        indicators = [
            len(task) < 200,  # 短查詢
            not self._contains_multiple_requests(task),
            self._is_single_tool_task(task),
            not context or len(context.get("history", [])) < 3
        ]
        return all(indicators)

    def _needs_planning(self, task: str) -> bool:
        """是否需要規劃"""
        planning_keywords = [
            "plan", "steps", "how to", "strategy",
            "design", "architect", "implement"
        ]
        return any(keyword in task.lower() for keyword in planning_keywords)

    def _is_multi_step(self, task: str) -> bool:
        """是否為多步驟任務"""
        multi_step_patterns = [
            r"first.*then",
            r"step \d+",
            r"and then",
            r"after that"
        ]
        import re
        return any(re.search(pattern, task, re.IGNORECASE)
                  for pattern in multi_step_patterns)

class ExecutionPath(Enum):
    FAST = "fast"
    AGENT = "agent"
```

#### 2.2.2 Route Executor (router/executor.py)

```python
# 路由執行器設計
class RouteExecutor:
    """根據路由決策執行任務"""

    def __init__(self, agent_core: Agent):
        self.core = agent_core
        self.agents = self._init_agents()

    async def execute(self, task: str, path: ExecutionPath) -> str:
        """執行任務"""
        if path == ExecutionPath.FAST:
            return await self._execute_fast_path(task)
        else:
            return await self._execute_agent_path(task)

    async def _execute_fast_path(self, task: str) -> str:
        """快速路徑執行"""
        # 直接使用核心 Agent
        return await self.core.process(task)

    async def _execute_agent_path(self, task: str) -> str:
        """代理路徑執行"""
        # 1. 規劃階段
        plan = await self.agents["planner"].plan(task)

        # 2. 執行階段
        results = []
        for step in plan.steps:
            result = await self.agents["executor"].execute(step)
            results.append(result)

        # 3. 審核階段
        final_result = await self.agents["reviewer"].review(
            task=task,
            plan=plan,
            results=results
        )

        return final_result

    def _init_agents(self) -> dict:
        """初始化代理"""
        return {
            "planner": PlannerAgent(self.core),
            "executor": ExecutorAgent(self.core),
            "reviewer": ReviewerAgent(self.core)
        }
```

### 2.3 企業模組 (Layer 2)

#### 2.3.1 Permission System (enterprise/permissions.py)

```python
# 權限系統設計
class PermissionSystem:
    """基於角色的權限控制系統"""

    def __init__(self, config: dict):
        self.rules = self._load_rules(config)
        self.default_level = config.get("default", PermissionLevel.ASK)

    def check(self, action: str, context: dict) -> PermissionLevel:
        """檢查權限
        Args:
            action: 動作標識 (e.g., "tool:bash:execute")
            context: 上下文資訊 (user, params, etc.)
        Returns:
            PermissionLevel: ALLOW, ASK, or DENY
        """
        # 匹配規則
        for rule in self.rules:
            if self._match_rule(rule, action, context):
                return rule.level

        return self.default_level

    def _match_rule(self, rule: Rule, action: str, context: dict) -> bool:
        """匹配規則"""
        # 動作匹配
        if not self._match_pattern(rule.action_pattern, action):
            return False

        # 上下文條件匹配
        if rule.conditions:
            return all(self._check_condition(cond, context)
                      for cond in rule.conditions)

        return True

    def _load_rules(self, config: dict) -> list:
        """載入權限規則"""
        rules = []
        for rule_config in config.get("rules", []):
            rules.append(Rule(
                action_pattern=rule_config["action"],
                level=PermissionLevel[rule_config["level"].upper()],
                conditions=rule_config.get("conditions", [])
            ))
        return rules

class PermissionLevel(Enum):
    ALLOW = "allow"  # 允許執行
    ASK = "ask"      # 請求確認
    DENY = "deny"    # 拒絕執行

@dataclass
class Rule:
    action_pattern: str
    level: PermissionLevel
    conditions: list = None
```

#### 2.3.2 Audit Logger (enterprise/audit.py)

```python
# 審計日誌系統設計
class AuditLogger:
    """審計日誌記錄器"""

    def __init__(self, config: dict):
        self.enabled = config.get("enabled", False)
        self.storage = self._init_storage(config)
        self.filters = config.get("filters", [])

    async def log(self, event: AuditEvent):
        """記錄審計事件"""
        if not self.enabled:
            return

        if self._should_log(event):
            await self.storage.write(event.to_json())

    def _should_log(self, event: AuditEvent) -> bool:
        """判斷是否應該記錄"""
        # 應用過濾規則
        for filter_rule in self.filters:
            if not self._match_filter(filter_rule, event):
                return False
        return True

    def _init_storage(self, config: dict):
        """初始化存儲"""
        storage_type = config.get("storage", "file")
        if storage_type == "file":
            return FileStorage(config.get("path", "./audit.log"))
        elif storage_type == "syslog":
            return SyslogStorage(config.get("server"))
        else:
            return MemoryStorage()

@dataclass
class AuditEvent:
    timestamp: datetime
    user: str
    action: str
    resource: str
    result: str
    details: dict = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)
```

---

## 3. 資料模型

### 3.1 核心資料結構

```python
# 對話上下文
@dataclass
class Message:
    role: str  # "user", "assistant", "system", "tool"
    content: str
    metadata: Optional[dict] = None

# 工具調用
@dataclass
class ToolCall:
    id: str
    name: str
    parameters: dict

# 工具結果
@dataclass
class ToolResult:
    tool_call_id: str
    content: Any
    error: Optional[str] = None

# 執行計劃
@dataclass
class ExecutionPlan:
    steps: List[Step]
    estimated_time: float
    complexity: str  # "simple", "moderate", "complex"

@dataclass
class Step:
    id: str
    description: str
    tool: Optional[str]
    parameters: Optional[dict]
    dependencies: List[str] = field(default_factory=list)
```

### 3.2 配置模型

```python
# 配置資料結構
@dataclass
class Config:
    mode: str = "minimal"  # minimal, standard, enterprise
    core: CoreConfig = field(default_factory=CoreConfig)
    routing: Optional[RoutingConfig] = None
    enterprise: Optional[EnterpriseConfig] = None

@dataclass
class CoreConfig:
    llm: LLMConfig
    tools: ToolsConfig

@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000

@dataclass
class ToolsConfig:
    enabled: List[str] = field(default_factory=lambda: ["python", "files"])
    timeout: int = 30

@dataclass
class RoutingConfig:
    enabled: bool = False
    fast_path_threshold: int = 1000
    agent_timeout: int = 60

@dataclass
class EnterpriseConfig:
    permissions: PermissionsConfig
    audit: AuditConfig
    mcp: MCPConfig
```

### 3.3 狀態管理

```python
# 會話狀態
class SessionState:
    """管理會話狀態"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Message] = []
        self.variables: dict = {}
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

    def add_message(self, message: Message):
        """添加訊息"""
        self.messages.append(message)
        self.last_activity = datetime.now()

    def get_context(self, max_messages: int = 10) -> List[Message]:
        """獲取上下文（最近的 N 條訊息）"""
        return self.messages[-max_messages:]

    def clear(self):
        """清空會話"""
        self.messages.clear()
        self.variables.clear()

# 全局狀態管理
class StateManager:
    """全局狀態管理器"""

    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}
        self.active_session: Optional[str] = None

    def create_session(self, session_id: str = None) -> SessionState:
        """創建新會話"""
        if not session_id:
            session_id = str(uuid.uuid4())

        session = SessionState(session_id)
        self.sessions[session_id] = session
        self.active_session = session_id
        return session

    def get_session(self, session_id: str = None) -> Optional[SessionState]:
        """獲取會話"""
        if not session_id:
            session_id = self.active_session
        return self.sessions.get(session_id)

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """清理舊會話"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = [
            sid for sid, session in self.sessions.items()
            if session.last_activity < cutoff_time
        ]
        for sid in to_remove:
            del self.sessions[sid]
```

---

## 4. 工具設計

### 4.1 工具介面規範

```python
# 工具基類
class BaseTool(ABC):
    """所有工具的基類"""

    @property
    @abstractmethod
    def definition(self) -> dict:
        """工具定義（OpenAI function 格式）"""
        pass

    @abstractmethod
    async def execute(self, parameters: dict) -> dict:
        """執行工具"""
        pass

    def validate_parameters(self, parameters: dict) -> bool:
        """驗證參數"""
        # 使用 jsonschema 驗證
        from jsonschema import validate
        try:
            validate(parameters, self.definition["parameters"])
            return True
        except:
            return False
```

### 4.2 內建工具實作

#### Python Tool (tools/python.py)

```python
class Tool(BaseTool):
    """Python 程式碼執行工具"""

    @property
    def definition(self) -> dict:
        return {
            "name": "python",
            "description": "Execute Python code",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    }
                },
                "required": ["code"]
            }
        }

    async def execute(self, parameters: dict) -> dict:
        """執行 Python 程式碼"""
        code = parameters.get("code", "")

        try:
            # 使用受限的執行環境
            import io
            import contextlib

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(code, {"__builtins__": self._safe_builtins()})

            return {
                "success": True,
                "output": output.getvalue()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _safe_builtins(self) -> dict:
        """安全的內建函數子集"""
        import builtins
        safe = ["print", "len", "range", "str", "int", "float", "list", "dict"]
        return {k: getattr(builtins, k) for k in safe}
```

#### File Tool (tools/files.py)

```python
class Tool(BaseTool):
    """檔案操作工具"""

    @property
    def definition(self) -> dict:
        return {
            "name": "files",
            "description": "File system operations",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["read", "write", "list", "delete"]
                    },
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["operation", "path"]
            }
        }

    async def execute(self, parameters: dict) -> dict:
        """執行檔案操作"""
        operation = parameters.get("operation")
        path = parameters.get("path", "")

        # 安全檢查
        if not self._is_safe_path(path):
            return {"error": "Access denied"}

        try:
            if operation == "read":
                with open(path, "r") as f:
                    return {"content": f.read()}

            elif operation == "write":
                content = parameters.get("content", "")
                with open(path, "w") as f:
                    f.write(content)
                return {"success": True}

            elif operation == "list":
                import os
                files = os.listdir(path)
                return {"files": files}

            elif operation == "delete":
                import os
                os.remove(path)
                return {"success": True}

        except Exception as e:
            return {"error": str(e)}

    def _is_safe_path(self, path: str) -> bool:
        """檢查路徑安全性"""
        import os
        # 確保在工作目錄內
        abs_path = os.path.abspath(path)
        work_dir = os.path.abspath(".")
        return abs_path.startswith(work_dir)
```

---

## 5. API 設計

### 5.1 REST API

```python
# API 路由定義 (web/api.py)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Core Agentic Brain API")

# 請求/響應模型
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[dict] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    metadata: Optional[dict] = None

# API 端點
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """處理聊天請求"""
    try:
        # 獲取或創建會話
        session = state_manager.get_session(request.session_id)
        if not session:
            session = state_manager.create_session()

        # 處理訊息
        response = await agent.process(request.message)

        return ChatResponse(
            response=response,
            session_id=session.session_id,
            metadata={"tokens_used": 0}  # TODO: 實際 token 計算
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def status():
    """系統狀態"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "mode": config.mode,
        "uptime": get_uptime()
    }

@app.get("/api/tools")
async def list_tools():
    """列出可用工具"""
    return {
        "tools": [
            {"name": name, "description": tool.definition.get("description")}
            for name, tool in tool_manager.tools.items()
        ]
    }

@app.post("/api/tools/{tool_name}/execute")
async def execute_tool(tool_name: str, parameters: dict):
    """直接執行工具"""
    if not permission_system.check(f"tool:{tool_name}:execute", {}):
        raise HTTPException(status_code=403, detail="Permission denied")

    result = await tool_manager.execute(tool_name, parameters)
    return result
```

### 5.2 WebSocket API

```python
# WebSocket 處理 (web/websocket.py)
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket 聊天連接"""
    await websocket.accept()
    session = state_manager.create_session()

    try:
        while True:
            # 接收訊息
            data = await websocket.receive_json()

            # 處理訊息
            response = await agent.process(data.get("message", ""))

            # 發送回應
            await websocket.send_json({
                "type": "response",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })

    except WebSocketDisconnect:
        # 清理會話
        state_manager.sessions.pop(session.session_id, None)

@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """事件串流 WebSocket"""
    await websocket.accept()

    # 訂閱事件
    async for event in event_bus.subscribe():
        await websocket.send_json(event.to_dict())
```

### 5.3 CLI 介面

```python
# CLI 介面 (cli/main.py)
import asyncio
import click
from rich.console import Console
from rich.markdown import Markdown

console = Console()

@click.command()
@click.option('--mode', default='minimal', help='Execution mode')
@click.option('--config', default='config.yaml', help='Config file')
def main(mode: str, config: str):
    """Core Agentic Brain CLI"""
    # 載入配置
    config_data = load_config(config)
    config_data['mode'] = mode

    # 初始化系統
    agent = Agent(config_data)

    # 互動循環
    console.print("[bold green]Core Agentic Brain[/bold green]")
    console.print(f"Mode: {mode} | Type 'exit' to quit")

    while True:
        try:
            # 獲取輸入
            user_input = console.input("\n[bold blue]You:[/bold blue] ")

            if user_input.lower() in ['exit', 'quit']:
                break

            # 處理輸入
            response = asyncio.run(agent.process(user_input))

            # 顯示回應
            console.print("\n[bold green]AI:[/bold green]")
            console.print(Markdown(response))

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    console.print("\n[yellow]Goodbye![/yellow]")

if __name__ == "__main__":
    main()
```

---

## 6. 演算法設計

### 6.1 任務複雜度評估演算法

```python
def calculate_task_complexity(task: str, context: dict) -> float:
    """計算任務複雜度分數
    Returns:
        0.0-1.0 的複雜度分數
    """
    score = 0.0
    weights = {
        "length": 0.2,
        "tools": 0.3,
        "steps": 0.3,
        "context": 0.2
    }

    # 長度因素
    length_score = min(len(task) / 1000, 1.0)
    score += length_score * weights["length"]

    # 工具需求因素
    tool_count = estimate_tool_count(task)
    tool_score = min(tool_count / 5, 1.0)
    score += tool_score * weights["tools"]

    # 步驟複雜度
    step_count = estimate_steps(task)
    step_score = min(step_count / 10, 1.0)
    score += step_score * weights["steps"]

    # 上下文依賴
    context_size = len(context.get("history", []))
    context_score = min(context_size / 20, 1.0)
    score += context_score * weights["context"]

    return score

def estimate_tool_count(task: str) -> int:
    """估算需要的工具數量"""
    tool_indicators = {
        "python": ["code", "calculate", "compute", "algorithm"],
        "files": ["file", "read", "write", "save", "load"],
        "browser": ["search", "web", "browse", "url", "website"],
        "database": ["query", "sql", "database", "table"],
        "api": ["api", "endpoint", "request", "fetch"]
    }

    count = 0
    task_lower = task.lower()
    for tool, keywords in tool_indicators.items():
        if any(keyword in task_lower for keyword in keywords):
            count += 1

    return count

def estimate_steps(task: str) -> int:
    """估算任務步驟數"""
    # 簡單啟發式：基於句子和連接詞
    import re

    sentences = re.split(r'[.!?]+', task)
    connectors = re.findall(r'\b(then|after|next|finally|and)\b', task.lower())

    estimated_steps = len(sentences) + len(connectors)
    return max(1, estimated_steps)
```

### 6.2 快速路徑優化演算法

```python
class FastPathOptimizer:
    """快速路徑優化器"""

    def optimize(self, task: str, context: dict) -> OptimizedPlan:
        """優化執行計劃"""
        # 1. 識別可並行的操作
        operations = self.parse_operations(task)

        # 2. 建立依賴圖
        dep_graph = self.build_dependency_graph(operations)

        # 3. 拓撲排序
        execution_order = self.topological_sort(dep_graph)

        # 4. 識別並行機會
        parallel_groups = self.identify_parallel_groups(
            execution_order, dep_graph
        )

        return OptimizedPlan(
            sequential_steps=execution_order,
            parallel_groups=parallel_groups
        )

    def parse_operations(self, task: str) -> List[Operation]:
        """解析操作"""
        # 簡化版本：基於關鍵詞識別
        operations = []

        if "read" in task or "load" in task:
            operations.append(Operation("read", priority=1))

        if "process" in task or "analyze" in task:
            operations.append(Operation("process", priority=2))

        if "write" in task or "save" in task:
            operations.append(Operation("write", priority=3))

        return operations

    def build_dependency_graph(self, operations: List[Operation]) -> Graph:
        """建立依賴圖"""
        graph = {}

        # 簡單規則：read -> process -> write
        for i, op in enumerate(operations):
            graph[op.id] = []
            if i > 0:
                graph[operations[i-1].id].append(op.id)

        return graph

    def topological_sort(self, graph: dict) -> List[str]:
        """拓撲排序"""
        from collections import deque

        # 計算入度
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] += 1

        # BFS
        queue = deque([node for node in in_degree if in_degree[node] == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result
```

---

## 7. 錯誤處理

### 7.1 錯誤層級定義

```python
class ErrorLevel(Enum):
    CRITICAL = "critical"  # 系統無法繼續
    ERROR = "error"        # 操作失敗
    WARNING = "warning"    # 可能的問題
    INFO = "info"          # 資訊性

class SystemError(Exception):
    """系統錯誤基類"""

    def __init__(self, message: str, level: ErrorLevel = ErrorLevel.ERROR):
        self.message = message
        self.level = level
        super().__init__(message)

class ConfigurationError(SystemError):
    """配置錯誤"""
    pass

class ToolExecutionError(SystemError):
    """工具執行錯誤"""
    pass

class PermissionError(SystemError):
    """權限錯誤"""
    pass
```

### 7.2 錯誤處理策略

```python
class ErrorHandler:
    """統一錯誤處理"""

    def __init__(self):
        self.handlers = {
            ConfigurationError: self.handle_config_error,
            ToolExecutionError: self.handle_tool_error,
            PermissionError: self.handle_permission_error
        }

    async def handle(self, error: Exception) -> dict:
        """處理錯誤"""
        handler = self.handlers.get(type(error), self.handle_generic_error)
        return await handler(error)

    async def handle_config_error(self, error: ConfigurationError) -> dict:
        """處理配置錯誤"""
        return {
            "error": "Configuration Error",
            "message": str(error),
            "suggestion": "Please check your config.yaml file"
        }

    async def handle_tool_error(self, error: ToolExecutionError) -> dict:
        """處理工具錯誤"""
        return {
            "error": "Tool Execution Failed",
            "message": str(error),
            "fallback": "Try using a different approach"
        }

    async def handle_permission_error(self, error: PermissionError) -> dict:
        """處理權限錯誤"""
        return {
            "error": "Permission Denied",
            "message": str(error),
            "action": "Request permission from administrator"
        }

    async def handle_generic_error(self, error: Exception) -> dict:
        """處理通用錯誤"""
        import traceback
        return {
            "error": type(error).__name__,
            "message": str(error),
            "trace": traceback.format_exc() if DEBUG else None
        }
```

---

## 8. 測試設計

### 8.1 單元測試策略

```python
# 測試框架：pytest
# tests/test_core.py

import pytest
from unittest.mock import Mock, patch
from core.agent import Agent

class TestAgent:
    """Agent 核心測試"""

    @pytest.fixture
    def agent(self):
        """創建測試 Agent"""
        config = {"llm": {"provider": "mock"}}
        return Agent(config)

    @pytest.mark.asyncio
    async def test_simple_query(self, agent):
        """測試簡單查詢"""
        response = await agent.process("Hello")
        assert response is not None
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_tool_execution(self, agent):
        """測試工具執行"""
        with patch.object(agent.tools, 'execute') as mock_execute:
            mock_execute.return_value = {"result": "success"}

            response = await agent.process("Run Python code: print('test')")
            mock_execute.assert_called()

    @pytest.mark.asyncio
    async def test_error_handling(self, agent):
        """測試錯誤處理"""
        with patch.object(agent.llm, 'generate') as mock_generate:
            mock_generate.side_effect = Exception("LLM Error")

            with pytest.raises(Exception):
                await agent.process("Test query")

# tests/test_router.py
class TestRouter:
    """路由器測試"""

    def test_simple_task_detection(self):
        """測試簡單任務檢測"""
        analyzer = TaskAnalyzer()

        simple_tasks = [
            "What is 2+2?",
            "Show me the current time",
            "Read file.txt"
        ]

        for task in simple_tasks:
            assert analyzer.analyze(task) == ExecutionPath.FAST

    def test_complex_task_detection(self):
        """測試複雜任務檢測"""
        analyzer = TaskAnalyzer()

        complex_tasks = [
            "Create a plan for building a web application",
            "First read the file, then analyze it, and finally generate a report",
            "Design and implement a sorting algorithm"
        ]

        for task in complex_tasks:
            assert analyzer.analyze(task) == ExecutionPath.AGENT
```

### 8.2 整合測試

```python
# tests/test_integration.py

class TestIntegration:
    """整合測試"""

    @pytest.fixture
    def system(self):
        """創建完整系統"""
        config = load_config("tests/test_config.yaml")
        agent = Agent(config)
        router = RouteExecutor(agent)
        return router

    @pytest.mark.asyncio
    async def test_end_to_end_simple(self, system):
        """端到端簡單任務測試"""
        response = await system.execute(
            "Calculate 2+2",
            ExecutionPath.FAST
        )
        assert "4" in response

    @pytest.mark.asyncio
    async def test_end_to_end_complex(self, system):
        """端到端複雜任務測試"""
        response = await system.execute(
            "Create a Python function to sort a list",
            ExecutionPath.AGENT
        )
        assert "def" in response
        assert "sort" in response.lower()
```

### 8.3 性能測試

```python
# tests/test_performance.py

import time
import asyncio
from statistics import mean, stdev

class TestPerformance:
    """性能測試"""

    @pytest.mark.performance
    async def test_response_time(self):
        """測試響應時間"""
        agent = Agent()
        times = []

        for _ in range(100):
            start = time.time()
            await agent.process("Hello")
            times.append(time.time() - start)

        avg_time = mean(times)
        std_time = stdev(times)

        assert avg_time < 1.0  # 平均小於1秒
        assert std_time < 0.5  # 標準差小於0.5秒

    @pytest.mark.performance
    def test_memory_usage(self):
        """測試記憶體使用"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 創建多個 Agent 實例
        agents = [Agent() for _ in range(10)]

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        assert memory_increase < 100  # 增加小於100MB
```

---

## 9. 部署配置

### 9.1 Docker 配置

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用
COPY . .

# 環境變量
ENV PYTHONUNBUFFERED=1
ENV MODE=minimal

# 健康檢查
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/status')"

# 啟動命令
CMD ["python", "main.py"]
```

### 9.2 Docker Compose

```yaml
# docker-compose.yaml
version: '3.8'

services:
  core-brain:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MODE=${MODE:-minimal}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./data:/app/data
    restart: unless-stopped

  # 可選：Redis 快取
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    profiles:
      - enterprise
```

### 9.3 Kubernetes 配置

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: core-agentic-brain
spec:
  replicas: 3
  selector:
    matchLabels:
      app: core-brain
  template:
    metadata:
      labels:
        app: core-brain
    spec:
      containers:
      - name: core-brain
        image: core-agentic-brain:latest
        ports:
        - containerPort: 8000
        env:
        - name: MODE
          value: "standard"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/status
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: core-brain-service
spec:
  selector:
    app: core-brain
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## 10. 監控與日誌

### 10.1 監控指標

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# 定義指標
request_count = Counter('agent_requests_total', 'Total requests')
request_duration = Histogram('agent_request_duration_seconds', 'Request duration')
active_sessions = Gauge('agent_active_sessions', 'Active sessions')
tool_executions = Counter('tool_executions_total', 'Tool executions', ['tool_name'])

# 指標收集裝飾器
def track_metrics(func):
    async def wrapper(*args, **kwargs):
        request_count.inc()

        with request_duration.time():
            result = await func(*args, **kwargs)

        return result
    return wrapper
```

### 10.2 日誌配置

```python
# logging_config.py
import logging
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'json',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        'core': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'tools': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file']
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

---

## 附錄 A: 配置範例

### 極簡模式配置

```yaml
# config.minimal.yaml
version: "1.0"
mode: minimal

core:
  llm:
    provider: openai
    model: gpt-4
  tools:
    enabled:
      - python
      - files
```

### 標準模式配置

```yaml
# config.standard.yaml
version: "1.0"
mode: standard

core:
  llm:
    provider: openai
    model: gpt-4
  tools:
    enabled:
      - python
      - files
      - browser

routing:
  enabled: true
  fast_path_threshold: 1000
```

### 企業模式配置

```yaml
# config.enterprise.yaml
version: "1.0"
mode: enterprise

core:
  llm:
    provider: openai
    model: gpt-4
  tools:
    enabled:
      - python
      - files
      - browser
      - database

routing:
  enabled: true
  fast_path_threshold: 1000
  agent_timeout: 60

enterprise:
  permissions:
    enabled: true
    default: ask
    rules:
      - action: "tool:python:execute"
        level: allow
      - action: "tool:database:*"
        level: ask

  audit:
    enabled: true
    storage: file
    path: ./audit.log
    retention_days: 30

  mcp:
    enabled: true
    servers:
      - name: local
        url: localhost:5000
```

---

## 附錄 B: 開發指南

### 快速開始

```bash
# 1. 克隆專案
git clone https://github.com/org/core-agentic-brain.git
cd core-agentic-brain

# 2. 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 設置環境變量
cp .env.example .env
# 編輯 .env 添加 API keys

# 5. 運行測試
pytest

# 6. 啟動應用
python main.py
```

### 開發工作流程

```bash
# 代碼格式化
black .
ruff check .

# 類型檢查
mypy .

# 運行特定測試
pytest tests/test_core.py -v

# 性能測試
pytest -m performance

# 覆蓋率報告
pytest --cov=core --cov-report=html
```

---

**文檔狀態:** 已批准
**下次審查日期:** 2026-04-27
**維護負責人:** 開發團隊