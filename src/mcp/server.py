@mcp.tool()
async def rag_list_documents() -> str:
    """
    列出知識庫中所有已索引的文件
    
    Returns:
        已索引的文件列表
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.get(f"{RAG_API_BASE}/documents")
            response.raise_for_status()
            docs = response.json()
            
            if not docs:
                return "知識庫目前沒有任何文件"
            
            output = ["📚 已索引的文件:", ""]
            for i, doc in enumerate(docs, 1):
                # 處理字串列表或物件列表
                if isinstance(doc, str):
                    output.append(f"  {i}. {doc}")
                else:
                    name = doc.get("name", "unknown")
                    chunks = doc.get("chunks", "?")
                    status = doc.get("status", "unknown")
                    output.append(f"  {i}. {name}")
                    output.append(f"     狀態: {status} | 區塊數: {chunks}")
            
            return "\n".join(output)
            
        except httpx.HTTPError as e:
            return f"取得文件列表失敗: {str(e)}"