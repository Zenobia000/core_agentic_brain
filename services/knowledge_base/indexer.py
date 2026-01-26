"""
Indexer - 使用 Cohere Embedding 索引文件到 Qdrant
支援 Cohere 和 OpenAI 雙 provider
"""

import os
import logging
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

from dotenv import load_dotenv

# 載入環境變數
_project_root = Path(__file__).resolve().parent.parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)

logger = logging.getLogger(__name__)

# 全域實例
_indexer_instance = None


class Indexer:
    """
    文件索引器 - 支援 Cohere 和 OpenAI embedding
    
    Cohere 優勢：
    1. 多語言支援 (embed-multilingual-v3.0)
    2. 區分 document 和 query embedding (input_type)
    3. 較低成本
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
        self.embed_dim = None
        
        self._initialize()
    
    def _initialize(self):
        """初始化 clients 和設定"""
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
                self.embed_dim = 1024  # Cohere v3 模型固定 1024 維
                logger.info(f"✅ [Indexer] 使用 Cohere embedding: {self.embed_model}")
            except ImportError:
                logger.warning("⚠️ [Indexer] cohere 套件未安裝")
            except Exception as e:
                logger.error(f"❌ [Indexer] Cohere 初始化失敗: {e}")
        
        # 備用：OpenAI
        if not self.cohere_client and openai_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=openai_key)
                self.embed_provider = "openai"
                self.embed_model = "text-embedding-3-small"
                self.embed_dim = 1536
                logger.info(f"✅ [Indexer] 使用 OpenAI embedding: {self.embed_model}")
            except ImportError:
                logger.warning("⚠️ [Indexer] openai 套件未安裝")
            except Exception as e:
                logger.error(f"❌ [Indexer] OpenAI 初始化失敗: {e}")
        
        if not self.cohere_client and not self.openai_client:
            logger.error("❌ [Indexer] 沒有可用的 embedding provider！")
            logger.error("   請設定 COHERE_API_KEY 或 OPENAI_API_KEY")
            raise ValueError("需要設定 COHERE_API_KEY 或 OPENAI_API_KEY")
        
        # 初始化 Qdrant
        self._init_qdrant()
    
    def _init_qdrant(self):
        """初始化 Qdrant client 和 collection"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            self.qdrant_client = QdrantClient(url=self.qdrant_url)
            
            # 檢查 collection 是否存在
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # 創建新 collection
                logger.info(f"📦 [Indexer] 創建新 collection: {self.collection_name}")
                logger.info(f"📦 [Indexer] 向量維度: {self.embed_dim}")
                
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embed_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ [Indexer] Collection 創建成功")
            else:
                # 檢查維度是否匹配
                collection_info = self.qdrant_client.get_collection(self.collection_name)
                existing_dim = collection_info.config.params.vectors.size
                
                if existing_dim != self.embed_dim:
                    logger.warning(f"⚠️ [Indexer] 維度不匹配！")
                    logger.warning(f"   Collection 維度: {existing_dim}")
                    logger.warning(f"   當前 provider 維度: {self.embed_dim}")
                    logger.warning(f"   請重置 collection 或切換 embedding provider")
                else:
                    logger.info(f"✅ [Indexer] Collection 已存在，維度匹配: {existing_dim}")
                    
        except Exception as e:
            logger.error(f"❌ [Indexer] Qdrant 初始化失敗: {e}")
            raise
    
    def get_embedding(self, text: str, input_type: str = "search_document") -> List[float]:
        """
        取得文字的 embedding 向量
        
        Args:
            text: 輸入文字
            input_type: Cohere 專用
                - "search_document": 索引文件時使用
                - "search_query": 查詢時使用
                
        Returns:
            embedding 向量
        """
        if self.cohere_client:
            return self._get_cohere_embedding(text, input_type)
        else:
            return self._get_openai_embedding(text)
    
    def _get_cohere_embedding(self, text: str, input_type: str) -> List[float]:
        """使用 Cohere 取得 embedding"""
        try:
            response = self.cohere_client.embed(
                texts=[text],
                model=self.embed_model,
                input_type=input_type  # 重要！區分 document 和 query
            )
            return response.embeddings[0]
        except Exception as e:
            logger.error(f"❌ [Indexer] Cohere embedding 失敗: {e}")
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
            logger.error(f"❌ [Indexer] OpenAI embedding 失敗: {e}")
            raise
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        索引文件到 Qdrant
        
        Args:
            documents: 文件列表，每個包含 text 和 metadata
            
        Returns:
            成功索引的數量
        """
        if not documents:
            logger.warning("⚠️ [Indexer] 沒有文件需要索引")
            return 0
        
        from qdrant_client.models import PointStruct
        
        logger.info(f"💾 [Indexer] ====== 開始索引 ======")
        logger.info(f"💾 [Indexer] 文件數量: {len(documents)}")
        logger.info(f"💾 [Indexer] Provider: {self.embed_provider}")
        
        points = []
        success_count = 0
        
        for i, doc in enumerate(documents):
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            
            if not text.strip():
                continue
            
            try:
                # 索引文件時使用 search_document
                vector = self.get_embedding(text, input_type="search_document")
                
                payload = {
                    "text": text,
                    **metadata
                }
                
                points.append(PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=payload
                ))
                
                success_count += 1
                
                # 每 10 個文件記錄一次進度
                if (i + 1) % 10 == 0:
                    logger.info(f"💾 [Indexer] 進度: {i + 1}/{len(documents)}")
                
            except Exception as e:
                logger.error(f"❌ [Indexer] 第 {i + 1} 個文件 embedding 失敗: {e}")
        
        # 批次寫入 Qdrant
        if points:
            try:
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                logger.info(f"✅ [Indexer] 成功索引 {success_count} 個文件")
            except Exception as e:
                logger.error(f"❌ [Indexer] Qdrant 寫入失敗: {e}")
                raise
        
        return success_count
    
    def delete_by_filename(self, file_name: str) -> int:
        """
        刪除指定檔案的所有向量
        
        Args:
            file_name: 檔案名稱
            
        Returns:
            刪除的向量數量
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        try:
            # 先計算要刪除多少
            count_result = self.qdrant_client.count(
                collection_name=self.collection_name,
                count_filter=Filter(
                    must=[FieldCondition(key="file_name", match=MatchValue(value=file_name))]
                )
            )
            count = count_result.count
            
            if count > 0:
                # 執行刪除
                self.qdrant_client.delete(
                    collection_name=self.collection_name,
                    points_selector=Filter(
                        must=[FieldCondition(key="file_name", match=MatchValue(value=file_name))]
                    )
                )
                logger.info(f"🗑️ [Indexer] 已刪除 {count} 個向量 (file: {file_name})")
            
            return count
            
        except Exception as e:
            logger.error(f"❌ [Indexer] 刪除失敗: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """取得索引統計"""
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            return {
                "collection": self.collection_name,
                "points_count": collection_info.points_count,
                "status": str(collection_info.status),
                "embed_provider": self.embed_provider,
                "embed_model": self.embed_model,
                "embed_dim": self.embed_dim
            }
        except Exception as e:
            logger.error(f"❌ [Indexer] 取得統計失敗: {e}")
            return {"error": str(e)}


def get_indexer() -> Indexer:
    """取得全域 Indexer 實例"""
    global _indexer_instance
    if _indexer_instance is None:
        _indexer_instance = Indexer()
    return _indexer_instance


def reset_indexer():
    """重置全域 Indexer 實例"""
    global _indexer_instance
    _indexer_instance = None
