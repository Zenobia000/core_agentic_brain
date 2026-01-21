# ⚡ 後端架構設計 - FastAPI + Clean Architecture

## 🎯 架構概覽

從 **Monolithic Web App** 重構為 **分層架構 + 事件驅動** 的現代後端應用

### 設計原則
- **Clean Architecture**: 分離關注點，依賴反轉
- **Domain-Driven Design**: 以業務領域為核心
- **Event-Driven**: 鬆耦合的事件通訊
- **CQRS**: 命令查詢責任分離

### 技術棧
- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL + SQLAlchemy 2.0
- **Cache**: Redis + aioredis
- **Message Queue**: Celery + Redis
- **WebSocket**: python-socketio
- **Monitoring**: Prometheus + Grafana

---

## 📁 後端目錄結構

```
backend/
├── app/
│   ├── api/                    # API 路由層
│   │   ├── deps.py            # 依賴注入
│   │   ├── middleware.py      # 中間件
│   │   ├── v1/               # API v1 版本
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py   # 會話管理 API
│   │   │   ├── agents.py     # Agent 相關 API
│   │   │   ├── tools.py      # 工具狀態 API
│   │   │   └── monitoring.py # 監控 API
│   │   └── v2/               # API v2 版本 (未來擴展)
│   │       └── __init__.py
│   ├── core/                  # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py         # 配置管理
│   │   ├── security.py       # 安全相關
│   │   ├── logging.py        # 日誌配置
│   │   ├── database.py       # 資料庫連接
│   │   └── events.py         # 事件總線
│   ├── domain/               # 領域層 (DDD)
│   │   ├── __init__.py
│   │   ├── entities/         # 實體
│   │   │   ├── session.py
│   │   │   ├── agent.py
│   │   │   └── execution.py
│   │   ├── services/         # 領域服務
│   │   │   ├── agent_service.py
│   │   │   ├── optimization_service.py
│   │   │   └── circuit_breaker_service.py
│   │   └── events/           # 領域事件
│   │       ├── session_events.py
│   │       └── agent_events.py
│   ├── infrastructure/       # 基礎設施層
│   │   ├── __init__.py
│   │   ├── database/         # 資料庫實現
│   │   │   ├── models.py     # SQLAlchemy 模型
│   │   │   └── repositories/ # Repository 實現
│   │   │       ├── session_repo.py
│   │   │       ├── agent_repo.py
│   │   │       └── metric_repo.py
│   │   ├── external/         # 外部服務
│   │   │   ├── manus_adapter.py
│   │   │   └── llm_adapter.py
│   │   ├── messaging/        # 訊息系統
│   │   │   ├── event_bus.py
│   │   │   └── handlers.py
│   │   └── monitoring/       # 監控實現
│   │       ├── metrics.py
│   │       └── health.py
│   ├── application/          # 應用層
│   │   ├── __init__.py
│   │   ├── commands/         # 命令 (CQRS)
│   │   │   ├── create_session.py
│   │   │   ├── execute_agent.py
│   │   │   └── optimize_tokens.py
│   │   ├── queries/          # 查詢 (CQRS)
│   │   │   ├── session_queries.py
│   │   │   └── metric_queries.py
│   │   ├── handlers/         # 命令/查詢處理器
│   │   │   ├── session_handlers.py
│   │   │   └── agent_handlers.py
│   │   └── services/         # 應用服務
│   │       ├── session_service.py
│   │       ├── websocket_service.py
│   │       └── notification_service.py
│   ├── presentation/         # 表現層
│   │   ├── __init__.py
│   │   ├── schemas/          # API Schema
│   │   │   ├── requests.py
│   │   │   ├── responses.py
│   │   │   └── websocket.py
│   │   └── websocket/        # WebSocket 處理
│   │       ├── manager.py
│   │       ├── handlers.py
│   │       └── events.py
│   ├── shared/               # 共享模組
│   │   ├── __init__.py
│   │   ├── exceptions.py     # 自定義例外
│   │   ├── constants.py      # 常數定義
│   │   └── utils.py          # 工具函數
│   └── main.py              # 應用入口
├── tests/                    # 測試
│   ├── unit/                # 單元測試
│   ├── integration/         # 整合測試
│   └── e2e/                 # 端到端測試
├── migrations/              # 資料庫遷移
├── scripts/                 # 部署腳本
├── requirements.txt         # Python 依賴
├── Dockerfile
└── docker-compose.yml
```

