"""
Orchestrator Actor - 主編排器
協調 Planner、Router、Executor、Memory 執行任務
"""

from typing import Dict, Any, Optional, AsyncIterator, List
import asyncio
import logging
import time
import os
from pathlib import Path

# 確保載入 .env 檔案（使用專案根目錄）
from dotenv import load_dotenv
_project_root = Path(__file__).resolve().parent.parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)

from orchestrator.actors.base import Actor, ActorMessage, SupervisorActor
from core.protocols import (
    Event, EventType, Intent, Task, TaskStatus,
    Context
)
from core.events import create_event

logger = logging.getLogger(__name__)


class OrchestratorActor(SupervisorActor):
    """
    主編排 Actor
    
    職責:
    - 接收用戶意圖
    - 協調 Planner 分解任務
    - 路由任務到適當服務
    - 追蹤執行狀態
    - 管理記憶
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(name="orchestrator", config=config)
        
        # 子 Actor
        self.planner = None
        self.router = None
        self.executor = None
        self.memory_actor = None
        
        # 狀態
        self.active_intents: Dict[str, Dict] = {}
        self.task_results: Dict[str, Any] = {}
        
        # 回調
        self._response_callbacks: Dict[str, asyncio.Queue] = {}
    
    async def on_start(self) -> None:
        """啟動時初始化子 Actor"""
        # 建立子 Actor
        from orchestrator.actors.planner import PlannerActor
        from orchestrator.actors.router import RouterActor
        from orchestrator.actors.executor import ExecutorActor
        from orchestrator.actors.memory import MemoryActor
        
        self.planner = self.spawn_child(
            PlannerActor, 
            "planner",
            config=self.config.get("planner", {})
        )
        
        self.router = self.spawn_child(
            RouterActor,
            "router",
            config=self.config.get("router", {})
        )
        
        self.executor = self.spawn_child(
            ExecutorActor,
            "executor",
            config=self.config.get("executor", {})
        )
        
        self.memory_actor = self.spawn_child(
            MemoryActor,
            "memory",
            config=self.config.get("memory", {})
        )
        
        logger.info("Orchestrator children created")
    
    async def handle_message(self, message: ActorMessage) -> Optional[Any]:
        """處理訊息"""
        content = message.content
        msg_type = content.get("type")
        
        if msg_type == "intent":
            # 處理用戶意圖
            return await self._handle_intent(content, message.correlation_id)
        
        elif msg_type == "plan":
            # 收到 Planner 的計畫
            await self._handle_plan(content, message.correlation_id)
        
        elif msg_type == "task_result":
            # 收到任務執行結果
            await self._handle_task_result(content, message.correlation_id)
        
        elif msg_type == "child_error":
            # 子 Actor 錯誤
            await self._handle_child_error(content)
        
        return None
    
    async def process_intent(
        self, 
        intent_data: Dict[str, Any]
    ) -> AsyncIterator[Event]:
        """
        處理用戶意圖 (外部呼叫入口)
        
        Args:
            intent_data: 意圖資料
            
        Yields:
            處理過程中的事件
        """
        correlation_id = intent_data.get("id", str(time.time()))
        
        # 建立回應佇列
        response_queue = asyncio.Queue()
        self._response_callbacks[correlation_id] = response_queue
        
        try:
            # 發送意圖訊息給自己
            await self.send(ActorMessage(
                sender="external",
                content={
                    "type": "intent",
                    "payload": intent_data
                },
                correlation_id=correlation_id
            ))
            
            # 持續產出事件直到完成
            while True:
                try:
                    event = await asyncio.wait_for(
                        response_queue.get(),
                        timeout=60.0  # 總超時
                    )
                    
                    yield event
                    
                    # 檢查是否完成
                    if event.type in (EventType.DONE, EventType.ERROR):
                        break
                        
                except asyncio.TimeoutError:
                    yield create_event(
                        EventType.ERROR,
                        content="Processing timeout",
                        correlation_id=correlation_id
                    )
                    break
                    
        finally:
            self._response_callbacks.pop(correlation_id, None)
    
    async def _handle_intent(
        self, 
        content: Dict[str, Any],
        correlation_id: str
    ) -> None:
        """處理意圖"""
        intent_data = content.get("payload", {})
        
        # 記錄活躍意圖
        self.active_intents[correlation_id] = {
            "intent": intent_data,
            "status": "planning",
            "started_at": time.time()
        }
        
        # 發送 thinking 事件
        await self._emit_event(
            EventType.THINKING,
            "分析問題並規劃任務...",
            correlation_id
        )
        
        # 發送給 Planner
        await self.tell(self.planner, {
            "type": "create_plan",
            "intent": intent_data
        }, correlation_id)
    
    async def _handle_plan(
        self, 
        content: Dict[str, Any],
        correlation_id: str
    ) -> None:
        """處理規劃結果"""
        plan = content.get("plan", {})
        tasks = plan.get("tasks", [])
        
        if correlation_id in self.active_intents:
            self.active_intents[correlation_id]["status"] = "executing"
            self.active_intents[correlation_id]["plan"] = plan
        
        if not tasks:
            # 沒有任務需要執行，直接生成回答
            await self._generate_response(
                plan.get("analysis", ""),
                correlation_id
            )
            return
        
        # 發送 thinking 事件（分析結果）
        analysis = plan.get("analysis", "")
        if analysis:
            await self._emit_event(
                EventType.THINKING,
                analysis,
                correlation_id
            )
        
        # 發送 planning 事件（詳細的任務規劃）- 新增！
        # 收集所有查詢
        all_queries = []
        task_descriptions = []
        for task in tasks:
            params = task.get("parameters", {})
            if "queries" in params:
                all_queries.extend(params["queries"])
            elif "query" in params:
                all_queries.append(params["query"])
            task_descriptions.append({
                "id": task.get("id"),
                "tool": task.get("tool"),
                "description": task.get("description", task.get("tool"))
            })
        
        # 發送 planning 事件
        await self._emit_planning_event(
            correlation_id,
            summary=f"將執行 {len(tasks)} 個任務來回答問題",
            queries=all_queries,
            tasks=task_descriptions
        )
        
        # 按執行順序執行任務
        execution_order = plan.get("execution_order", [t["id"] for t in tasks])
        task_map = {t["id"]: t for t in tasks}
        
        for task_id in execution_order:
            task_data = task_map.get(task_id)
            if not task_data:
                continue
            
            tool_name = task_data.get("tool", "unknown")
            params = task_data.get("parameters", {})
            
            # 發送更詳細的 tool_call 事件
            await self._emit_event(
                EventType.TOOL_CALL,
                tool_name,
                correlation_id,
                data={
                    "arguments": params,
                    "queries": params.get("queries", [params.get("query")] if params.get("query") else []),
                    "description": task_data.get("description", "")
                }
            )
            
            # 執行任務
            await self.tell(self.executor, {
                "type": "execute_task",
                "task": task_data,
                "context": self.active_intents.get(correlation_id, {}).get("intent", {}).get("context", {})
            }, correlation_id)
            
            # 等待任務結果
            result = await self._wait_for_task_result(task_id, correlation_id)
            
            # 發送更詳細的 tool_result 事件
            results_count = 0
            if isinstance(result, dict):
                results_count = len(result.get('results', []))
            
            await self._emit_event(
                EventType.TOOL_RESULT,
                f"找到 {results_count} 個相關結果",
                correlation_id,
                data={
                    "preview": str(result)[:200],
                    "results_count": results_count
                }
            )
            
            # 儲存結果供後續任務使用
            self.task_results[task_id] = result
        
        # 所有任務完成，生成最終回答
        await self._generate_final_answer(correlation_id)
    
    async def _handle_task_result(
        self, 
        content: Dict[str, Any],
        correlation_id: str
    ) -> None:
        """處理任務結果"""
        task_id = content.get("task_id")
        result = content.get("result")
        
        if task_id:
            self.task_results[task_id] = result
    
    async def _wait_for_task_result(
        self, 
        task_id: str,
        correlation_id: str,
        timeout: float = 30.0
    ) -> Any:
        """等待任務結果"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if task_id in self.task_results:
                return self.task_results.pop(task_id)
            await asyncio.sleep(0.1)
        
        return {"error": "Task timeout"}
    
    async def _generate_response(
        self,
        content: str,
        correlation_id: str
    ) -> None:
        """生成簡單回應"""
        await self._emit_event(EventType.ANSWER, content, correlation_id)
        await self._emit_event(EventType.DONE, "", correlation_id)
    
    async def _generate_final_answer(
        self,
        correlation_id: str
    ) -> None:
        """根據任務結果生成最終回答"""
        intent_data = self.active_intents.get(correlation_id, {}).get("intent", {})
        plan = self.active_intents.get(correlation_id, {}).get("plan", {})
        
        # 收集所有任務結果
        all_results = []
        all_sources = []
        context_texts = []
        
        logger.info(f"📝 [Orchestrator] 開始生成最終回答...")
        logger.info(f"📝 [Orchestrator] 任務數量: {len(plan.get('tasks', []))}")
        logger.info(f"📝 [Orchestrator] 已保存結果數量: {len(self.task_results)}")
        
        for task in plan.get("tasks", []):
            task_id = task.get("id")
            if task_id in self.task_results:
                result = self.task_results[task_id]
                all_results.append({
                    "task": task,
                    "result": result
                })
                
                logger.info(f"📝 [Orchestrator] 處理任務 {task_id} 結果...")
                
                # 提取上下文文本
                if isinstance(result, dict):
                    # 直接從 results 列表提取（適用於 rag_search 和 rag_search_multiple）
                    if "results" in result and isinstance(result["results"], list):
                        for r in result["results"]:
                            if isinstance(r, dict) and "text" in r:
                                text = r["text"]
                                if text and len(text) > 20:  # 過濾過短的文本
                                    context_texts.append(text)
                                    logger.debug(f"📝 提取文本: {text[:50]}...")
                    
                    # 收集來源
                    if "sources" in result:
                        all_sources.extend(result["sources"])
        
        logger.info(f"📝 [Orchestrator] 提取到 {len(context_texts)} 個上下文文本")
        logger.info(f"📝 [Orchestrator] 收集到 {len(all_sources)} 個來源")
        
        # 去重來源
        seen_sources = set()
        unique_sources = []
        for src in all_sources:
            key = (src.get("file_name", ""), src.get("page_label", ""))
            if key not in seen_sources:
                seen_sources.add(key)
                unique_sources.append(src)
        
        # 發送 "正在生成回答" 事件
        await self._emit_generating_event(
            correlation_id,
            context_count=len(context_texts),
            source_count=len(unique_sources)
        )
        
        # 使用 LLM 生成最終回答
        try:
            from openai import AsyncOpenAI
            
            # 確保 .env 已載入
            load_dotenv(_env_path, override=True)
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OPENAI_API_KEY not set for final answer generation")
                answer = "無法生成回答：API Key 未設置"
                await self._emit_event(EventType.ANSWER, answer, correlation_id)
            else:
                client = AsyncOpenAI(api_key=api_key)
                
                # 建構上下文
                context_text = "\n\n---\n\n".join(context_texts[:15])  # 限制上下文長度
                
                # 建構提示
                messages = [
                    {
                        "role": "system",
                        "content": """你是一個專業的知識助手。根據用戶的問題和檢索到的相關資料，生成清晰、準確、有結構的回答。

## 回答原則
1. **準確性**: 只基於提供的資料回答，不要編造
2. **結構化**: 使用標題、條列、段落組織回答
3. **完整性**: 盡可能涵蓋問題的各個面向
4. **可讀性**: 用繁體中文，語言清晰易懂

## 回答格式
- 如果是概述類問題：先給出總結，再分點詳述
- 如果是比較類問題：使用表格或對比列表
- 如果是解釋類問題：由淺入深，逐步解釋
- 如果資料不足：誠實說明，並指出已知的部分"""
                    },
                    {
                        "role": "user",
                        "content": f"""## 用戶問題
{intent_data.get('content', '')}

## 檢索到的相關資料
{context_text}

## 任務
請根據以上資料，回答用戶的問題。回答要全面且有結構。"""
                    }
                ]
                
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.7
                )
                
                answer = response.choices[0].message.content
                
                # 發送回答
                await self._emit_event(EventType.ANSWER, answer, correlation_id)
                
                # 發送來源
                if unique_sources:
                    await self._emit_event(
                        EventType.SOURCE,
                        f"{len(unique_sources)} 個參考來源",
                        correlation_id,
                        data={"sources": unique_sources[:5]}
                    )
            
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            await self._emit_event(
                EventType.ANSWER,
                f"處理完成，但生成回答時發生錯誤: {e}",
                correlation_id
            )
        
        # 完成
        await self._emit_event(EventType.DONE, "", correlation_id)
        
        # 清理
        self.active_intents.pop(correlation_id, None)
    
    async def _emit_event(
        self,
        event_type: EventType,
        content: str,
        correlation_id: str,
        data: Optional[Dict] = None
    ) -> None:
        """發送事件到回調佇列"""
        event = create_event(
            event_type,
            content=content,
            data=data,
            source="orchestrator",
            correlation_id=correlation_id
        )
        
        queue = self._response_callbacks.get(correlation_id)
        if queue:
            await queue.put(event)
    
    async def _emit_planning_event(
        self,
        correlation_id: str,
        summary: str,
        queries: List[str],
        tasks: List[Dict]
    ) -> None:
        """發送規劃事件（包含查詢列表和任務描述）"""
        # 使用自定義事件格式
        import json
        from core.protocols import Event
        
        event = Event(
            type=EventType.PLAN,  # 使用 PLAN 事件類型
            payload={
                "content": summary,
                "data": {
                    "type": "planning",  # 前端用這個判斷
                    "summary": summary,
                    "queries": queries,
                    "tasks": tasks
                }
            },
            timestamp=time.time(),
            source="orchestrator",
            correlation_id=correlation_id
        )
        
        queue = self._response_callbacks.get(correlation_id)
        if queue:
            await queue.put(event)
    
    async def _emit_generating_event(
        self,
        correlation_id: str,
        context_count: int,
        source_count: int
    ) -> None:
        """發送正在生成回答的事件"""
        from core.protocols import Event
        
        event = Event(
            type=EventType.THINKING,  # 使用 THINKING 類型，前端會識別為 generating
            payload={
                "content": f"正在根據 {context_count} 段內容和 {source_count} 個來源生成回答...",
                "data": {
                    "type": "generating",
                    "context_count": context_count,
                    "source_count": source_count
                }
            },
            timestamp=time.time(),
            source="orchestrator",
            correlation_id=correlation_id
        )
        
        queue = self._response_callbacks.get(correlation_id)
        if queue:
            await queue.put(event)
