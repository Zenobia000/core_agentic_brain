import sys
import logging
import time
from pathlib import Path

# 路徑修正 (防止 ModuleNotFoundError)
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

from src.ingestion.parser import load_and_chunk_documents
from src.ingestion.extractor import SemanticExtractor
from src.ingestion.indexer import VectorIndexer

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # 輸出到螢幕
        logging.FileHandler("ingestion.log", encoding='utf-8') # 輸出到檔案 (方便除錯)
    ]
)
logger = logging.getLogger(__name__)

def run_pipeline(limit: int = 5):
    """
    執行完整的 RAG 資料處理管線 (Blue Line)
    :param limit: 為了節省 Token，預設只處理前 N 個 Chunks。設為 None 則處理全部。
    """
    logger.info("🚀 啟動 RAG 資料處理管線 (Phase 1 Full Pipeline)")
    
    # 1. 載入與切分 (Parser)
    logger.info("Step 1: 正在載入文件...")
    raw_nodes = load_and_chunk_documents()
    
    if not raw_nodes:
        logger.error("❌ 沒有讀到任何文件，流程終止。")
        return

    logger.info(f"📊 原始文件共切分為 {len(raw_nodes)} 個 Chunks。")
    
    # 應用 Limit 限制
    target_nodes = raw_nodes[:limit] if limit else raw_nodes
    logger.info(f"⚠️ 測試模式：僅處理前 {len(target_nodes)} 個 Chunks (Total: {len(raw_nodes)})")

    # 2. 語意萃取 (Extractor)
    logger.info("Step 2: 開始 AI 語意萃取 (這需要一點時間)...")
    extractor = SemanticExtractor()
    processed_chunks = []

    start_time = time.time()
    for i, node in enumerate(target_nodes):
        logger.info(f"🤖 Processing Chunk {i+1}/{len(target_nodes)} ...")
        result = extractor.extract(node)
        
        if result:
            processed_chunks.append(result)
        else:
            logger.warning(f"⚠️ Chunk {i+1} 萃取失敗，跳過。")

    duration = time.time() - start_time
    logger.info(f"✅ 萃取完成！耗時 {duration:.2f} 秒。成功率: {len(processed_chunks)}/{len(target_nodes)}")

    # 3. 向量入庫 (Indexer)
    if processed_chunks:
        logger.info("Step 3: 寫入向量資料庫 (Qdrant)...")
        indexer = VectorIndexer()
        indexer.index(processed_chunks)
        logger.info("🎉 Pipeline 執行完畢！資料已入庫。")
    else:
        logger.warning("❌ 沒有有效的資料可以入庫。")

if __name__ == "__main__":
    # 執行管線 (預設只跑 5 筆)
    # 想跑全部請改用: run_pipeline(limit=None)
    run_pipeline(limit=5)