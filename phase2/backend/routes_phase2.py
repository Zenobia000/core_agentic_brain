"""
Phase 2 後端路由擴展
複製這些路由到 src/main.py 中
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
import os
import time
from datetime import datetime

router = APIRouter()

# ============================================
# 1️⃣ 多 PDF 選擇器 API
# ============================================

@router.get("/documents")
async def list_documents():
    """列出所有已上傳的 PDF 文件"""
    from qdrant_client import QdrantClient
    
    pdf_dir = "data/raw"
    documents = []
    
    # 連接 Qdrant 檢查索引狀態
    try:
        client = QdrantClient(host="localhost", port=6333)
        has_qdrant = True
    except:
        has_qdrant = False
    
    if os.path.exists(pdf_dir):
        for filename in os.listdir(pdf_dir):
            if filename.lower().endswith('.pdf'):
                filepath = os.path.join(pdf_dir, filename)
                
                # 檢查是否已索引
                indexed = False
                vector_count = 0
                if has_qdrant:
                    try:
                        results, _ = client.scroll(
                            collection_name="documents",
                            scroll_filter={
                                "must": [
                                    {"key": "source", "match": {"value": filename}}
                                ]
                            },
                            limit=1,
                            with_payload=False,
                            with_vectors=False
                        )
                        indexed = len(results) > 0
                        
                        # 取得該文件的向量數量
                        if indexed:
                            all_points, _ = client.scroll(
                                collection_name="documents",
                                scroll_filter={
                                    "must": [
                                        {"key": "source", "match": {"value": filename}}
                                    ]
                                },
                                limit=1000,
                                with_payload=False,
                                with_vectors=False
                            )
                            vector_count = len(all_points)
                    except Exception as e:
                        print(f"Error checking index for {filename}: {e}")
                
                documents.append({
                    "name": filename,
                    "path": f"/files/{filename}",
                    "size": os.path.getsize(filepath),
                    "indexed": indexed,
                    "vector_count": vector_count,
                    "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                })
    
    # 按修改時間排序
    documents.sort(key=lambda x: x["modified"], reverse=True)
    
    return {"documents": documents, "total": len(documents)}


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """刪除 PDF 文件及其向量索引"""
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    
    # 刪除檔案
    filepath = f"data/raw/{filename}"
    file_deleted = False
    if os.path.exists(filepath):
        os.remove(filepath)
        file_deleted = True
    
    # 刪除向量索引
    vectors_deleted = 0
    try:
        client = QdrantClient(host="localhost", port=6333)
        
        # 先計算有多少向量
        points, _ = client.scroll(
            collection_name="documents",
            scroll_filter=Filter(
                must=[FieldCondition(key="source", match=MatchValue(value=filename))]
            ),
            limit=1000,
            with_payload=False
        )
        vectors_deleted = len(points)
        
        # 刪除向量
        client.delete(
            collection_name="documents",
            points_selector=Filter(
                must=[FieldCondition(key="source", match=MatchValue(value=filename))]
            )
        )
    except Exception as e:
        print(f"Error deleting vectors: {e}")
    
    return {
        "message": f"已刪除 {filename}",
        "file_deleted": file_deleted,
        "vectors_deleted": vectors_deleted
    }


class FilteredSearchRequest(BaseModel):
    query: str
    filenames: Optional[List[str]] = None
    top_k: int = 5


@router.post("/search/filtered")
async def filtered_search(request: FilteredSearchRequest):
    """在指定的文件中搜尋"""
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
    from openai import OpenAI
    import os
    
    client = QdrantClient(host="localhost", port=6333)
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # 生成查詢向量
    embedding_response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=request.query
    )
    query_vector = embedding_response.data[0].embedding
    
    # 建立過濾條件
    search_filter = None
    if request.filenames and len(request.filenames) > 0:
        if len(request.filenames) == 1:
            search_filter = Filter(
                must=[FieldCondition(key="source", match=MatchValue(value=request.filenames[0]))]
            )
        else:
            search_filter = Filter(
                should=[
                    FieldCondition(key="source", match=MatchValue(value=f))
                    for f in request.filenames
                ]
            )
    
    # 執行搜尋
    results = client.query_points(
        collection_name="documents",
        query=query_vector,
        query_filter=search_filter,
        limit=request.top_k,
        with_payload=True
    )
    
    return {
        "results": [
            {
                "content": point.payload.get("content", ""),
                "source": point.payload.get("source", ""),
                "page": point.payload.get("page", 1),
                "score": point.score
            }
            for point in results.points
        ],
        "query": request.query,
        "filtered_by": request.filenames
    }


# ============================================
# 2️⃣ Deep Research API
# ============================================

# 研究任務狀態存儲
research_tasks = {}


class ResearchRequest(BaseModel):
    topic: str
    documents: Optional[List[str]] = None


@router.post("/research/start")
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """啟動深度研究任務"""
    task_id = f"research_{int(time.time() * 1000)}"
    
    research_tasks[task_id] = {
        "status": "running",
        "progress": 0,
        "steps": [],
        "report": None,
        "error": None,
        "created_at": datetime.now().isoformat()
    }
    
    background_tasks.add_task(
        run_deep_research,
        task_id,
        request.topic,
        request.documents
    )
    
    return {"task_id": task_id, "status": "started"}


async def run_deep_research(task_id: str, topic: str, documents: Optional[List[str]]):
    """執行深度研究（背景任務）"""
    from openai import OpenAI
    import os
    
    task = research_tasks[task_id]
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        # Step 1: 分析主題，生成子問題
        task["steps"].append({"step": "🔍 分析研究主題", "status": "running"})
        task["progress"] = 5
        
        sub_questions = await generate_sub_questions(openai_client, topic)
        
        task["steps"][-1]["status"] = "done"
        task["steps"][-1]["result"] = f"生成 {len(sub_questions)} 個子問題"
        task["progress"] = 15
        
        # Step 2: 對每個子問題進行搜尋
        all_findings = []
        all_sources = []
        
        for i, question in enumerate(sub_questions):
            task["steps"].append({
                "step": f"📚 研究: {question[:50]}...",
                "status": "running"
            })
            
            # 搜尋相關內容
            search_results = await search_for_research(question, documents)
            
            if search_results:
                all_sources.extend(search_results)
                
                # 生成該部分的答案
                answer = await generate_section_answer(openai_client, question, search_results)
                
                all_findings.append({
                    "question": question,
                    "answer": answer,
                    "sources": search_results
                })
            
            task["steps"][-1]["status"] = "done"
            task["steps"][-1]["result"] = f"找到 {len(search_results)} 個相關段落"
            task["progress"] = 15 + (i + 1) * (65 / len(sub_questions))
        
        # Step 3: 整合報告
        task["steps"].append({"step": "📝 撰寫研究報告", "status": "running"})
        task["progress"] = 85
        
        report = await generate_final_report(openai_client, topic, all_findings)
        
        # 去重來源
        unique_sources = {}
        for s in all_sources:
            key = f"{s['source']}_p{s['page']}"
            if key not in unique_sources:
                unique_sources[key] = s
        
        task["steps"][-1]["status"] = "done"
        task["progress"] = 100
        task["status"] = "completed"
        task["report"] = {
            "title": f"研究報告：{topic}",
            "content": report,
            "sources": list(unique_sources.values()),
            "findings_count": len(all_findings),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)
        task["steps"].append({"step": "❌ 發生錯誤", "status": "failed", "result": str(e)})


async def generate_sub_questions(client, topic: str) -> List[str]:
    """使用 LLM 生成子問題"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """你是一個研究助手。根據給定的主題，生成 3-5 個深入且具體的研究子問題。
