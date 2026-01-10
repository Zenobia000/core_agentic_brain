import logging
import os
from qdrant_client import QdrantClient
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridRetriever:
    def __init__(self):
        # 回到最簡單的初始化
        self.client = QdrantClient(url="http://localhost:6333")
        self.collection_name = "rag_knowledge_base"
        
        api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = OpenAI(api_key=api_key)

    def get_embedding(self, text: str):
        text = text.replace("\n", " ")
        response = self.openai_client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    def search(self, query_text: str, top_k: int = 3):
        logger.info(f"🔍 搜尋: {query_text}")
        
        try:
            # 1. 取得向量
            query_vector = self.get_embedding(query_text)

            # 2. 執行搜尋 (最原始、最簡單的寫法，絕對相容 Phase 4 的資料)
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k
            ).points
            
            logger.info(f"✅ 找到 {len(search_result)} 筆相關資料")
            return search_result

        except Exception as e:
            logger.error(f"❌ 搜尋失敗: {e}")
            return []