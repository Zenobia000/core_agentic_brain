"""
Long-term Memory - 長期記憶 (RAG)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Document(BaseModel):
    """文件模型"""
    doc_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    source: Optional[str] = None
    source_type: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class RetrievalResult(BaseModel):
    """檢索結果"""
    document: Document
    score: float
    highlights: List[str] = Field(default_factory=list)


class VectorStoreBase(ABC):
    """向量存儲抽象基類"""
    
    @abstractmethod
    async def add_documents(self, documents: List[Document]) -> List[str]:
        pass
    
    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        pass
    
    @abstractmethod
    async def delete(self, doc_ids: List[str]) -> bool:
        pass


class QdrantVectorStore(VectorStoreBase):
    """Qdrant 向量存儲"""
    
    def __init__(self, host: str = "localhost", port: int = 6333, collection_name: str = "long_term_memory"):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self._client = None
    
    async def _ensure_client(self):
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.models import Distance, VectorParams
                self._client = QdrantClient(host=self.host, port=self.port)
                
                collections = self._client.get_collections().collections
                if self.collection_name not in [c.name for c in collections]:
                    self._client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                    )
            except ImportError:
                raise ImportError("pip install qdrant-client")
    
    async def _get_embedding(self, text: str) -> List[float]:
        try:
            from openai import OpenAI
            import os
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.embeddings.create(model="text-embedding-3-small", input=text)
            return response.data[0].embedding
        except ImportError:
            raise ImportError("pip install openai")
    
    async def add_documents(self, documents: List[Document]) -> List[str]:
        await self._ensure_client()
        from qdrant_client.models import PointStruct
        
        points = []
        for doc in documents:
            if doc.embedding is None:
                doc.embedding = await self._get_embedding(doc.content)
            points.append(PointStruct(
                id=hash(doc.doc_id) % (2**63),
                vector=doc.embedding,
                payload={"doc_id": doc.doc_id, "content": doc.content, "source": doc.source}
            ))
        
        self._client.upsert(collection_name=self.collection_name, points=points)
        return [doc.doc_id for doc in documents]
    
    async def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        await self._ensure_client()
        query_embedding = await self._get_embedding(query)
        results = self._client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k
        )
        
        return [
            RetrievalResult(
                document=Document(doc_id=hit.payload.get("doc_id", ""), content=hit.payload.get("content", "")),
                score=hit.score
            )
            for hit in results
        ]
    
    async def delete(self, doc_ids: List[str]) -> bool:
        await self._ensure_client()
        # Implementation would use filters
        return True


class LongTermMemory(BaseModel):
    """長期記憶管理器"""
    
    vector_store: Optional[Any] = None
    host: str = "localhost"
    port: int = 6333
    collection_name: str = "long_term_memory"
    
    class Config:
        arbitrary_types_allowed = True
    
    async def initialize(self) -> None:
        self.vector_store = QdrantVectorStore(self.host, self.port, self.collection_name)
    
    async def store(self, content: str, source: Optional[str] = None) -> str:
        if self.vector_store is None:
            await self.initialize()
        
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        doc = Document(doc_id=doc_id, content=content, source=source)
        await self.vector_store.add_documents([doc])
        return doc_id
    
    async def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        if self.vector_store is None:
            await self.initialize()
        return await self.vector_store.search(query, top_k)