---

## 🏗️ 分層架構實現

### 1. 表現層 (Presentation Layer)

#### API 路由
```python
# app/api/v1/sessions.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.application.commands.create_session import CreateSessionCommand
from app.application.queries.session_queries import SessionQueries
from app.presentation.schemas.requests import CreateSessionRequest
from app.presentation.schemas.responses import SessionResponse
from app.api.deps import get_session_service, get_current_user

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    background_tasks: BackgroundTasks,
    session_service: SessionService = Depends(get_session_service),
    current_user: User = Depends(get_current_user)
) -> SessionResponse:
    """創建新的 AI 會話"""

    try:
        # 建立命令
        command = CreateSessionCommand(
            user_id=current_user.id,
            prompt=request.prompt,
            task_type=request.task_type,
            token_budget=request.token_budget
        )

        # 執行命令
        session = await session_service.create_session(command)

        # 背景執行 Agent
        background_tasks.add_task(
            session_service.execute_agent_async,
            session.id,
            request.prompt
        )

        return SessionResponse.from_domain(session)

    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    queries: SessionQueries = Depends(get_session_queries)
) -> SessionResponse:
    """獲取會話詳細資訊"""

    session = await queries.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse.from_domain(session)

@router.post("/{session_id}/stop")
async def stop_session(
    session_id: UUID,
    session_service: SessionService = Depends(get_session_service)
) -> dict:
    """停止會話執行"""

    await session_service.stop_session(session_id)
    return {"status": "stopped"}
```

#### WebSocket 管理
```python
# app/presentation/websocket/manager.py
import asyncio
from typing import Dict, Set
from fastapi import WebSocket
from app.domain.events.session_events import SessionEvent
from app.core.events import EventBus

class ConnectionManager:
    """WebSocket 連接管理器"""

    def __init__(self, event_bus: EventBus):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_sessions: Dict[WebSocket, str] = {}
        self.event_bus = event_bus

        # 訂閱事件
        self.event_bus.subscribe("session.*", self.handle_session_event)
        self.event_bus.subscribe("agent.*", self.handle_agent_event)
        self.event_bus.subscribe("tool.*", self.handle_tool_event)

    async def connect(self, websocket: WebSocket, session_id: str):
        """建立 WebSocket 連接"""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()

        self.active_connections[session_id].add(websocket)
        self.connection_sessions[websocket] = session_id

    async def disconnect(self, websocket: WebSocket):
        """斷開 WebSocket 連接"""
        session_id = self.connection_sessions.pop(websocket, None)
        if session_id and session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)

            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def send_to_session(self, session_id: str, message: dict):
        """向指定會話發送訊息"""
        if session_id in self.active_connections:
            disconnected = []

            for connection in self.active_connections[session_id].copy():
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            # 清理斷線的連接
            for conn in disconnected:
                await self.disconnect(conn)

    async def broadcast(self, message: dict):
        """廣播訊息到所有連接"""
        for session_connections in self.active_connections.values():
            for connection in session_connections.copy():
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def handle_session_event(self, event: SessionEvent):
        """處理會話事件"""
        message = {
            "type": "session_update",
            "event": event.event_type,
            "session_id": str(event.session_id),
            "data": event.data,
            "timestamp": event.timestamp.isoformat()
        }

        await self.send_to_session(str(event.session_id), message)

    async def handle_agent_event(self, event):
        """處理 Agent 事件"""
        message = {
            "type": "agent_update",
            "event": event.event_type,
            "session_id": str(event.session_id),
            "data": {
                "thinking_step": event.thinking_step,
                "token_usage": event.token_usage,
                "tool_calls": event.tool_calls
            },
            "timestamp": event.timestamp.isoformat()
        }

        await self.send_to_session(str(event.session_id), message)

    async def handle_tool_event(self, event):
        """處理工具事件"""
        message = {
            "type": "tool_status",
            "tool_name": event.tool_name,
            "status": event.status,
            "error": event.error,
            "timestamp": event.timestamp.isoformat()
        }

        await self.broadcast(message)
```