這些問題應該：
1. 涵蓋主題的不同面向
2. 從基礎到進階
3. 包含實際應用或比較

只輸出問題列表，每行一個問題，不要編號。"""
            },
            {
                "role": "user",
                "content": f"研究主題：{topic}"
            }
        ],
        temperature=0.7
    )
    
    questions = response.choices[0].message.content.strip().split('\n')
    return [q.strip().lstrip('0123456789.-•) ') for q in questions if q.strip() and len(q.strip()) > 5]


async def search_for_research(query: str, documents: Optional[List[str]]) -> List[dict]:
    """執行向量搜尋"""
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    from openai import OpenAI
    import os
    
    client = QdrantClient(host="localhost", port=6333)
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # 生成查詢向量
    embedding_response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_vector = embedding_response.data[0].embedding
    
    # 建立過濾條件
    search_filter = None
    if documents and len(documents) > 0:
        search_filter = Filter(
            should=[
                FieldCondition(key="source", match=MatchValue(value=f))
                for f in documents
            ]
        )
    
    # 執行搜尋
    results = client.query_points(
        collection_name="documents",
        query=query_vector,
        query_filter=search_filter,
        limit=5,
        with_payload=True
    )
    
    return [
        {
            "content": point.payload.get("content", ""),
            "source": point.payload.get("source", ""),
            "page": point.payload.get("page", 1),
            "score": point.score
        }
        for point in results.points
    ]


async def generate_section_answer(client, question: str, sources: List[dict]) -> str:
    """生成單個問題的答案"""
    context = "\n\n".join([
        f"[來源: {s['source']}, 頁碼: {s['page']}]\n{s['content']}"
        for s in sources
    ])
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "根據提供的資料來源，回答問題。保持客觀、準確，並標註關鍵資訊的來源。"
            },
            {
                "role": "user",
                "content": f"問題：{question}\n\n參考資料：\n{context}"
            }
        ],
        temperature=0.3
    )
    
    return response.choices[0].message.content


async def generate_final_report(client, topic: str, findings: List[dict]) -> str:
    """生成最終研究報告"""
    findings_text = "\n\n---\n\n".join([
        f"### {f['question']}\n\n{f['answer']}"
        for f in findings
    ])
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """你是一個專業的研究報告撰寫者。
根據提供的研究發現，生成一份結構完整的研究報告。

