"""
Phase 2 後端路由擴展 - 修復版
Collection: rag_knowledge_base
Payload: text, file_name, page_label
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
import os
import time
from datetime import datetime

router = APIRouter()

# ========== 配置 ==========
COLLECTION_NAME = "rag_knowledge_base"
PDF_DIR = "data/raw"

# ============================================
# 1️⃣ 多 PDF 選擇器 API
# ============================================

@router.get("/documents")
async def list_documents():
    """列出所有已上傳的 PDF 文件"""
    from qdrant_client import QdrantClient
    
    documents = []
    
    try:
        client = QdrantClient(host="localhost", port=6333)
        has_qdrant = True
    except:
        has_qdrant = False
    
    if os.path.exists(PDF_DIR):
        for filename in os.listdir(PDF_DIR):
            if filename.lower().endswith('.pdf'):
                filepath = os.path.join(PDF_DIR, filename)
                
                indexed = False
                vector_count = 0
                
                if has_qdrant:
                    try:
                        # 使用正確的 payload 字段名 file_name
                        results, _ = client.scroll(
                            collection_name=COLLECTION_NAME,
                            scroll_filter={
                                "must": [
                                    {"key": "file_name", "match": {"value": filename}}
                                ]
                            },
                            limit=1,
                            with_payload=False,
                            with_vectors=False
                        )
                        indexed = len(results) > 0
                        
                        if indexed:
                            all_points, _ = client.scroll(
                                collection_name=COLLECTION_NAME,
                                scroll_filter={
                                    "must": [
                                        {"key": "file_name", "match": {"value": filename}}
                                    ]
                                },
                                limit=10000,
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
    
    documents.sort(key=lambda x: x["modified"], reverse=True)
    
    return {"documents": documents, "total": len(documents)}


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """刪除 PDF 文件及其向量索引"""
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    
    filepath = f"{PDF_DIR}/{filename}"
    file_deleted = False
    if os.path.exists(filepath):
        os.remove(filepath)
        file_deleted = True
    
    vectors_deleted = 0
    try:
        client = QdrantClient(host="localhost", port=6333)
        
        points, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[FieldCondition(key="file_name", match=MatchValue(value=filename))]
            ),
            limit=10000,
            with_payload=False
        )
        vectors_deleted = len(points)
        
        if vectors_deleted > 0:
            point_ids = [p.id for p in points]
            client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=point_ids
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
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    from openai import OpenAI
    
    client = QdrantClient(host="localhost", port=6333)
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    embedding_response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=request.query
    )
    query_vector = embedding_response.data[0].embedding
    
    search_filter = None
    if request.filenames and len(request.filenames) > 0:
        if len(request.filenames) == 1:
            search_filter = Filter(
                must=[FieldCondition(key="file_name", match=MatchValue(value=request.filenames[0]))]
            )
        else:
            search_filter = Filter(
                should=[
                    FieldCondition(key="file_name", match=MatchValue(value=f))
                    for f in request.filenames
                ]
            )
    
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=search_filter,
        limit=request.top_k,
        with_payload=True
    )
    
    return {
        "results": [
            {
                "content": point.payload.get("text", ""),
                "source": point.payload.get("file_name", ""),
                "page": point.payload.get("page_label", "1"),
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
    """執行深度研究"""
    from openai import OpenAI
    
    task = research_tasks[task_id]
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        task["steps"].append({"step": "🔍 分析研究主題", "status": "running"})
        task["progress"] = 5
        
        sub_questions = await generate_sub_questions(openai_client, topic)
        
        task["steps"][-1]["status"] = "done"
        task["steps"][-1]["result"] = f"生成 {len(sub_questions)} 個子問題"
        task["progress"] = 15
        
        all_findings = []
        all_sources = []
        
        for i, question in enumerate(sub_questions):
            task["steps"].append({
                "step": f"📚 研究: {question[:40]}...",
                "status": "running"
            })
            
            search_results = await search_for_research(question, documents)
            
            if search_results:
                all_sources.extend(search_results)
                answer = await generate_section_answer(openai_client, question, search_results)
                
                all_findings.append({
                    "question": question,
                    "answer": answer,
                    "sources": search_results
                })
            
            task["steps"][-1]["status"] = "done"
            task["steps"][-1]["result"] = f"找到 {len(search_results)} 個相關段落"
            task["progress"] = 15 + (i + 1) * (65 / len(sub_questions))
        
        task["steps"].append({"step": "📝 撰寫研究報告", "status": "running"})
        task["progress"] = 85
        
        report = await generate_final_report(openai_client, topic, all_findings)
        
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
    """生成子問題"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """你是一個研究助手。根據給定的主題，生成 3-5 個深入且具體的研究子問題。
這些問題應該涵蓋主題的不同面向。只輸出問題列表，每行一個問題，不要編號。"""
            },
            {"role": "user", "content": f"研究主題：{topic}"}
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
    
    client = QdrantClient(host="localhost", port=6333)
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    embedding_response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_vector = embedding_response.data[0].embedding
    
    search_filter = None
    if documents and len(documents) > 0:
        search_filter = Filter(
            should=[
                FieldCondition(key="file_name", match=MatchValue(value=f))
                for f in documents
            ]
        )
    
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=search_filter,
        limit=5,
        with_payload=True
    )
    
    return [
        {
            "content": point.payload.get("text", ""),
            "source": point.payload.get("file_name", ""),
            "page": point.payload.get("page_label", "1"),
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
            {"role": "user", "content": f"問題：{question}\n\n參考資料：\n{context}"}
        ],
        temperature=0.3
    )
    
    return response.choices[0].message.content


async def generate_final_report(client, topic: str, findings: List[dict]) -> str:
    """生成最終報告"""
    findings_text = "\n\n---\n\n".join([
        f"### {f['question']}\n\n{f['answer']}"
        for f in findings
    ])
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """你是一個專業的研究報告撰寫者。根據提供的研究發現，生成一份結構完整的研究報告。

報告格式（使用 Markdown）：
# 標題

## 📋 執行摘要
簡潔總結主要發現（3-5 句）

## 🔍 主要發現
列出 3-5 個關鍵發現

## 📖 詳細分析
整合所有研究發現，形成連貫的分析

## 💡 結論與建議
總結並提出建議"""
            },
            {"role": "user", "content": f"研究主題：{topic}\n\n研究發現：\n{findings_text}"}
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
        
        points, _ = client.scroll(
            collection_name=name,
            limit=10000,
            with_payload=["file_name"],
            with_vectors=False
        )
        
        doc_stats = {}
        for p in points:
            # 使用正確的字段名 file_name
            source = p.payload.get("file_name", "unknown")
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
                        # 使用正確的字段名
                        "source": p.payload.get("file_name", ""),
                        "page": p.payload.get("page_label", ""),
                        "content": p.payload.get("text", "")[:300] + "..." if len(p.payload.get("text", "")) > 300 else p.payload.get("text", "")
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
