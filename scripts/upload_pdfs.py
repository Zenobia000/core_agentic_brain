#!/usr/bin/env python3
"""
PDF 上傳腳本 - 將 PDF 文件上傳到知識庫
"""

import os
import sys
import asyncio
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# 確保載入 .env 檔案（使用專案根目錄）
from dotenv import load_dotenv
_project_root = Path(__file__).resolve().parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import AsyncOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance


# 配置
COLLECTION_NAME = "rag_knowledge_base"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


async def extract_text_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """從 PDF 提取文字並分塊"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("請安裝 PyMuPDF: pip install pymupdf")
        sys.exit(1)
    
    doc = fitz.open(pdf_path)
    file_name = Path(pdf_path).name
    
    chunks = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        if not text.strip():
            continue
        
        # 分塊
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1
            
            if current_length >= CHUNK_SIZE:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "file_name": file_name,
                    "page_label": str(page_num + 1),
                    "chunk_index": len(chunks)
                })
                
                # 保留 overlap
                overlap_words = current_chunk[-CHUNK_OVERLAP // 5:]
                current_chunk = overlap_words
                current_length = sum(len(w) + 1 for w in current_chunk)
        
        # 處理最後一個 chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(chunk_text) > 50:  # 至少 50 字元
                chunks.append({
                    "text": chunk_text,
                    "file_name": file_name,
                    "page_label": str(page_num + 1),
                    "chunk_index": len(chunks)
                })
    
    doc.close()
    return chunks


async def get_embeddings(texts: List[str], client: AsyncOpenAI) -> List[List[float]]:
    """批次取得向量"""
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    return [item.embedding for item in response.data]


async def upload_pdf(pdf_path: str, qdrant: QdrantClient, openai_client: AsyncOpenAI):
    """上傳單一 PDF"""
    print(f"\n📄 處理: {Path(pdf_path).name}")
    
    # 提取文字
    chunks = await extract_text_from_pdf(pdf_path)
    print(f"   提取了 {len(chunks)} 個區塊")
    
    if not chunks:
        print("   ⚠️ 無法提取文字")
        return
    
    # 批次處理 embedding
    batch_size = 20
    all_points = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c["text"] for c in batch]
        
        print(f"   正在處理 {i + 1}-{min(i + batch_size, len(chunks))} / {len(chunks)}...")
        
        embeddings = await get_embeddings(texts, openai_client)
        
        for j, (chunk, embedding) in enumerate(zip(batch, embeddings)):
            # 生成唯一 ID
            content_hash = hashlib.md5(
                f"{chunk['file_name']}_{chunk['page_label']}_{chunk['chunk_index']}".encode()
            ).hexdigest()
            point_id = int(content_hash[:16], 16) % (2**63)
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "text": chunk["text"],
                    "file_name": chunk["file_name"],
                    "page_label": chunk["page_label"],
                    "chunk_index": chunk["chunk_index"],
                    "source": "pdf_upload"
                }
            )
            all_points.append(point)
    
    # 上傳到 Qdrant
    print(f"   上傳 {len(all_points)} 個向量到 Qdrant...")
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=all_points
    )
    
    print(f"   ✅ 完成: {Path(pdf_path).name}")


async def main():
    # 檢查環境變數
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 錯誤: OPENAI_API_KEY 未設置")
        sys.exit(1)
    
    # 初始化客戶端
    openai_client = AsyncOpenAI(api_key=api_key)
    qdrant = QdrantClient(
        host=os.getenv("QDRANT_HOST", "localhost"),
        port=int(os.getenv("QDRANT_PORT", 6333))
    )
    
    # 確保 collection 存在
    collections = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION_NAME not in collections:
        print(f"建立 collection: {COLLECTION_NAME}")
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIM,
                distance=Distance.COSINE
            )
        )
    
    # 取得 PDF 檔案
    if len(sys.argv) > 1:
        pdf_files = sys.argv[1:]
    else:
        # 預設搜尋當前目錄
        pdf_files = list(Path(".").glob("*.pdf"))
    
    if not pdf_files:
        print("用法: python upload_pdfs.py file1.pdf file2.pdf ...")
        sys.exit(1)
    
    print(f"\n📚 準備上傳 {len(pdf_files)} 個 PDF 檔案\n")
    print("=" * 50)
    
    for pdf_path in pdf_files:
        if not Path(pdf_path).exists():
            print(f"⚠️ 檔案不存在: {pdf_path}")
            continue
        
        await upload_pdf(str(pdf_path), qdrant, openai_client)
    
    # 顯示統計
    print("\n" + "=" * 50)
    info = qdrant.get_collection(COLLECTION_NAME)
    print(f"\n📊 知識庫統計:")
    print(f"   總向量數: {info.points_count}")
    print(f"   索引狀態: {info.status}")
    print("\n✅ 上傳完成!")


if __name__ == "__main__":
    asyncio.run(main())