### 2. 應用層 (Application Layer)

#### 命令處理器
```python
# app/application/commands/create_session.py
from dataclasses import dataclass
from uuid import UUID
from typing import Optional

@dataclass
class CreateSessionCommand:
    """創建會話命令"""
    user_id: UUID
    prompt: str
    task_type: str = "general"
    token_budget: int = 4000

# app/application/handlers/session_handlers.py
from app.domain.entities.session import Session
from app.domain.services.agent_service import AgentDomainService
from app.infrastructure.database.repositories.session_repo import SessionRepository
from app.core.events import EventBus

class CreateSessionHandler:
    """創建會話命令處理器"""

    def __init__(
        self,
        session_repo: SessionRepository,
        agent_service: AgentDomainService,
        event_bus: EventBus
    ):
        self.session_repo = session_repo
        self.agent_service = agent_service
        self.event_bus = event_bus

    async def handle(self, command: CreateSessionCommand) -> Session:
        """處理創建會話命令"""

        # 創建會話實體
        session = Session.create(
            user_id=command.user_id,
            prompt=command.prompt,
            task_type=command.task_type,
            token_budget=command.token_budget
        )

        # 保存到資料庫
        await self.session_repo.save(session)

        # 發布事件
        await self.event_bus.publish(
            "session.created",
            {
                "session_id": session.id,
                "user_id": session.user_id,
                "task_type": session.task_type
            }
        )

        return session
```

#### 應用服務
```python
# app/application/services/session_service.py
from typing import Optional
from uuid import UUID
from app.application.commands.create_session import CreateSessionCommand
from app.application.handlers.session_handlers import CreateSessionHandler
from app.domain.entities.session import Session
from app.domain.services.agent_service import AgentDomainService
from app.infrastructure.external.manus_adapter import ManusAdapter

class SessionService:
    """會話應用服務"""

    def __init__(
        self,
        create_handler: CreateSessionHandler,
        agent_service: AgentDomainService,
        manus_adapter: ManusAdapter
    ):
        self.create_handler = create_handler
        self.agent_service = agent_service
        self.manus_adapter = manus_adapter

    async def create_session(self, command: CreateSessionCommand) -> Session:
        """創建新會話"""
        return await self.create_handler.handle(command)

    async def execute_agent_async(self, session_id: UUID, prompt: str):
        """異步執行 Agent (背景任務)"""

        try:
            # 更新會話狀態為處理中
            await self.update_session_status(session_id, "processing")

            # 執行 Agent
            result = await self.manus_adapter.execute(
                session_id=session_id,
                prompt=prompt,
                optimization_enabled=True
            )

            # 更新結果
            await self.update_session_result(session_id, result)

        except Exception as e:
            # 處理錯誤
            await self.handle_execution_error(session_id, str(e))

    async def stop_session(self, session_id: UUID):
        """停止會話執行"""

        # 通知 Agent 停止
        await self.manus_adapter.cancel_execution(session_id)

        # 更新狀態
        await self.update_session_status(session_id, "stopped")

    async def update_session_status(self, session_id: UUID, status: str):
        """更新會話狀態"""
        # 實現狀態更新邏輯
        pass

    async def update_session_result(self, session_id: UUID, result: dict):
        """更新會話結果"""
        # 實現結果更新邏輯
        pass

    async def handle_execution_error(self, session_id: UUID, error: str):
        """處理執行錯誤"""
        # 實現錯誤處理邏輯
        pass
```

### 3. 領域層 (Domain Layer)

