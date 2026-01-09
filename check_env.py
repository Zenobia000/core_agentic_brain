import os
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
import qdrant_client
from qdrant_client import models  # [修正點] 顯式匯入 models 模組

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
    # 建立 Client
    client = qdrant_client.QdrantClient(url=os.getenv("QDRANT_URL"))
    
    # 檢查並建立 Collection
    if not client.collection_exists("test_collection"):
        client.create_collection(
            collection_name="test_collection",
            # [修正點] 直接使用 models.VectorParams
            vectors_config=models.VectorParams(
                size=1536, 
                distance=models.Distance.COSINE
            )
        )
    print("✅ 向量資料庫連線成功 (Collection 'test_collection' is ready)")
except Exception as e:
    print(f"❌ 向量資料庫失敗: {e}")