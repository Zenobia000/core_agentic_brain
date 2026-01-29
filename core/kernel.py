"""
系統核心 - 中央調度器 (< 150 行)
基於 Linus 原則：單一調度點，消除特殊情況
"""

import uuid
from typing import Dict, Any, Optional
from core.communication import CommunicationBus, Message, MessageType
from core.prompt_loader import PromptLoader
from core.types import TaskContext, ExecutionResult
from core.logger import logger, contextualize, configure as configure_logger
from core.workspace import WorkspaceManager


class Kernel:
    """系統核心 - 像 Linux Kernel 的單一調度器"""

    def __init__(self, config_path: str = "config.yaml"):
        """初始化系統核心 - 一次載入所有資源"""
        # 載入配置
        from core.config import load_config
        from core.utils import get_config_value
        self.config = load_config(config_path)

        # 初始化日誌系統
        logging_config = get_config_value(self.config, "logging") or {}
        configure_logger(logging_config)

        # 初始化工作區管理器
        self.workspace = WorkspaceManager(self.config)

        # 初始化核心組件
        self.bus = CommunicationBus()
        self.prompts = PromptLoader("prompts")  # 一次載入所有提示詞
        self.agents = {}  # 動態創建的代理
        self.tools = {}  # 註冊的工具

        # 載入工具 (純函數化)
        self._load_tools()

        # 初始化 LLM
        from core.llm import LLMProvider
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
        # Generate unique run_id for this execution
        run_id = f"run_{uuid.uuid4().hex[:8]}"

        # Create workspace for this run
        workspace_path = self.workspace.create_run_context(run_id)

        # Create or update task context with run_id and workspace_path
        if context is None:
            context = TaskContext(prompt=request, run_id=run_id, workspace_path=workspace_path)
        else:
            context.run_id = run_id
            context.workspace_path = workspace_path

        # Use contextualized logging for the entire execution
        with contextualize(run_id=run_id):
            logger.info(f"Request received: '{request[:80]}...' " if len(request) > 80 else f"Request received: '{request}'")

            # 路由決策 - 使用 LLM 分析器 (雙階段: 問題重塑 -> 路由決策)
            from router.llm_analyzer import LLMTaskAnalyzer
            analyzer = LLMTaskAnalyzer(llm_provider=self.llm)
            routing = await analyzer.analyze(context)

            # Log two-phase analysis results
            if hasattr(routing, 'metadata') and routing.metadata:
                system_mode = routing.metadata.get('system_mode', 'unknown')
                intent_type = routing.metadata.get('intent_type', 'unknown')
                logger.info(f"[Phase 1] Intent: {intent_type}, Mode: {system_mode}")
                if routing.metadata.get('key_questions'):
                    logger.debug(f"[Phase 1] Key questions: {routing.metadata.get('key_questions')}")

            strategy_name = routing.strategy if hasattr(routing, 'strategy') else "direct"
            complexity_name = routing.complexity.value if hasattr(routing, 'complexity') else "unknown"
            logger.info(f"Routing decision: strategy={strategy_name}, complexity={complexity_name}")

            # System 2 Integration: Apply Refined Goal if available
            # This ensures that all downstream agents work with the deconstructed/refined task
            if hasattr(routing, 'metadata') and routing.metadata and "refined_goal" in routing.metadata:
                refined_goal = routing.metadata["refined_goal"]
                if refined_goal and refined_goal != context.prompt:
                    logger.info(f"System 2 Refinement: Upgrading prompt to refined goal")
                    # Preserve original for audit
                    context.metadata["original_prompt"] = context.prompt
                    context.metadata["system_2_thought_process"] = routing.metadata.get("thought_process", "")
                    
                    # Update context and request
                    context.prompt = refined_goal
                    request = refined_goal  # Update local var for direct execution path

            # 判斷是否使用多代理協調
            use_orchestration = (
                hasattr(routing, 'complexity') and
                routing.complexity.value in ['moderate', 'complex'] and
                hasattr(routing, 'agents') and
                len(routing.agents) > 1
            )

            if use_orchestration:
                # 使用多代理協調器
                from core.orchestration import MultiAgentOrchestrator, ExecutionStrategy
                from core.types import AgentRole

                # 創建協調器
                orchestrator = MultiAgentOrchestrator(self)

                # 映射策略
                strategy_map = {
                    "direct": ExecutionStrategy.DIRECT,
                    "sequential": ExecutionStrategy.SEQUENTIAL,
                    "orchestrated": ExecutionStrategy.ORCHESTRATED,
                    "react": ExecutionStrategy.REACT
                }
                strategy = strategy_map.get(
                    routing.strategy if hasattr(routing, 'strategy') else "direct",
                    ExecutionStrategy.DIRECT
                )

                # routing.agents 已經是 AgentRole 枚舉列表，直接使用
                agent_roles = routing.agents if hasattr(routing, 'agents') else []

                logger.debug(f"Dispatching to orchestrator with agents: {[r.value for r in agent_roles]}")

                # 執行協調
                result = await orchestrator.orchestrate(
                    context=context,
                    strategy=strategy,
                    agents=agent_roles
                )

                # 添加路由元資料
                if not result.metadata:
                    result.metadata = {}
                result.metadata["routing"] = {
                    "complexity": routing.complexity.value if hasattr(routing, 'complexity') else "unknown",
                    "strategy": routing.strategy if hasattr(routing, 'strategy') else "direct",
                    "reasoning": routing.reasoning if hasattr(routing, 'reasoning') else ""
                }

                logger.info(f"Execution finished. Success: {result.success}")
                return result

            else:
                # 簡單任務，使用原始的單代理執行
                logger.info("Dispatching task to agent: executor")
                agent = self.get_or_create_agent("executor")

                # 創建訊息
                message = Message(
                    type=MessageType.PROMPT,
                    content=request,
                    source="kernel",
                    target="agent.executor",
                    metadata={"context": context, "routing": routing}
                )

                # 透過 bus 發送訊息
                result = await self.bus.send(message)

                # 返回結果
                if isinstance(result, ExecutionResult):
                    logger.info(f"Execution finished. Success: {result.success}")
                    return result
                elif isinstance(result, Message):
                    success = result.type != MessageType.ERROR
                    logger.info(f"Execution finished. Success: {success}")
                    return ExecutionResult(
                        success=success,
                        response=str(result.content),
                        metadata=result.metadata
                    )
                else:
                    logger.info("Execution finished. Success: True")
                    return ExecutionResult(
                        success=True,
                        response=str(result)
                    )

    def get_prompt(self, path: str, **kwargs) -> str:
        """統一的提示詞獲取介面"""
        return self.prompts.get(path, **kwargs)

    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict,
        context: Optional[TaskContext] = None
    ) -> Any:
        """統一的工具調用介面

        Args:
            tool_name: 工具名稱
            parameters: 工具參數
            context: 任務上下文（包含 workspace_path）

        Returns:
            工具執行結果
        """
        message = Message(
            type=MessageType.TOOL_CALL,
            content=parameters,
            source="kernel",
            target=f"tool.{tool_name}",
            metadata={"context": context} if context else {}
        )
        return await self.bus.send(message)

    def get_tool_definitions(self) -> list:
        """獲取所有工具的定義

        Returns:
            工具定義列表（OpenAI function calling 格式）
        """
        return [tool.definition for tool in self.tools.values()]


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

        # 優先傳遞 kernel（用於 ReAct 工具調用）
        if 'kernel' in params and 'llm_provider' in params:
            self.agent = agent_class(llm_provider=kernel.llm, kernel=kernel)
        elif 'kernel' in params:
            self.agent = agent_class(kernel=kernel)
        elif 'llm_provider' in params:
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