#### 實體
```python
# app/domain/entities/session.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

class SessionStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"

class TaskType(Enum):
    SIMPLE_QUERY = "simple_query"
    WEB_SEARCH = "web_search"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    GENERAL = "general"

@dataclass
class Session:
    """會話實體"""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    status: SessionStatus = field(default=SessionStatus.PENDING)
    task_type: TaskType = field(default=TaskType.GENERAL)
    prompt: str = ""
    result: Optional[str] = None
    token_budget: int = 4000
    token_used: int = 0
    optimization_enabled: bool = True
    workspace_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    # 領域事件
    _domain_events: list = field(default_factory=list, init=False)

    @classmethod
    def create(
        cls,
        user_id: UUID,
        prompt: str,
        task_type: str = "general",
        token_budget: int = 4000
    ) -> "Session":
        """創建新會話"""

        session = cls(
            user_id=user_id,
            prompt=prompt,
            task_type=TaskType(task_type),
            token_budget=token_budget
        )

        # 添加領域事件
        session._domain_events.append(
            SessionCreatedEvent(
                session_id=session.id,
                user_id=session.user_id,
                task_type=session.task_type
            )
        )

        return session

    def start_processing(self):
        """開始處理"""
        if self.status != SessionStatus.PENDING:
            raise DomainException("Session is not in pending status")

        self.status = SessionStatus.PROCESSING
        self.updated_at = datetime.now()

        self._domain_events.append(
            SessionProcessingStartedEvent(session_id=self.id)
        )

    def complete(self, result: str, token_used: int):
        """完成處理"""
        if self.status != SessionStatus.PROCESSING:
            raise DomainException("Session is not processing")

        self.status = SessionStatus.COMPLETED
        self.result = result
        self.token_used = token_used
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()

        self._domain_events.append(
            SessionCompletedEvent(
                session_id=self.id,
                result=result,
                token_used=token_used
            )
        )

    def fail(self, error_message: str):
        """處理失敗"""
        self.status = SessionStatus.FAILED
        self.result = f"Error: {error_message}"
        self.updated_at = datetime.now()

        self._domain_events.append(
            SessionFailedEvent(
                session_id=self.id,
                error=error_message
            )
        )

    def stop(self):
        """停止處理"""
        if self.status not in [SessionStatus.PENDING, SessionStatus.PROCESSING]:
            raise DomainException("Cannot stop session in current status")

        self.status = SessionStatus.STOPPED
        self.updated_at = datetime.now()

        self._domain_events.append(
            SessionStoppedEvent(session_id=self.id)
        )

    def update_token_usage(self, used: int):
        """更新 Token 使用量"""
        if used > self.token_budget:
            raise DomainException("Token usage exceeds budget")

        self.token_used = used
        self.updated_at = datetime.now()

    def get_domain_events(self) -> list:
        """獲取領域事件"""
        return self._domain_events.copy()

    def clear_domain_events(self):
        """清除領域事件"""
        self._domain_events.clear()
```

#### 領域服務
```python
# app/domain/services/agent_service.py
from typing import Dict, Any
from uuid import UUID
from app.domain.entities.session import Session
from app.infrastructure.external.manus_adapter import ManusAdapter
from app.domain.services.optimization_service import OptimizationService
from app.domain.services.circuit_breaker_service import CircuitBreakerService

class AgentDomainService:
    """Agent 領域服務"""

    def __init__(
        self,
        manus_adapter: ManusAdapter,
        optimization_service: OptimizationService,
        circuit_breaker_service: CircuitBreakerService
    ):
        self.manus_adapter = manus_adapter
        self.optimization_service = optimization_service
        self.circuit_breaker_service = circuit_breaker_service

    async def execute_session(self, session: Session) -> Dict[str, Any]:
        """執行會話"""

        # 檢查工具狀態
        if not self.circuit_breaker_service.can_use_tool("browser_use"):
            # 使用備用策略
            return await self._execute_with_fallback(session)

        # 開始處理
        session.start_processing()

        try:
            # 優化 Token 使用
            if session.optimization_enabled:
                optimized_prompt = await self.optimization_service.optimize_prompt(
                    session.prompt,
                    session.task_type
                )
            else:
                optimized_prompt = session.prompt

            # 執行 Agent
            result = await self.manus_adapter.execute(
                session_id=session.id,
                prompt=optimized_prompt,
                task_type=session.task_type.value,
                token_budget=session.token_budget
            )

            # 更新 Token 使用
            if "token_usage" in result:
                session.update_token_usage(result["token_usage"]["total"])

            # 完成處理
            session.complete(
                result=result.get("output", ""),
                token_used=result.get("token_usage", {}).get("total", 0)
            )

            # 記錄成功
            self.circuit_breaker_service.record_success("browser_use")

            return result

        except Exception as e:
            # 記錄失敗
            self.circuit_breaker_service.record_failure("browser_use", str(e))

            # 標記會話失敗
            session.fail(str(e))

            raise

    async def _execute_with_fallback(self, session: Session) -> Dict[str, Any]:
        """使用備用策略執行"""
        # 實現備用執行邏輯
        pass
```

