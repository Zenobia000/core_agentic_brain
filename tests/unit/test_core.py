"""
Core Engine 單元測試
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch


class TestEventBus:
    """EventBus 測試"""
    
    @pytest.mark.asyncio
    async def test_register_handler(self):
        """測試註冊處理器"""
        from core.events import EventBus
        
        bus = EventBus()
        await bus.initialize()
        
        handler = AsyncMock()
        bus.register_handler("test_event", handler)
        
        assert "test_event" in bus.handlers
        assert handler in bus.handlers["test_event"]
    
    @pytest.mark.asyncio
    async def test_emit_event(self):
        """測試發送事件"""
        from core.events import EventBus, create_event
        from core.protocols import EventType
        
        bus = EventBus()
        await bus.initialize()
        
        received = []
        
        async def handler(event):
            received.append(event)
            return event
        
        bus.register_handler(EventType.INTENT.value, handler)
        
        event = create_event(EventType.INTENT, content="test")
        
        async for response in bus.emit(event):
            pass
        
        assert len(received) == 1
        assert received[0].type == EventType.INTENT


class TestContext:
    """Context Manager 測試"""
    
    @pytest.mark.asyncio
    async def test_local_context_manager(self):
        """測試本地 Context Manager"""
        from core.context import LocalContextManager
        from core.protocols import Context
        
        manager = LocalContextManager()
        await manager.initialize()
        
        # 儲存
        context = Context(
            session_id="test_session",
            user_id="test_user"
        )
        await manager.save_context(context)
        
        # 取得
        retrieved = await manager.get_context("test_session")
        assert retrieved is not None
        assert retrieved.user_id == "test_user"
        
        # 刪除
        await manager.delete_context("test_session")
        deleted = await manager.get_context("test_session")
        assert deleted is None
    
    @pytest.mark.asyncio
    async def test_update_conversation(self):
        """測試更新對話"""
        from core.context import LocalContextManager
        
        manager = LocalContextManager()
        await manager.initialize()
        
        await manager.update_conversation("session1", {
            "role": "user",
            "content": "Hello"
        })
        
        await manager.update_conversation("session1", {
            "role": "assistant",
            "content": "Hi there!"
        })
        
        context = await manager.get_context("session1")
        assert context is not None
        assert len(context.conversation_history) == 2


class TestProtocols:
    """Protocol 測試"""
    
    def test_intent_create(self):
        """測試 Intent 建立"""
        from core.protocols import Intent
        
        intent = Intent.create(
            content="Test message",
            intent_type="chat"
        )
        
        assert intent.content == "Test message"
        assert intent.type == "chat"
        assert intent.id is not None
    
    def test_event_to_sse(self):
        """測試 Event SSE 格式"""
        from core.protocols import Event, EventType
        
        event = Event(
            type=EventType.ANSWER,
            payload={"content": "Test answer"},
            source="test"
        )
        
        sse = event.to_sse()
        assert "data:" in sse
        assert "answer" in sse


class TestPolicyEngine:
    """Policy Engine 測試"""
    
    @pytest.mark.asyncio
    async def test_tool_permission(self):
        """測試工具權限"""
        from control_plane.policy.engine import PolicyEngine
        from core.protocols import Context
        
        engine = PolicyEngine()
        await engine.initialize()
        
        context = Context(
            session_id="test",
            user_id="test_user"
        )
        
        # user 角色預設可以使用 rag_search
        allowed, reason = await engine.is_tool_allowed("rag_search", context)
        assert allowed
        
        # user 角色預設不能使用 execute_bash (高風險)
        allowed, reason = await engine.is_tool_allowed("execute_bash", context)
        assert not allowed
    
    @pytest.mark.asyncio
    async def test_assign_role(self):
        """測試角色分配"""
        from control_plane.policy.engine import PolicyEngine
        from core.protocols import Context
        
        engine = PolicyEngine()
        await engine.initialize()
        
        # 分配 developer 角色
        engine.assign_role("test_user", "developer")
        
        context = Context(
            session_id="test",
            user_id="test_user"
        )
        
        # developer 可以使用 execute_bash
        allowed, reason = await engine.is_tool_allowed("execute_bash", context)
        assert allowed


class TestTracer:
    """Tracer 測試"""
    
    def test_trace_lifecycle(self):
        """測試追蹤生命週期"""
        from control_plane.ops.tracer import Tracer
        
        tracer = Tracer()
        
        # 開始追蹤
        trace_id = tracer.start_trace("test_trace")
        assert trace_id is not None
        
        # 開始 span
        span_id = tracer.start_span("test_span", trace_id)
        assert span_id is not None
        
        # 結束 span
        tracer.end_span(span_id, result="success")
        
        # 結束追蹤
        tracer.end_trace(trace_id)
        
        # 驗證
        trace = tracer.get_trace(trace_id)
        assert trace is not None
        assert trace["status"] == "completed"


class TestCostTracker:
    """Cost Tracker 測試"""
    
    def test_record_usage(self):
        """測試使用量記錄"""
        from control_plane.ops.tracer import CostTracker
        
        tracker = CostTracker()
        
        tracker.record(
            input_tokens=1000,
            output_tokens=500,
            model="gpt-4o"
        )
        
        assert tracker.total_input_tokens == 1000
        assert tracker.total_output_tokens == 500
        assert tracker.get_total_cost() > 0
    
    def test_budget_check(self):
        """測試預算檢查"""
        from control_plane.ops.tracer import CostTracker
        
        tracker = CostTracker(budget=0.01)
        
        # 記錄大量使用
        tracker.record(
            input_tokens=100000,
            output_tokens=50000,
            model="gpt-4o"
        )
        
        assert tracker.is_over_budget()


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
