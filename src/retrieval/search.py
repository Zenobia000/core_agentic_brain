import os
import sys
import logging
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv

# 路徑修正
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

import qdrant_client
from llama_index.embeddings.openai import OpenAIEmbedding

load_dotenv()
logger = logging.getLogger(__name__)

class HybridRetriever:
    def __init__(self, collection_name: str = "rag_knowledge_base"):
        self.client = qdrant_client.QdrantClient(url=os.getenv("QDRANT_URL"))
        self.collection_name = collection_name
        self.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    
    def search(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """
        執行雙路召回：同時搜尋 NQ1D (問題向量) 與 Content (內容向量)
        """
        logger.info(f"🔍 搜尋: {query_text}")
        
        # 1. 將使用者問題向量化
        query_vec = self.embed_model.get_text_embedding(query_text)

        # 2. 路徑 A: 針對 "question" 向量搜尋 (NQ1D match)
        results_q = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vec,
            using="question", # 指定使用 question 向量
            limit=top_k,
            with_payload=True
        ).points

        # 3. 路徑 B: 針對 "content" 向量搜尋 (Raw Text match)
        results_c = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vec,
            using="content",  # 指定使用 content 向量
            limit=top_k,
            with_payload=True
        ).points

        # 4. 合併結果並去重 (Simple Fusion)
        combined_results = {}
        
        # 處理 NQ1D 結果
        for point in results_q:
            point.payload["match_type"] = "NQ1D (精準)"
            combined_results[point.id] = point

        # 處理 Content 結果
        for point in results_c:
            if point.id not in combined_results:
                point.payload["match_type"] = "Content (廣泛)"
                combined_results[point.id] = point
            else:
                combined_results[point.id].payload["match_type"] = "Dual Match (強相關)"

        # 轉回列表並按分數排序
        final_list = list(combined_results.values())
        final_list.sort(key=lambda x: x.score, reverse=True)

        return final_list[:top_k]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    retriever = HybridRetriever()
    test_query = "CLIP 模型是如何訓練的？" 
    results = retriever.search(test_query, top_k=3)
    
    print("\n" + "="*50)
    print(f"🚀 針對問題 '{test_query}' 的檢索結果 (Warning Free 版)：")
    print("="*50)
    
    for i, hit in enumerate(results):
        payload = hit.payload
        print(f"\n[{i+1}] Score: {hit.score:.4f} | Type: {payload.get('match_type')}")
        print(f"📄 來源: {payload.get('file_name')} (Page {payload.get('page_label')})")
        print(f"📝 摘要: {payload.get('summary')}")
        print("-" * 30)