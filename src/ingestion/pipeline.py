import sys
import logging
import asyncio
from pathlib import Path

# 設定專案根目錄
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

# 引入我們之前寫好的模組
from src.ingestion.parser import load_and_chunk_documents
from src.ingestion.extractor import extract_nq1d
from src.ingestion.indexer import index_nodes

# 配置日誌
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def run_pipeline(target_filename: str = None):
    """
    執行 RAG 資料處理管線
    :param target_filename: 如果有指定，只處理這個檔案 (尚未實作單檔過濾，目前仍掃描目錄，但可用於擴充)
    """
    logger.info("🚀 啟動 RAG 資料處理管線 (Phase 1 Full Pipeline)")

    # Step 1: Parsing (Docling + Cohere)
    # 目前 parser 預設會掃描 data/raw 下的所有檔案
    # 若要優化效能，未來可以讓 parser 支援只讀特定檔案
    logger.info("Step 1: 正在載入與切分文件...")
    nodes = load_and_chunk_documents(data_dir="data/raw")
    
    if not nodes:
        logger.warning("⚠️ 沒有產生任何節點，結束管線。")
        return {"status": "empty", "processed_docs": 0}

    logger.info(f"📊 原始文件共切分為 {len(nodes)} 個 Chunks。")

    # Step 2: Extracting (NQ1D)
    logger.info("Step 2: 開始 AI 語意萃取 (這需要一點時間)...")
    # 這裡可以考慮只對新進檔案做萃取，目前先全量處理
    nodes = await extract_nq1d(nodes)

    # Step 3: Indexing (Qdrant)
    logger.info("Step 3: 寫入向量資料庫 (Qdrant)...")
    success_count = await index_nodes(nodes)
    
    logger.info("🎉 Pipeline 執行完畢！資料已入庫。")
    return {"status": "success", "processed_chunks": len(nodes), "indexed_count": success_count}

if __name__ == "__main__":
    # 如果是直接執行腳本
    asyncio.run(run_pipeline())