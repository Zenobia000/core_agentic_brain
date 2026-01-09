import logging
from src.ingestion.parser import PDFParser
from src.ingestion.indexer import Indexer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_ingestion(file_path: str):
    logger.info(f"🚀 [Pipeline] 開始處理檔案: {file_path}")
    try:
        parser = PDFParser()
        documents = parser.parse(file_path) # 解析
        
        if not documents:
            logger.warning("⚠️ 解析結果為空")
            return

        indexer = Indexer()
        indexer.index_documents(documents) # 入庫
        logger.info("✅ [Pipeline] 成功！")

    except Exception as e:
        logger.error(f"❌ [Pipeline] 失敗: {e}")
        raise e