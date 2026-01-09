import os
import sys
import logging
import uuid
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# 設定路徑
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

import qdrant_client
from qdrant_client import models
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from src.ingestion.schema import ProcessedChunk

load_dotenv()
logger = logging.getLogger(__name__)

class VectorIndexer:
    def __init__(self, collection_name: str = "rag_knowledge_base"):
        self.collection_name = collection_name
        self.client = qdrant_client.QdrantClient(url=os.getenv("QDRANT_URL"))
        
        # 使用 OpenAI Embedding 模型 (對應 Roadmap Source 6)
        # text-embedding-3-small 性價比高，適合 MVP
        self.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
        
        # 初始化 Collection
        self._init_collection()

    def _init_collection(self):
        """檢查並建立 Qdrant Collection，設定 Named Vectors"""
        if not self.client.collection_exists(self.collection_name):
            logger.info(f"🔨 正在建立向量集合: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    # 1. 內容向量 (Content Vector)
                    "content": models.VectorParams(size=1536, distance=models.Distance.COSINE),
                    # 2. 問題向量 (Question Vector) - 這是 NQ1D 的關鍵
                    "question": models.VectorParams(size=1536, distance=models.Distance.COSINE),
                }
            )
        else:
            logger.info(f"✅ 向量集合已存在: {self.collection_name}")

    def index(self, chunks: List[ProcessedChunk]):
        """
        將處理好的 Chunks 向量化並寫入 Qdrant
        """
        points = []
        logger.info(f"⚡ 正在為 {len(chunks)} 筆資料生成向量...")

        for chunk in chunks:
            try:
                # 1. 生成 Content Vector (針對原始文本)
                vec_content = self.embed_model.get_text_embedding(chunk.text)
                
                # 2. 生成 Question Vector (針對 NQ1D) 
                # 取第一個 canonical_q 作為主要索引
                if chunk.semantic_data.nq1d:
                    q_text = chunk.semantic_data.nq1d[0].canonical_q
                    vec_question = self.embed_model.get_text_embedding(q_text)
                else:
                    # 如果沒有問題，就用 content 補位 (避免報錯)
                    vec_question = vec_content

                # 3. 準備 Payload (Metadata) 
                payload = {
                    "file_name": chunk.file_name,
                    "page_label": chunk.page_label,
                    "text": chunk.text,
                    "summary": chunk.semantic_data.summary,
                    "what": chunk.semantic_data.what,
                    "why": chunk.semantic_data.why,
                    "how": json.dumps(chunk.semantic_data.how, ensure_ascii=False), # 轉字串存
                    "canonical_q": chunk.semantic_data.nq1d[0].canonical_q if chunk.semantic_data.nq1d else "",
                    "keywords": chunk.semantic_data.keywords
                }

                # 4. 建立 Qdrant Point
                points.append(models.PointStruct(
                    id=str(uuid.uuid4()), # 隨機生成 ID
                    vector={
                        "content": vec_content,
                        "question": vec_question
                    },
                    payload=payload
                ))
            except Exception as e:
                logger.error(f"❌ 向量化失敗 Chunk {chunk.chunk_id}: {e}")

        # 5. 批次寫入
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"✅ 成功寫入 {len(points)} 筆資料到 Qdrant！")
        else:
            logger.warning("⚠️ 沒有資料被寫入。")

# 單元測試
if __name__ == "__main__":
    import json
    # 模擬一個 ProcessedChunk 來測試 (不用每次都跑 LLM 燒錢)
    from src.ingestion.schema import SemanticExtraction, NQ1DItem
    
    logging.basicConfig(level=logging.INFO)

    # 造假資料
    mock_data = SemanticExtraction(
        summary="測試摘要",
        what="測試定義",
        why="測試原因",
        how=["步驟1", "步驟2"],
        nq1d=[NQ1DItem(canonical_q="這是測試問題嗎？", intent="test")],
        keywords=["test", "mock"]
    )
    
    mock_chunk = ProcessedChunk(
        chunk_id="test_001",
        file_name="test_doc.pdf",
        page_label="1",
        text="這是一段測試文字，用於驗證向量寫入是否成功。",
        semantic_data=mock_data
    )

    indexer = VectorIndexer()
    indexer.index([mock_chunk])