### 4. 基礎設施層 (Infrastructure Layer)

#### Repository 實現
```python
# app/infrastructure/database/repositories/session_repo.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.domain.entities.session import Session as SessionEntity
from app.infrastructure.database.models import Session as SessionModel

class SessionRepository:
    """會話倉儲實現"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def save(self, session: SessionEntity) -> SessionEntity:
        """保存會話"""

        # 轉換為資料庫模型
        db_session = SessionModel(
            id=session.id,
            user_id=session.user_id,
            status=session.status.value,
            task_type=session.task_type.value,
            prompt=session.prompt,
            result=session.result,
            token_budget=session.token_budget,
            token_used=session.token_used,
            optimization_enabled=session.optimization_enabled,
            workspace_path=session.workspace_path,
            created_at=session.created_at,
            updated_at=session.updated_at,
            completed_at=session.completed_at
        )

        # 檢查是否已存在
        existing = await self.db.get(SessionModel, session.id)
        if existing:
            # 更新現有記錄
            for key, value in db_session.__dict__.items():
                if not key.startswith('_'):
                    setattr(existing, key, value)
        else:
            # 新增記錄
            self.db.add(db_session)

        await self.db.commit()
        await self.db.refresh(existing or db_session)

        return session

    async def get_by_id(self, session_id: UUID) -> Optional[SessionEntity]:
        """根據 ID 獲取會話"""

        result = await self.db.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        )
        db_session = result.scalar_one_or_none()

        if not db_session:
            return None

        # 轉換為領域實體
        return SessionEntity(
            id=db_session.id,
            user_id=db_session.user_id,
            status=db_session.status,
            task_type=db_session.task_type,
            prompt=db_session.prompt,
            result=db_session.result,
            token_budget=db_session.token_budget,
            token_used=db_session.token_used,
            optimization_enabled=db_session.optimization_enabled,
            workspace_path=db_session.workspace_path,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
            completed_at=db_session.completed_at
        )

    async def list_by_user(self, user_id: UUID, limit: int = 50) -> List[SessionEntity]:
        """獲取用戶的會話列表"""

        result = await self.db.execute(
            select(SessionModel)
            .where(SessionModel.user_id == user_id)
            .order_by(SessionModel.created_at.desc())
            .limit(limit)
        )

        db_sessions = result.scalars().all()

        return [
            SessionEntity(
                id=s.id,
                user_id=s.user_id,
                status=s.status,
                task_type=s.task_type,
                prompt=s.prompt,
                result=s.result,
                token_budget=s.token_budget,
                token_used=s.token_used,
                optimization_enabled=s.optimization_enabled,
                workspace_path=s.workspace_path,
                created_at=s.created_at,
                updated_at=s.updated_at,
                completed_at=s.completed_at
            )
            for s in db_sessions
        ]

    async def update_status(self, session_id: UUID, status: str):
        """更新會話狀態"""

        await self.db.execute(
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(status=status, updated_at=datetime.now())
        )
        await self.db.commit()
```

