import os
import logging
from typing import List
from qdrant_client import QdrantClient
from llama_index.embeddings.openai import OpenAIEmbedding

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# [關鍵一致性 1] 必須跟 indexer.py 的名稱一模一樣
COLLECTION_NAME = "rag_knowledge_base"

class HybridRetriever:
    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        # 1. 初始化 Qdrant 客戶端
        self.client = QdrantClient(url=self.qdrant_url)
        
        # [關鍵一致性 2] 必須跟 indexer.py 使用同一顆模型
        # 如果寫入用 text-embedding-3-small，讀取也要用這顆，不然向量空間會對不準
        self.embed_model = OpenAIEmbedding(
            model="text-embedding-3-small",
            api_key=self.api_key
        )

    def search(self, query_text: str, top_k: int = 5):
        """
        執行向量搜尋
        """
        logger.info(f"🔍 搜尋: {query_text}")

        try:
            # 1. 將使用者的問題轉成向量
            query_vector = self.embed_model.get_query_embedding(query_text)

            # 2. 去 Qdrant 搜尋
            search_result = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True # 記得把原本的文字 (payload) 抓回來
            )

            if not search_result:
                logger.warning("⚠️ 找不到相關資料")
                return []

            logger.info(f"✅ 找到 {len(search_result)} 筆相關資料")
            return search_result

        except Exception as e:
            logger.error(f"❌ 搜尋失敗: {e}")
            return []