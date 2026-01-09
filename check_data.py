from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

# 取得所有資料
results = client.scroll(
    collection_name="rag_knowledge_base",
    limit=100,
    with_payload=True
)

print(f"📊 共有 {len(results[0])} 筆資料\n")

# 檢查有沒有包含 "400 million" 的內容
found_400m = False
for i, point in enumerate(results[0]):
    text = point.payload.get('text', '')
    page = point.payload.get('page_label', '?')
    
    if '400' in text or 'million' in text.lower():
        found_400m = True
        print(f"✅ 找到！Page {page}")
        print(f"內容: {text[:300]}...")
        print("---")

if not found_400m:
    print("❌ 沒有找到包含 '400 million' 的資料")
    print("\n📋 顯示前 10 筆資料的頁碼和內容預覽：")
    for i, point in enumerate(results[0][:10]):
        text = point.payload.get('text', '')
        page = point.payload.get('page_label', '?')
        print(f"\n--- 第 {i+1} 筆 (Page {page}) ---")
        print(f"{text[:150]}...")