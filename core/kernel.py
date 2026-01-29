"""
系統核心 - 中央調度器 (< 150 行)
基於 Linus 原則：單一調度點，消除特殊情況
"""

from typing import Dict, Any, Optional
from core.communication import CommunicationBus, Message, MessageType
from core.prompt_loader import PromptLoader
from core.types import TaskContext, ExecutionResult


class Kernel:
    """系統核心 - 像 Linux Kernel 的單一調度器"""

    def __init__(self, config_path: str = "config.yaml"):
        """初始化系統核心 - 一次載入所有資源"""
        # 載入配置
        from core.config import load_config
        self.config = load_config(config_path)

        # 初始化核心組件
        self.bus = CommunicationBus()
        self.prompts = PromptLoader("prompts")  # 一次載入所有提示詞
        self.agents = {}  # 動態創建的代理
        self.tools = {}  # 註冊的工具

        # 載入工具 (純函數化)
        self._load_tools()

        # 初始化 LLM
        from core.llm import LLMProvider
        from core.utils import get_config_value
        llm_config = get_config_value(self.config, "core", "llm") or \
                     get_config_value(self.config, "llm")
        self.llm = LLMProvider(llm_config)

    def _load_tools(self):
        """載入純函數工具"""
        from core.utils import get_config_value
        tools_config = get_config_value(self.config, "core", "tools") or \
                       get_config_value(self.config, "tools")

        enabled_tools = tools_config.get("enabled", [])

        for tool_name in enabled_tools:
            # 載入純函數工具
            for subdir in ['builtin', 'custom']:
                try:
                    import importlib
                    # 優先嘗試純函數版本
                    module_name = f"tools.{subdir}.{tool_name}_pure"
                    try:
                        module = importlib.import_module(module_name)
                    except ImportError:
                        # 如果沒有 _pure 版本，嘗試標準名稱
                        module_name = f"tools.{subdir}.{tool_name}"
                        module = importlib.import_module(module_name)

                    if hasattr(module, 'Tool'):
                        tool_instance = module.Tool()
                        # 確保有 handle 方法
                        if not hasattr(tool_instance, 'handle'):
                            print(f"Warning: Tool {tool_name} missing handle() method")
                            continue
                        self.tools[tool_name] = tool_instance
                        self.bus.register(f"tool.{tool_name}", tool_instance)
                        break
                except ImportError:
                    continue
            else:
                print(f"Warning: Could not load tool {tool_name}")

    def get_or_create_agent(self, agent_type: str):
        """獲取或創建代理 - 統一處理"""
        if agent_type not in self.agents:
            # 創建代理
            agent = self._create_agent(agent_type)
            if agent:
                self.agents[agent_type] = agent
                self.bus.register(f"agent.{agent_type}", agent)
            else:
                # 使用預設 executor
                if agent_type != "executor":
                    return self.get_or_create_agent("executor")
                else:
                    # 創建最小代理作為最後手段
                    agent = self._create_minimal_agent(agent_type)
                    self.agents[agent_type] = agent
                    self.bus.register(f"agent.{agent_type}", agent)

        return self.agents[agent_type]

    def _create_agent(self, agent_type: str):
        """創建指定類型的代理"""
        try:
            import importlib
            module = importlib.import_module(f"agents.{agent_type}")
            agent_class = f"{agent_type.capitalize()}Agent"

            if hasattr(module, agent_class):
                AgentClass = getattr(module, agent_class)
                return KernelAwareAgent(
                    agent_class=AgentClass,
                    kernel=self,
                    name=agent_type
                )
        except (ImportError, AttributeError) as e:
            print(f"Warning: Could not create agent {agent_type}: {e}")
        return None

    def _create_minimal_agent(self, agent_type: str):
        """創建最小功能代理"""
        from agents.base import BaseAgent

        class MinimalAgent(BaseAgent):
            async def execute(self, context):
                from core.types import ExecutionResult
                return ExecutionResult(
                    success=True,
                    response="Minimal agent executed"
                )

            def get_system_prompt(self):
                return "You are a minimal agent."

        return KernelAwareAgent(
            agent_class=MinimalAgent,
            kernel=self,
            name=agent_type
        )

    async def execute(self, request: str, context: Optional[TaskContext] = None) -> ExecutionResult:
        """統一執行入口 - 像系統調用

        Args:
            request: 用戶請求
            context: 任務上下文

        Returns:
            執行結果
        """
        # 創建任務上下文
        if context is None:
            context = TaskContext(prompt=request)

        # 路由決策 (簡單實作，可擴展)
        from router.analyzer import TaskAnalyzer
        analyzer = TaskAnalyzer()
        routing = await analyzer.analyze(context)

        # 獲取執行者 - 將策略映射到實際代理類型
        strategy = routing.strategy if hasattr(routing, 'strategy') else "direct"
        # 策略到代理的映射 (消除特殊情況)
        strategy_to_agent = {
            "direct": "executor",
            "sequential": "executor",
            "orchestrated": "executor",
            "parallel": "executor"
        }
        agent_type = strategy_to_agent.get(strategy, "executor")
        agent = self.get_or_create_agent(agent_type)

        # 創建訊息
        message = Message(
            type=MessageType.PROMPT,
            content=request,
            source="kernel",
            target=f"agent.{agent_type}",
            metadata={"context": context, "routing": routing}
        )

        # 透過 bus 發送訊息
        result = await self.bus.send(message)

        # 返回結果
        if isinstance(result, ExecutionResult):
            return result
        elif isinstance(result, Message):
            return ExecutionResult(
                success=result.type != MessageType.ERROR,
                response=str(result.content),
                metadata=result.metadata
            )
        else:
            return ExecutionResult(
                success=True,
                response=str(result)
            )

    def get_prompt(self, path: str, **kwargs) -> str:
        """統一的提示詞獲取介面"""
        return self.prompts.get(path, **kwargs)

    async def call_tool(self, tool_name: str, parameters: Dict) -> Any:
        """統一的工具調用介面"""
        message = Message(
            type=MessageType.TOOL_CALL,
            content=parameters,
            source="kernel",
            target=f"tool.{tool_name}"
        )
        return await self.bus.send(message)


