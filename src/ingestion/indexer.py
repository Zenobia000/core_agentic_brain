import os
import logging
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI

# 設定 Log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Indexer:
    def __init__(self):
        # 初始化 Qdrant
        self.client = QdrantClient(url="http://localhost:6333")
        self.collection_name = "rag_knowledge_base"
        
        # 初始化 OpenAI (用於生成 Embedding)
        api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = OpenAI(api_key=api_key)

        # 確保集合存在 (使用最簡單的設定，避免 Vector Name Mismatch)
        self._ensure_collection()

    def _ensure_collection(self):
        """如果集合不存在，則建立新的 (使用預設無名向量)"""
        try:
            self.client.get_collection(self.collection_name)
        except:
            logger.info(f"🔧 建立新的 Qdrant 集合: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1536,  # text-embedding-3-small
                    distance=models.Distance.COSINE
                )
            )

    def get_embedding(self, text: str):
        text = text.replace("\n", " ")
        response = self.openai_client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    def index_documents(self, documents: list):
        """將文件列表寫入 Qdrant"""
        if not documents:
            return

        logger.info(f"💾 [Indexer] 正在將 {len(documents)} 筆資料寫入 Qdrant...")
        
        points = []
        for doc in documents:
            text = doc.get("text", "")
            if not text.strip():
                continue
                
            try:
                # 生成向量
                vector = self.get_embedding(text)
                
                # 準備 Payload
                payload = {
                    "text": text,
                    "file_name": doc.get("metadata", {}).get("file_name", "unknown"),
                    "page_label": doc.get("metadata", {}).get("page_label", "unknown")
                }

                points.append(models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector, 
                    payload=payload
                ))
            except Exception as e:
                logger.error(f"❌ 向量化失敗 (跳過): {e}")

        # 批次寫入
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"✅ [Indexer] 寫入成功！")