"""
RAG Agent - 智能代理邏輯
支援多步推理、工具呼叫、串流輸出、文件篩選
"""

import json
import asyncio
from typing import AsyncGenerator, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from openai import OpenAI
import os

class EventType(Enum):
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ANSWER = "answer"
    SOURCE = "source"
    DONE = "done"
    ERROR = "error"

@dataclass
class AgentEvent:
    type: EventType
    content: str
    data: Optional[dict] = None
    
    def to_sse(self) -> str:
        """轉換為 Server-Sent Events 格式"""
        payload = {
            "type": self.type.value,
            "content": self.content,
        }
        if self.data:
            payload["data"] = self.data
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


class RAGAgent:
    """RAG 智能代理"""
    
    def __init__(self, retriever, generator):
        self.retriever = retriever
        self.generator = generator
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 定義可用工具
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "rag_search",
                    "description": "在知識庫中進行語意搜尋，找出與查詢相關的文件片段",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜尋查詢，可以是關鍵字或自然語言問題"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "返回結果數量，預設 5",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "rag_search_multiple",
                    "description": "用多個不同的查詢搜尋知識庫，適合需要比較或整合多個主題的問題",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "queries": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "多個搜尋查詢的列表"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "每個查詢返回的結果數量，預設 3",
                                "default": 3
                            }
                        },
                        "required": ["queries"]
                    }
                }
            }
        ]
        
        self.system_prompt = """你是一個專業的企業知識庫助手，負責回答用戶關於文件內容的問題。

你的工作流程：
1. 分析用戶的問題，思考需要搜尋什麼資訊
2. 使用 rag_search 或 rag_search_multiple 工具搜尋知識庫
3. 根據搜尋結果，整理出清晰、有條理的回答
4. 如果問題涉及多個主題（如比較），使用 rag_search_multiple 一次搜尋多個關鍵字

回答規範：
- 用繁體中文回答
- 回答要有結構，善用標題和條列
- 必須基於搜尋到的內容回答，不要編造
- 如果搜尋結果不足以回答問題，誠實告知用戶

請先思考問題需要什麼資訊，然後決定搜尋策略。"""

    def _filtered_search(self, query: str, top_k: int, selected_docs: Optional[List[str]] = None):
        """🆕 支援文件篩選的搜尋"""
        from qdrant_client import QdrantClient
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # 如果沒有篩選，使用原本的 retriever
        if not selected_docs or len(selected_docs) == 0:
            return self.retriever.search(query, top_k=top_k)
        
        # 有篩選，直接查 Qdrant
        try:
            client = QdrantClient(host="localhost", port=6333)
            openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # 生成查詢向量
            embedding_response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            query_vector = embedding_response.data[0].embedding
            
            # 建立篩選條件
            if len(selected_docs) == 1:
                search_filter = Filter(
                    must=[FieldCondition(key="file_name", match=MatchValue(value=selected_docs[0]))]
                )
            else:
                search_filter = Filter(
                    should=[
                        FieldCondition(key="file_name", match=MatchValue(value=f))
                        for f in selected_docs
                    ]
                )
            
            # 執行搜尋
            results = client.query_points(
                collection_name="rag_knowledge_base",
                query=query_vector,
                query_filter=search_filter,
                limit=top_k,
                with_payload=True
            )
            
            return results.points
            
        except Exception as e:
            print(f"Filtered search error: {e}")
            # 失敗時回退到原本的搜尋
            return self.retriever.search(query, top_k=top_k)

    def _execute_tool(self, tool_name: str, arguments: dict, selected_docs: Optional[List[str]] = None) -> tuple[str, list]:
        """執行工具並返回結果，🆕 支援文件篩選"""
        sources = []
        
        if tool_name == "rag_search":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)
            
            # 🆕 使用篩選搜尋
            results = self._filtered_search(query, top_k, selected_docs)
            
            if not results:
                return "沒有找到相關結果", []
            
            output = []
            for i, hit in enumerate(results, 1):
                payload = hit.payload
                text = payload.get("text", "")[:500]
                source_info = {
                    "file_name": payload.get("file_name", "unknown"),
                    "page_label": payload.get("page_label", "?"),
                    "score": hit.score,
                    "summary": text[:100] + "..."
                }
                sources.append(source_info)
                output.append(f"[結果 {i}] 來源: {source_info['file_name']} (頁 {source_info['page_label']})")
                output.append(f"相關度: {hit.score:.3f}")
                output.append(f"內容: {text}")
                output.append("")
            
            return "\n".join(output), sources
            
        elif tool_name == "rag_search_multiple":
            queries = arguments.get("queries", [])
            top_k = arguments.get("top_k", 3)
            
            all_output = []
            for query in queries:
                # 🆕 使用篩選搜尋
                results = self._filtered_search(query, top_k, selected_docs)
                
                all_output.append(f"=== 搜尋: {query} ===")
                if not results:
                    all_output.append("沒有找到相關結果")
                else:
                    for i, hit in enumerate(results, 1):
                        payload = hit.payload
                        text = payload.get("text", "")[:400]
                        source_info = {
                            "file_name": payload.get("file_name", "unknown"),
                            "page_label": payload.get("page_label", "?"),
                            "score": hit.score,
                            "summary": text[:100] + "..."
                        }
                        # 避免重複來源
                        if not any(s["file_name"] == source_info["file_name"] and 
                                   s["page_label"] == source_info["page_label"] for s in sources):
                            sources.append(source_info)
                        all_output.append(f"[{i}] {source_info['file_name']} (頁 {source_info['page_label']}): {text[:200]}...")
                all_output.append("")
            
            return "\n".join(all_output), sources
        
        return "未知工具", []

    async def chat_stream(self, user_message: str, selected_docs: Optional[List[str]] = None) -> AsyncGenerator[AgentEvent, None]:
        """串流式對話，返回 Agent 事件，🆕 支援文件篩選"""
        
        # 🆕 如果有篩選，在 system prompt 中提示
        system_prompt = self.system_prompt
        if selected_docs and len(selected_docs) > 0:
            docs_list = ", ".join(selected_docs)
            system_prompt += f"\n\n注意：用戶選擇了以下文件進行搜尋：{docs_list}。請只在這些文件中搜尋。"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        all_sources = []
        max_iterations = 5  # 防止無限迴圈
        
        for iteration in range(max_iterations):
            try:
                # 呼叫 OpenAI
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto"
                )
                
                assistant_message = response.choices[0].message
                
                # 檢查是否有工具呼叫
                if assistant_message.tool_calls:
                    # 有工具呼叫
                    messages.append(assistant_message)
                    
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)
                        
                        # 發送 thinking 事件
                        if tool_name == "rag_search":
                            thinking = f"搜尋知識庫：「{arguments.get('query', '')}」"
                        elif tool_name == "rag_search_multiple":
                            queries = arguments.get('queries', [])
                            thinking = f"多重搜尋：{', '.join(queries)}"
                        else:
                            thinking = f"執行工具：{tool_name}"
                        
                        yield AgentEvent(
                            type=EventType.THINKING,
                            content=thinking
                        )
                        
                        # 發送工具呼叫事件
                        yield AgentEvent(
                            type=EventType.TOOL_CALL,
                            content=tool_name,
                            data={"arguments": arguments}
                        )
                        
                        # 🆕 執行工具（傳入 selected_docs）
                        result, sources = self._execute_tool(tool_name, arguments, selected_docs)
                        all_sources.extend(sources)
                        
                        # 發送工具結果事件
                        result_preview = result[:200] + "..." if len(result) > 200 else result
                        yield AgentEvent(
                            type=EventType.TOOL_RESULT,
                            content=f"找到 {len(sources)} 個相關片段",
                            data={"preview": result_preview}
                        )
                        
                        # 加入工具結果到對話
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })
                        
                        # 小延遲讓前端有時間顯示
                        await asyncio.sleep(0.1)
                
                else:
                    # 沒有工具呼叫，返回最終回答
                    final_answer = assistant_message.content
                    
                    # 串流輸出回答
                    yield AgentEvent(
                        type=EventType.ANSWER,
                        content=final_answer
                    )
                    
                    # 發送來源（去重並排序）
                    unique_sources = []
                    seen = set()
                    for s in all_sources:
                        key = (s["file_name"], s["page_label"])
                        if key not in seen:
                            seen.add(key)
                            unique_sources.append(s)
                    
                    # 按相關度排序
                    unique_sources.sort(key=lambda x: x.get("score", 0), reverse=True)
                    
                    if unique_sources:
                        yield AgentEvent(
                            type=EventType.SOURCE,
                            content=f"{len(unique_sources)} 個參考來源",
                            data={"sources": unique_sources[:5]}
                        )
                    
                    # 完成
                    yield AgentEvent(type=EventType.DONE, content="")
                    return
                    
            except Exception as e:
                yield AgentEvent(
                    type=EventType.ERROR,
                    content=f"處理錯誤: {str(e)}"
                )
                return
        
        # 達到最大迭代次數
        yield AgentEvent(
            type=EventType.ERROR,
            content="處理超時，請簡化問題後重試"
        )