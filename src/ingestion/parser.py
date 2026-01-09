import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# 設定專案根目錄
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

from llama_index.core import SimpleDirectoryReader
# 1. 引入語意切分器
from llama_index.core.node_parser import SemanticSplitterNodeParser
# 2. 引入 Docling Reader
from llama_index.readers.docling import DoclingReader
# 3. 引入 Cohere Embedding (作為切分依據)
from llama_index.embeddings.cohere import CohereEmbedding

# 配置日誌
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

def load_and_chunk_documents(data_dir: str = "data/raw"):
    """
    【終極混合策略】
    1. Parsing: 使用 IBM Docling 將 PDF 轉為乾淨的 Markdown (解決排版/表格問題)
    2. Chunking: 使用 Cohere Embedding 進行語意切分 (解決上下文截斷問題)
    """
    input_dir = BASE_DIR / data_dir
    
    if not input_dir.exists():
        logger.error(f"❌ 資料目錄不存在: {input_dir}")
        return []

    # --- Step 1: Docling 解析 (清洗資料) ---
    logger.info("🧠 [Step 1] 初始化 Docling 解析器 (Layout Parsing)...")
    docling_reader = DoclingReader(export_type="markdown")

    reader = SimpleDirectoryReader(
        input_dir=str(input_dir),
        recursive=True,
        required_exts=[".pdf"],
        file_extractor={".pdf": docling_reader},
        filename_as_id=True
    )
    
    logger.info("🚀 正在執行 Docling 解析 (這會花一點時間)...")
    # 這裡出來的是整份完整的文件，還沒切
    documents = reader.load_data()
    logger.info(f"✅ Docling 清洗完成！獲得 {len(documents)} 份結構化文件")

    # --- Step 2: Cohere 語意切分 (精準下刀) ---
    logger.info("🧠 [Step 2] 初始化 Cohere 語意切分器 (Semantic Chunking)...")
    
    # 使用你的 Cohere Key
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        logger.error("❌ 找不到 COHERE_API_KEY，請檢查 .env 檔案")
        return []

    embed_model = CohereEmbedding(
        cohere_api_key=api_key,
        model_name="embed-multilingual-v3.0", # 支援中文最強
        input_type="search_document"
    )
    
    # 設定切分器
    # buffer_size=1: 比較前後句
    # breakpoint_percentile_threshold=95: 只有語意差異極大時才切斷 (保持段落完整性)
    splitter = SemanticSplitterNodeParser(
        buffer_size=1,
        breakpoint_percentile_threshold=95, 
        embed_model=embed_model
    )

    logger.info("✂️  正在使用 Cohere 計算語意距離並切分...")
    # 這裡會真的很慢，因為每一句都要 call API
    # 為了防止 Trial Key 爆掉，我們這裡不特別加 sleep，但如果文件太大可能會 429
    nodes = splitter.get_nodes_from_documents(documents)
    
    # 3. 補充 Metadata
    for node in nodes:
        node.metadata["processed_by"] = "docling_plus_cohere_semantic"
        logger.debug(f"Hybrid Chunk: {len(node.text)} chars")

    logger.info(f"✅ 混合策略切分完成！共生成 {len(nodes)} 個語意節點")
    
    return nodes

if __name__ == "__main__":
    try:
        nodes = load_and_chunk_documents()
        if nodes:
            print("\n" + "="*50)
            print(f"👀 預覽 Docling + Cohere 切分結果:")
            print("-" * 50)
            # 看看切出來的第一段長什麼樣
            print(nodes[0].text[:800] + "...") 
            print("="*50)
            
            # 驗證一下是不是真的照語意切 (長度應該很不固定)
            print("📊 Chunk 長度分佈 (前 5 個):")
            for i, n in enumerate(nodes[:5]):
                print(f"   Chunk {i+1}: {len(n.text)} chars")
                
            print(f"\n✅ Parser 測試成功！")
    except Exception as e:
        logger.error(f"❌ 執行失敗: {e}")