報告格式（使用 Markdown）：
# 標題

## 📋 執行摘要
簡潔總結主要發現（3-5 句）

## 🔍 主要發現
列出 3-5 個關鍵發現

## 📖 詳細分析
整合所有研究發現，形成連貫的分析

## 💡 結論與建議
總結並提出建議

請確保報告專業、條理清晰，並適當引用來源。"""
            },
            {
                "role": "user",
                "content": f"研究主題：{topic}\n\n研究發現：\n{findings_text}"
            }
        ],
        temperature=0.4
    )
    
    return response.choices[0].message.content


@router.get("/research/{task_id}")
async def get_research_status(task_id: str):
    """取得研究任務狀態"""
    if task_id not in research_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return research_tasks[task_id]


@router.get("/research")
async def list_research_tasks():
    """列出所有研究任務"""
    return {
        "tasks": [
            {
                "task_id": tid,
                "status": t["status"],
                "progress": t["progress"],
                "created_at": t.get("created_at"),
                "title": t.get("report", {}).get("title", "進行中...")
            }
            for tid, t in research_tasks.items()
        ]
    }


# ============================================
# 3️⃣ Qdrant 管理 API
# ============================================

@router.get("/qdrant/collections")
async def list_collections():
    """列出所有 Qdrant collections"""
    from qdrant_client import QdrantClient
    
    client = QdrantClient(host="localhost", port=6333)
    
    try:
        collections = client.get_collections().collections
        result = []
        
        for c in collections:
            info = client.get_collection(c.name)
            result.append({
                "name": c.name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": str(info.status)
            })
        
        return {"collections": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/qdrant/collection/{name}")
async def get_collection_info(name: str):
    """取得 collection 詳細資訊"""
    from qdrant_client import QdrantClient
    
    client = QdrantClient(host="localhost", port=6333)
    
    try:
        info = client.get_collection(name)
        
        # 取得文件統計
        points, _ = client.scroll(
            collection_name=name,
            limit=10000,
            with_payload=["source"],
            with_vectors=False
        )
        
        # 統計每個文件的向量數
        doc_stats = {}
        for p in points:
            source = p.payload.get("source", "unknown")
            doc_stats[source] = doc_stats.get(source, 0) + 1
        
        return {
            "name": name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": str(info.status),
            "config": {
                "size": info.config.params.vectors.size if hasattr(info.config.params.vectors, 'size') else None,
                "distance": str(info.config.params.vectors.distance) if hasattr(info.config.params.vectors, 'distance') else None
            },
            "documents": [
                {"name": k, "vectors": v}
                for k, v in sorted(doc_stats.items(), key=lambda x: -x[1])
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/qdrant/collection/{name}/points")
async def browse_points(name: str, limit: int = 20, offset: Optional[str] = None):
    """瀏覽 collection 中的 points"""
    from qdrant_client import QdrantClient
    
    client = QdrantClient(host="localhost", port=6333)
    
    try:
        points, next_offset = client.scroll(
            collection_name=name,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        return {
            "points": [
                {
                    "id": str(p.id),
                    "payload": {
                        "source": p.payload.get("source", ""),
                        "page": p.payload.get("page", ""),
                        "content": p.payload.get("content", "")[:300] + "..." if len(p.payload.get("content", "")) > 300 else p.payload.get("content", "")
                    }
                }
                for p in points
            ],
            "next_offset": str(next_offset) if next_offset else None,
            "count": len(points)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/qdrant/collection/{name}")
async def delete_collection(name: str):
    """刪除 collection"""
    from qdrant_client import QdrantClient
    
    client = QdrantClient(host="localhost", port=6333)
    
    try:
        client.delete_collection(name)
        return {"message": f"Collection '{name}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 如何使用：在 main.py 中加入
# ============================================
"""
在 src/main.py 中加入以下代碼：

from routes_phase2 import router as phase2_router

app.include_router(phase2_router)
"""
