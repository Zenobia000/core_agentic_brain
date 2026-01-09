import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# 設定專案根目錄 (確保能讀到 .env 與 data)
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

from llama_index.core import SimpleDirectoryReader, Settings
from llama_index.core.node_parser import SentenceSplitter

# 配置日誌
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

def load_and_chunk_documents(data_dir: str = "data/raw"):
    """
    1. 讀取指定目錄下的 PDF/MD 文件
    2. 執行初步切分 (Structure Pass)
    3. 返回 Node 列表
    """
    input_dir = BASE_DIR / data_dir
    
    if not input_dir.exists():
        logger.error(f"❌ 資料目錄不存在: {input_dir}")
        return []

    # 1. 讀取文件 (Ingestion)
    logger.info(f"📂 開始掃描目錄: {input_dir} ...")
    reader = SimpleDirectoryReader(
        input_dir=str(input_dir),
        recursive=True,
        required_exts=[".pdf", ".md"], # 鎖定 PDF 與 Markdown
        filename_as_id=True
    )
    documents = reader.load_data()
    logger.info(f"✅ 成功讀取 {len(documents)} 頁原始文件")

    if not documents:
        logger.warning("⚠️ 目錄為空，請放入 .pdf 檔案！")
        return []

    # 2. 切分策略 (Chunking Strategy) - 對應 Roadmap 1.1
    # 這裡使用 SentenceSplitter 做為基礎切分 (Structure Pass)
    # chunk_size=1024 約對應中文 500-800 字，保留上下文
    splitter = SentenceSplitter(
        chunk_size=1024,
        chunk_overlap=200
    )

    nodes = splitter.get_nodes_from_documents(documents)
    
    # 3. 補充 Metadata (為 Phase 1.2 語意萃取做準備)
    for node in nodes:
        # 確保有檔名資訊，方便後續回溯
        file_name = node.metadata.get("file_name", "unknown")
        page_label = node.metadata.get("page_label", "1")
        
        # 您可以在這裡加入更多自定義 Metadata 邏輯
        node.metadata["processed_by"] = "parser_v1"
        
        # 簡化顯示用
        logger.debug(f"Chunk created: {file_name} (Page {page_label}) - {len(node.text)} chars")

    logger.info(f"✂️  文件已切分為 {len(nodes)} 個節點 (Chunks)")
    return nodes

if __name__ == "__main__":
    # 測試執行
    try:
        nodes = load_and_chunk_documents()
        if nodes:
            # 預覽第一個 Chunk 的內容
            print("\n" + "="*50)
            print(f"👀 預覽第一個 Chunk (來自: {nodes[0].metadata['file_name']})")
            print("-" * 50)
            print(nodes[0].text[:500] + "...") # 只印前 500 字
            print("="*50 + "\n")
            print(f"✅ Parser 測試成功！準備進入語意萃取 (Phase 1.2)")
    except Exception as e:
        logger.error(f"❌ 執行失敗: {e}")