class KernelAwareAgent:
    """Kernel 感知的代理包裝器 - 消除直接 PromptLoader 依賴"""

    def __init__(self, agent_class, kernel: Kernel, name: str):
        """初始化代理包裝器"""
        self.kernel = kernel
        self.name = name
        # 創建原始代理 - 檢查是否接受參數
        import inspect
        sig = inspect.signature(agent_class.__init__)
        params = list(sig.parameters.keys())

        if 'llm_provider' in params:
            # 新式代理接受 llm_provider
            self.agent = agent_class(llm_provider=kernel.llm)
        elif len(params) == 1:  # 只有 self
            # 舊式代理無參數
            self.agent = agent_class()
        else:
            # 其他情況
            self.agent = agent_class()

    async def handle(self, message: Message) -> Any:
        """處理訊息 - 統一介面"""
        if message.type == MessageType.PROMPT:
            # 從 kernel 獲取提示詞而非直接使用 PromptLoader
            context = message.metadata.get("context", TaskContext(prompt=message.content))

            # 替換 agent 的 get_system_prompt 方法
            original_get_prompt = self.agent.get_system_prompt

            def kernel_get_prompt():
                # 從 kernel 獲取提示詞
                return self.kernel.get_prompt(f"{self.name}.system")

            self.agent.get_system_prompt = kernel_get_prompt

            # 執行
            result = await self.agent.execute(context)

            # 恢復原方法
            self.agent.get_system_prompt = original_get_prompt

            return result
        else:
            return Message(
                type=MessageType.ERROR,
                content=f"Agent {self.name} cannot handle {message.type}",
                source=f"agent.{self.name}",
                target=message.source
            )