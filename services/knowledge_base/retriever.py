"""
Retriever - 使用 Cohere Embedding 查詢 Qdrant
支援 Cohere 和 OpenAI 雙 provider
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from dotenv import load_dotenv

# 載入環境變數
_project_root = Path(__file__).resolve().parent.parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)

logger = logging.getLogger(__name__)

# 全域實例
_retriever_instance = None


class Retriever:
    """
    向量檢索器 - 支援 Cohere 和 OpenAI embedding
    
    重要：Cohere 查詢時必須使用 input_type="search_query"
    """
    
    def __init__(
        self,
        collection_name: str = "rag_knowledge_base",
        qdrant_url: str = "http://localhost:6333"
    ):
        self.collection_name = collection_name
        self.qdrant_url = qdrant_url
        
        # API clients
        self.cohere_client = None
        self.openai_client = None
        self.qdrant_client = None
        
        # Embedding 設定
        self.embed_provider = None
        self.embed_model = None
        
        self._initialize()
    
    def _initialize(self):
        """初始化 clients"""
        # 確保環境變數已載入
        load_dotenv(_env_path, override=True)
        
        cohere_key = os.getenv("COHERE_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        # 優先使用 Cohere
        if cohere_key:
            try:
                import cohere
                self.cohere_client = cohere.Client(api_key=cohere_key)
                self.embed_provider = "cohere"
                self.embed_model = os.getenv("COHERE_EMBED_MODEL", "embed-multilingual-v3.0")
                logger.info(f"✅ [Retriever] 使用 Cohere embedding: {self.embed_model}")
            except ImportError:
                logger.warning("⚠️ [Retriever] cohere 套件未安裝")
            except Exception as e:
                logger.error(f"❌ [Retriever] Cohere 初始化失敗: {e}")
        
        # 備用：OpenAI
        if not self.cohere_client and openai_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=openai_key)
                self.embed_provider = "openai"
                self.embed_model = "text-embedding-3-small"
                logger.info(f"✅ [Retriever] 使用 OpenAI embedding: {self.embed_model}")
            except ImportError:
                logger.warning("⚠️ [Retriever] openai 套件未安裝")
            except Exception as e:
                logger.error(f"❌ [Retriever] OpenAI 初始化失敗: {e}")
        
        if not self.cohere_client and not self.openai_client:
            logger.error("❌ [Retriever] 沒有可用的 embedding provider！")
            raise ValueError("需要設定 COHERE_API_KEY 或 OPENAI_API_KEY")
        
        # 初始化 Qdrant
        self._init_qdrant()
    
    def _init_qdrant(self):
        """初始化 Qdrant client"""
        try:
            from qdrant_client import QdrantClient
            self.qdrant_client = QdrantClient(url=self.qdrant_url)
            logger.info(f"✅ [Retriever] Qdrant 連接成功: {self.qdrant_url}")
        except Exception as e:
            logger.error(f"❌ [Retriever] Qdrant 初始化失敗: {e}")
            raise
    
    def get_query_embedding(self, query: str) -> List[float]:
        """
        取得查詢的 embedding 向量
        
        重要：Cohere 必須使用 input_type="search_query"
        """
        if self.cohere_client:
            return self._get_cohere_embedding(query)
        else:
            return self._get_openai_embedding(query)
    
    def _get_cohere_embedding(self, text: str) -> List[float]:
        """使用 Cohere 取得查詢 embedding"""
        try:
            response = self.cohere_client.embed(
                texts=[text],
                model=self.embed_model,
                input_type="search_query"  # 重要！查詢時使用 search_query
            )
            return response.embeddings[0]
        except Exception as e:
            logger.error(f"❌ [Retriever] Cohere embedding 失敗: {e}")
            raise
    
    def _get_openai_embedding(self, text: str) -> List[float]:
        """使用 OpenAI 取得 embedding"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embed_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"❌ [Retriever] OpenAI embedding 失敗: {e}")
            raise
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        語意搜尋
        
        Args:
            query: 搜尋查詢
            top_k: 返回結果數量
            filters: 過濾條件，如 {"file_name": ["doc1.pdf", "doc2.pdf"]}
            
        Returns:
            搜尋結果列表
        """
        logger.info(f"🔍 [Retriever] ====== 開始搜尋 ======")
        logger.info(f"🔍 [Retriever] Query: {query[:50]}...")
        logger.info(f"🔍 [Retriever] Top-K: {top_k}")
        logger.info(f"🔍 [Retriever] Filters: {filters}")
        
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        try:
            # 取得查詢向量
            query_vector = self.get_query_embedding(query)
            logger.info(f"✅ [Retriever] Query embedding 完成 (dim: {len(query_vector)})")
            
            # 建構過濾條件
            search_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        # 多值篩選 (OR)
                        conditions.append(Filter(should=[
                            FieldCondition(key=key, match=MatchValue(value=v))
                            for v in value
                        ]))
                    else:
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
                if conditions:
                    search_filter = Filter(must=conditions)
                    logger.info(f"📋 [Retriever] 過濾條件已建構: {len(conditions)} 個條件")
            
            # 執行搜尋
            results = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=search_filter,
                limit=top_k,
                with_payload=True
            )
            
            logger.info(f"✅ [Retriever] 找到 {len(results.points)} 個結果")
            
            # 詳細記錄結果
            for i, point in enumerate(results.points):
                file_name = point.payload.get("file_name", "unknown")
                text_preview = point.payload.get("text", "")[:50]
                logger.info(f"  [{i+1}] score={point.score:.4f}, file={file_name}")
                logger.debug(f"      text: {text_preview}...")
            
            # 轉換為標準格式
            return [
                {
                    "text": p.payload.get("text", ""),
                    "file_name": p.payload.get("file_name", "unknown"),
                    "page_label": p.payload.get("page_label", "?"),
                    "score": p.score,
                    "metadata": p.payload
                }
                for p in results.points
            ]
            
        except Exception as e:
            logger.error(f"❌ [Retriever] 搜尋失敗: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def search_multiple(
        self,
        queries: List[str],
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        多查詢搜尋
        
        Args:
            queries: 多個查詢
            top_k: 每個查詢返回的結果數量
            filters: 過濾條件
            
        Returns:
            合併的搜尋結果
        """
        logger.info(f"🔍 [Retriever] 多查詢搜尋: {len(queries)} 個查詢")
        
        all_results = []
        seen_texts = set()  # 用於去重
        
        for query in queries:
            results = self.search(query, top_k=top_k, filters=filters)
            
            for r in results:
                # 使用文本的前 100 字符作為去重鍵
                text_key = r["text"][:100] if r["text"] else ""
                if text_key and text_key not in seen_texts:
                    seen_texts.add(text_key)
                    all_results.append(r)
        
        # 按 score 排序
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"✅ [Retriever] 多查詢搜尋完成: {len(all_results)} 個不重複結果")
        
        return {
            "queries": queries,
            "results": all_results,
            "total": len(all_results)
        }


def get_retriever() -> Retriever:
    """取得全域 Retriever 實例"""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = Retriever()
    return _retriever_instance


def reset_retriever():
    """重置全域 Retriever 實例"""
    global _retriever_instance
    _retriever_instance = None
