import os
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, Document
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client

# 1. Load Environment
load_dotenv()
print("✅ 環境變數載入完成")

# 2. Test LLM Connection 
try:
    llm = OpenAI(model="gpt-4o", temperature=0)
    response = llm.complete("Say 'System Ready' if you can hear me.")
    print(f"✅ LLM 回應: {response}")
except Exception as e:
    print(f"❌ LLM 連線失敗: {e}")

# 3. Test Vector DB Connection 
try:
    client = qdrant_client.QdrantClient(url=os.getenv("QDRANT_URL"))
    # 簡單建立一個 Collection 測試
    if not client.collection_exists("test_collection"):
        client.create_collection(
            collection_name="test_collection",
            vectors_config=qdrant_client.models.VectorParams(size=1536, distance=qdrant_client.models.Distance.COSINE)
        )
    print("✅ 向量資料庫連線成功")
except Exception as e:
    print(f"❌ 向量資料庫失敗: {e}")