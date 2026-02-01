"""
系統核心 - 中央調度器 (< 150 行)
基於 Linus 原則：單一調度點，消除特殊情況
"""

import uuid
from typing import Dict, Any, Optional
from core.communication import CommunicationBus, Message, MessageType
from core.prompt_loader import PromptLoader
from core.types import TaskContext, ExecutionResult
from core.logger import log, logger, contextualize, configure as configure_logger
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
        """載入純函數工具並註冊到 ToolRegistry"""
        from core.utils import get_config_value
        from core.tool_registry import get_tool_registry, ToolCategory

        tools_config = get_config_value(self.config, "core", "tools") or \
                       get_config_value(self.config, "tools")

        enabled_tools = tools_config.get("enabled", [])
        registry = get_tool_registry()

        # Category mapping for tool classification
        category_map = {
            "files": ToolCategory.FILE,
            "python": ToolCategory.CODE,
            "websearch": ToolCategory.SEARCH,
            "ask_user": ToolCategory.USER,
            "terminate": ToolCategory.CORE,
            "shell": ToolCategory.SYSTEM,
        }

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

                        # Register in central ToolRegistry
                        category = category_map.get(tool_name, ToolCategory.CORE)
                        registry.register(
                            name=tool_name,
                            definition=tool_instance.definition,
                            category=category
                        )
                        break
                except ImportError:
                    continue
            else:
                print(f"Warning: Could not load tool {tool_name}")

        # Freeze registry after all tools loaded
        registry.freeze()

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
        """創建指定類型的代理 - 直接實例化，無需 wrapper"""
        try:
            import importlib
            module = importlib.import_module(f"agents.{agent_type}")
            agent_class_name = f"{agent_type.capitalize()}Agent"

            if hasattr(module, agent_class_name):
                AgentClass = getattr(module, agent_class_name)
                # Directly instantiate with dependencies
                return DirectAgent(
                    agent=AgentClass(llm_provider=self.llm, kernel=self),
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

        return DirectAgent(
            agent=MinimalAgent(llm_provider=self.llm, kernel=self),
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
        # Reuse existing run_id if provided in context, otherwise generate new one
        # This ensures same conversation/clarification flow shares one workspace
        if context and context.run_id:
            run_id = context.run_id
            workspace_path = context.workspace_path or self.workspace.get_run_path(run_id)
            if not workspace_path:
                workspace_path = self.workspace.create_run_context(run_id)
        else:
            run_id = f"run_{uuid.uuid4().hex[:8]}"
            workspace_path = self.workspace.create_run_context(run_id)

        # Create or update task context with run_id and workspace_path
        if context is None:
            context = TaskContext(prompt=request, run_id=run_id, workspace_path=workspace_path)
        else:
            context.run_id = run_id
            context.workspace_path = workspace_path

        # Use contextualized logging for the entire execution
        with contextualize(run_id=run_id):
            request_preview = request[:80] + "..." if len(request) > 80 else request
            log.milestone(f"Request: {request_preview}", phase="kernel")

            # 路由決策 - 使用 LLM 分析器 (雙階段: 問題重塑 -> 路由決策)
            from router.llm_analyzer import LLMTaskAnalyzer
            analyzer = LLMTaskAnalyzer(llm_provider=self.llm)
            routing = await analyzer.analyze(context)

            # Log analysis results
            strategy_name = routing.strategy if hasattr(routing, 'strategy') else "direct"
            complexity_name = routing.complexity.value if hasattr(routing, 'complexity') else "unknown"
            log.detail("routing", f"{strategy_name} ({complexity_name})")

            # ========== CLARIFICATION GATE (Fail Fast) ==========
            # Router returns strategy="clarification" when high ambiguity detected
            if strategy_name == "clarification":
                key_questions = routing.metadata.get("key_questions", [])
                questions_text = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(key_questions))
                log.warning(f"BLOCKED - Clarification needed, {len(key_questions)} questions")
                return ExecutionResult(
                    success=False,
                    response=f"為了提供準確的回應，我需要先確認：\n{questions_text}\n\n請提供更多資訊。",
                    error="CLARIFICATION_NEEDED",
                    metadata={
                        "ambiguity_level": routing.metadata.get("ambiguity_level"),
                        "key_questions": key_questions,
                        "strategy": "clarification"
                    }
                )
            # ========== END CLARIFICATION GATE ==========

            # System 2 Integration: Apply Refined Goal if available
            # This ensures that all downstream agents work with the deconstructed/refined task
            if hasattr(routing, 'metadata') and routing.metadata and "refined_goal" in routing.metadata:
                refined_goal = routing.metadata["refined_goal"]
                if refined_goal and refined_goal != context.prompt:
                    log.step("Applying refined goal")
                    # Preserve original for audit
                    context.metadata["original_prompt"] = context.prompt
                    context.metadata["system_2_thought_process"] = routing.metadata.get("thought_process", "")
                    
                    # Update context and request
                    context.prompt = refined_goal
                    request = refined_goal  # Update local var for direct execution path

            # Propagate routing metadata to context
            context.metadata["ambiguity_level"] = routing.metadata.get("ambiguity_level", "low")
            context.metadata["key_questions"] = routing.metadata.get("key_questions", [])

            # Domain expertise injection (unified from schemas/)
            if routing.metadata.get("okr_prompt"):
                context.metadata["domain_schema"] = routing.metadata.get("domain_schema")
                context.metadata["okr_prompt"] = routing.metadata.get("okr_prompt")
                context.metadata["domain"] = routing.metadata.get("domain", "none")

            # User delegation flag - controls how autonomous executor should be
            context.metadata["user_delegates"] = routing.metadata.get("user_delegates", False)

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

                log.debug(f"Dispatching to orchestrator with agents: {[r.value for r in agent_roles]}")

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

                if result.success:
                    log.task_complete()
                else:
                    log.task_failed(error=result.error)
                return result

            else:
                # 簡單任務，使用原始的單代理執行
                log.agent("executor", "Direct execution")
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
                    if result.success:
                        log.task_complete()
                    else:
                        log.task_failed(error=result.error)
                    return result
                elif isinstance(result, Message):
                    success = result.type != MessageType.ERROR
                    if success:
                        log.task_complete()
                    else:
                        log.task_failed()
                    return ExecutionResult(
                        success=success,
                        response=str(result.content),
                        metadata=result.metadata
                    )
                else:
                    log.task_complete()
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

    def get_tool_definitions(self, context: Optional["TaskContext"] = None) -> list:
        """獲取工具定義，支援根據 context 過濾

        Args:
            context: 可選的任務上下文，用於領域特定過濾

        Returns:
            工具定義列表（OpenAI function calling 格式）
        """
        from core.tool_registry import get_tool_registry, ToolCategory

        registry = get_tool_registry()

        # No context = return all tools (backward compatible)
        if context is None:
            return registry.get_all()

        # Domain-based filtering
        domain = context.metadata.get("domain_schema") if context.metadata else None

        if domain == "code":
            # Code tasks: prioritize code and file tools
            return registry.get_filtered(
                categories={ToolCategory.CORE, ToolCategory.CODE, ToolCategory.FILE, ToolCategory.USER}
            )
        elif domain == "travel":
            # Travel tasks: prioritize search and user tools
            return registry.get_filtered(
                categories={ToolCategory.CORE, ToolCategory.SEARCH, ToolCategory.USER}
            )

        # Default: return all tools
        return registry.get_all()


class DirectAgent:
    """簡化的代理包裝器 - 無 monkey-patch，直接委派

    Phase 5 重構：移除 KernelAwareAgent 的 runtime method 替換
    Agents 已經透過 PromptLoader 直接載入 prompts
    """

    def __init__(self, agent, name: str):
        """初始化代理包裝器"""
        self.agent = agent
        self.name = name

    async def handle(self, message: Message) -> Any:
        """處理訊息 - 簡單委派到 agent.execute()"""
        if message.type == MessageType.PROMPT:
            context = message.metadata.get("context", TaskContext(prompt=message.content))
            return await self.agent.execute(context)
        else:
            return Message(
                type=MessageType.ERROR,
                content=f"Agent {self.name} cannot handle {message.type}",
                source=f"agent.{self.name}",
                target=message.source
            )