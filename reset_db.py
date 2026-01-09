from qdrant_client import QdrantClient

# 連線到 Qdrant
client = QdrantClient(url="http://localhost:6333")

collection_name = "rag_knowledge_base"

# 強制刪除舊的集合
try:
    client.delete_collection(collection_name)
    print(f"✅ 成功刪除舊集合: {collection_name}")
except Exception as e:
    print(f"⚠️ 刪除失敗 (可能本來就不存在): {e}")

# 檢查是否真的刪了
collections = client.get_collections()
print(f"🔍 目前剩餘的集合: {collections}")