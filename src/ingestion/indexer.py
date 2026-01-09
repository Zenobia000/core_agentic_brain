import os
import logging
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.http import models
from llama_index.core.schema import BaseNode
from llama_index.embeddings.openai import OpenAIEmbedding

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 設定 Collection 名稱
COLLECTION_NAME = "rag_knowledge_base"

async def index_nodes(nodes: List[BaseNode]):
    """
    將處理好的節點 (含 NQ1D 問題) 寫入 Qdrant 向量資料庫。
    包含：
    1. 生成向量 (Content Vector)
    2. 建立 Collection (如果不存在)
    3. 批次寫入 (Upsert)
    """
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key = os.getenv("OPENAI_API_KEY")

    if not nodes:
        logger.warning("⚠️ 沒有節點需要索引")
        return 0

    # 1. 初始化客戶端
    client = QdrantClient(url=qdrant_url)
    
    # 初始化 Embedding 模型 (用來把文字變成向量)
    # 這裡我們使用 OpenAI text-embedding-3-small (CP 值最高)
    embed_model = OpenAIEmbedding(
        model="text_embedding_3_small", 
        api_key=api_key
    )

    # 2. 檢查並建立 Collection
    if not client.collection_exists(collection_name=COLLECTION_NAME):
        logger.info(f"🆕 Collection 不存在，正在建立: {COLLECTION_NAME}...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=1536,  # text-embedding-3-small 的維度
                distance=models.Distance.COSINE
            )
        )
    else:
        logger.info(f"✅ 向量集合已存在: {COLLECTION_NAME}")

    # 3. 生成向量 (Batch Embedding)
    logger.info(f"⚡ 正在為 {len(nodes)} 筆資料生成向量...")
    
    points = []
    for node in nodes:
        # 準備要向量化的文字
        # 策略：我們主要對「內文」做向量化。
        # (進階策略：也可以把生成的 NQ1D 問題加進來一起算，這裡我們先單純一點算內文)
        text_to_embed = node.text 
        
        try:
            # 呼叫 OpenAI 生成向量
            vector = embed_model.get_text_embedding(text_to_embed)
            
            # 整理 Payload (要存進資料庫的欄位)
            # 這裡我們把生成的 "questions" 也存進去，方便之後做關鍵字搜尋
            payload = {
                "text": node.text,
                "file_name": node.metadata.get("file_name", "unknown"),
                "page_label": node.metadata.get("page_label", "unknown"),
                "questions": node.metadata.get("questions", []), # NQ1D 問題
                "processed_by": node.metadata.get("processed_by", "unknown")
            }

            # 建立 Qdrant Point
            point = models.PointStruct(
                id=node.node_id, # 使用 LlamaIndex 生成的 UUID
                vector=vector,
                payload=payload
            )
            points.append(point)
            
        except Exception as e:
            logger.error(f"❌ 向量化失敗 (Node ID: {node.node_id}): {e}")

    # 4. 寫入資料庫 (Upsert)
    if points:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        logger.info(f"✅ 成功寫入 {len(points)} 筆資料到 Qdrant！")
        return len(points)
    else:
        logger.warning("⚠️ 沒有資料被寫入")
        return 0