#### 外部服務適配器
```python
# app/infrastructure/external/manus_adapter.py
from typing import Dict, Any
from uuid import UUID
from manus_core.agents.optimized import TokenAwareAgent
from manus_core.flows.flow_factory import FlowFactory, FlowType
from manus_core.tools.circuit_breaker import circuit_breaker_manager

class ManusAdapter:
    """OpenManus 核心適配器"""

    def __init__(self):
        self.active_agents: Dict[UUID, TokenAwareAgent] = {}
        self.active_flows: Dict[UUID, Any] = {}

    async def execute(
        self,
        session_id: UUID,
        prompt: str,
        task_type: str = "general",
        token_budget: int = 4000
    ) -> Dict[str, Any]:
        """執行 Agent"""

        try:
            # 創建優化版 Agent
            agent = TokenAwareAgent()
            agent.set_task_type(task_type)
            agent.token_budget = token_budget
            agent.enable_optimization = True

            # 創建 Flow
            flow = FlowFactory.create_flow(
                flow_type=FlowType.PLANNING,
                agents=agent
            )

            # 保存引用
            self.active_agents[session_id] = agent
            self.active_flows[session_id] = flow

            # 執行
            result = await flow.execute(prompt, str(session_id))

            # 獲取統計信息
            token_stats = agent.get_token_usage_report()

            return {
                "output": result,
                "token_usage": {
                    "total": agent.memory_optimizer.estimate_tokens(agent.memory.messages),
                    "budget": agent.token_budget,
                    "optimizations": agent.token_stats.get("total_optimizations", 0),
                    "saved": agent.token_stats.get("tokens_saved", 0)
                },
                "tool_status": circuit_breaker_manager.get_status()
            }

        finally:
            # 清理資源
            self.cleanup_session(session_id)

    async def cancel_execution(self, session_id: UUID):
        """取消執行"""

        if session_id in self.active_flows:
            flow = self.active_flows[session_id]
            if hasattr(flow, 'cancel'):
                await flow.cancel()

        self.cleanup_session(session_id)

    def cleanup_session(self, session_id: UUID):
        """清理會話資源"""

        self.active_agents.pop(session_id, None)
        self.active_flows.pop(session_id, None)

    def get_session_stats(self, session_id: UUID) -> Dict[str, Any]:
        """獲取會話統計"""

        agent = self.active_agents.get(session_id)
        if not agent:
            return {}

        return {
            "token_usage": agent.memory_optimizer.estimate_tokens(agent.memory.messages),
            "token_budget": agent.token_budget,
            "optimization_enabled": agent.enable_optimization,
            "task_type": agent.task_type
        }
```

### 5. 事件系統

#### 事件總線
```python
# app/core/events.py
import asyncio
from typing import Dict, List, Callable, Any
import json
from datetime import datetime

class EventBus:
    """事件總線"""

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[Dict[str, Any]] = []

    def subscribe(self, event_pattern: str, handler: Callable):
        """訂閱事件"""
        if event_pattern not in self.subscribers:
            self.subscribers[event_pattern] = []

        self.subscribers[event_pattern].append(handler)

    def unsubscribe(self, event_pattern: str, handler: Callable):
        """取消訂閱"""
        if event_pattern in self.subscribers:
            self.subscribers[event_pattern].remove(handler)

    async def publish(self, event_name: str, data: Dict[str, Any]):
        """發布事件"""

        # 記錄事件
        event = {
            "name": event_name,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        self.event_history.append(event)

        # 找到匹配的訂閱者
        for pattern, handlers in self.subscribers.items():
            if self._match_pattern(event_name, pattern):
                for handler in handlers:
                    try:
                        await handler(event)
                    except Exception as e:
                        print(f"Event handler error: {e}")

    def _match_pattern(self, event_name: str, pattern: str) -> bool:
        """匹配事件模式"""
        if pattern == "*":
            return True

        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return event_name.startswith(prefix)

        return event_name == pattern

    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """獲取事件歷史"""
        return self.event_history[-limit:]
```

---

## 🔧 依賴注入系統

```python
# app/api/deps.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.core.events import EventBus
from app.infrastructure.database.repositories.session_repo import SessionRepository
from app.application.services.session_service import SessionService
from app.domain.services.agent_service import AgentDomainService
from app.infrastructure.external.manus_adapter import ManusAdapter

# 單例實例
_event_bus = EventBus()
_manus_adapter = ManusAdapter()

def get_event_bus() -> EventBus:
    return _event_bus

def get_manus_adapter() -> ManusAdapter:
    return _manus_adapter

def get_session_repository(
    db: AsyncSession = Depends(get_db_session)
) -> SessionRepository:
    return SessionRepository(db)

def get_agent_service(
    manus_adapter: ManusAdapter = Depends(get_manus_adapter)
) -> AgentDomainService:
    return AgentDomainService(manus_adapter)

def get_session_service(
    session_repo: SessionRepository = Depends(get_session_repository),
    agent_service: AgentDomainService = Depends(get_agent_service),
    event_bus: EventBus = Depends(get_event_bus)
) -> SessionService:
    return SessionService(session_repo, agent_service, event_bus)
```

---

## 🐳 Docker 配置

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 設置環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 啟動應用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📊 監控與指標

### 健康檢查
```python
# app/infrastructure/monitoring/health.py
from typing import Dict, Any
from app.core.database import engine
from app.infrastructure.external.manus_adapter import ManusAdapter
from manus_core.tools.circuit_breaker import circuit_breaker_manager

class HealthChecker:
    """健康檢查服務"""

    def __init__(self, manus_adapter: ManusAdapter):
        self.manus_adapter = manus_adapter

    async def check_health(self) -> Dict[str, Any]:
        """執行健康檢查"""

        checks = {
            "database": await self._check_database(),
            "manus_core": await self._check_manus_core(),
            "tools": await self._check_tools()
        }

        # 整體健康狀態
        overall_status = "healthy" if all(
            check["status"] == "healthy" for check in checks.values()
        ) else "unhealthy"

        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "checks": checks
        }

    async def _check_database(self) -> Dict[str, Any]:
        """檢查資料庫連接"""
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            return {"status": "healthy", "message": "Database connection OK"}

        except Exception as e:
            return {"status": "unhealthy", "message": f"Database error: {str(e)}"}

    async def _check_manus_core(self) -> Dict[str, Any]:
        """檢查 Manus 核心"""
        try:
            # 檢查核心模組是否正常
            stats = circuit_breaker_manager.get_status()

            return {
                "status": "healthy",
                "message": "Manus core OK",
                "circuit_breakers": stats
            }

        except Exception as e:
            return {"status": "unhealthy", "message": f"Manus core error: {str(e)}"}

    async def _check_tools(self) -> Dict[str, Any]:
        """檢查工具狀態"""
        try:
            tool_status = circuit_breaker_manager.get_status()
            unhealthy_tools = [
                tool for tool, status in tool_status.items()
                if status.get("state") == "open"
            ]

            if unhealthy_tools:
                return {
                    "status": "degraded",
                    "message": f"Tools degraded: {', '.join(unhealthy_tools)}",
                    "unhealthy_tools": unhealthy_tools
                }

            return {"status": "healthy", "message": "All tools operational"}

        except Exception as e:
            return {"status": "unhealthy", "message": f"Tool check error: {str(e)}"}
```

---

## ✅ 後端重構檢查清單

### 🏗️ 架構基礎
- [ ] 分層架構建立 (Presentation/Application/Domain/Infrastructure)
- [ ] 依賴注入系統
- [ ] 事件驅動架構
- [ ] CQRS 模式實施

### 🗄️ 資料層
- [ ] PostgreSQL 資料庫設計
- [ ] SQLAlchemy 2.0 ORM
- [ ] Repository 模式實現
- [ ] 資料庫遷移系統

### 🌐 API 層
- [ ] RESTful API 設計
- [ ] API 版本管理 (v1/v2)
- [ ] OpenAPI/Swagger 文檔
- [ ] 錯誤處理標準化

### 🔌 WebSocket
- [ ] 連接管理系統
- [ ] 事件廣播機制
- [ ] 即時通訊協議
- [ ] 連接生命週期管理

### 🧠 業務邏輯
- [ ] OpenManus 核心整合
- [ ] Token 優化服務
- [ ] 熔斷器服務
- [ ] 會話管理邏輯

### 🧪 測試
- [ ] 單元測試 (Domain/Application)
- [ ] 整合測試 (Infrastructure)
- [ ] API 測試 (Presentation)
- [ ] 測試覆蓋率 90%+

### 📊 監控
- [ ] 健康檢查端點
- [ ] Prometheus 指標
- [ ] 結構化日誌
- [ ] 錯誤追蹤

### 🚀 部署
- [ ] Docker 容器化
- [ ] 環境配置管理
- [ ] 資料庫遷移腳本
- [ ] CI/CD 整合

**預期完成時間**: 2-3 週
**關鍵里程碑**: 完整的 RESTful API，支持所有前端功能需求