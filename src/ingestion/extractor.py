import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# --- [關鍵修正] 設定專案根目錄路徑，確保能 Import src 模組 ---
# 取得當前檔案的上一層的上一層 (即專案根目錄 rag-project)
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))
# -----------------------------------------------------------

from llama_index.core import Document
from llama_index.core.schema import TextNode
from llama_index.llms.openai import OpenAI
from llama_index.core.prompts import PromptTemplate

# 現在 Python 找得到 src 了
from src.ingestion.schema import SemanticExtraction, ProcessedChunk

load_dotenv()
logger = logging.getLogger(__name__)

# --- System Prompt 設計 (Roadmap Phase 1.2) ---
EXTRACT_PROMPT_TMPL = """
你是一位資深的技術文件分析師。你的任務是從以下「文件片段 (Chunk)」中萃取關鍵知識，並將其轉化為結構化數據。

請特別關注：
1. **WHAT**: 這段文字在講什麼核心概念？
2. **WHY**: 為什麼這樣做？有什麼好處或原因？
3. **HOW**: 具體的方法、步驟或演算法細節。
4. **NQ1D**: 想像使用者會問什麼問題，而這段文字正好是完美答案？請生成 "Canonical Question" (標準化問題)。

文件片段內容：
---------------------
{context_str}
---------------------

請以繁體中文輸出，並嚴格遵守 JSON Schema 格式。
如果該片段沒有包含特定欄位（如沒有步驟），請在該欄位填入 "N/A" 或空陣列。
"""

class SemanticExtractor:
    def __init__(self):
        # 使用 GPT-4o 確保 JSON 遵循能力與推理解析能力
        self.llm = OpenAI(model="gpt-4o", temperature=0.1)
        self.prompt = PromptTemplate(EXTRACT_PROMPT_TMPL)

    def extract(self, node: TextNode) -> ProcessedChunk:
        """
        對單一 Node 進行 LLM 萃取
        """
        try:
            # 1. 構建 Prompt
            fmt_prompt = self.prompt.format(context_str=node.text)
            
            # 2. 呼叫 LLM (使用 structured_predict 強制輸出 Pydantic 格式)
            extraction = self.llm.structured_predict(
                SemanticExtraction, 
                prompt=self.prompt,
                context_str=node.text
            )
            
            # 3. 組裝最終物件
            processed_chunk = ProcessedChunk(
                chunk_id=node.node_id,
                file_name=node.metadata.get("file_name", "unknown"),
                page_label=node.metadata.get("page_label", "unknown"),
                text=node.text,
                semantic_data=extraction
            )
            
            logger.info(f"✅ Extracted: {processed_chunk.file_name} (Page {processed_chunk.page_label}) - Q: {extraction.nq1d[0].canonical_q}")
            return processed_chunk

        except Exception as e:
            logger.error(f"❌ Extraction failed for node {node.node_id}: {e}")
            return None

# 單元測試區
if __name__ == "__main__":
    # 這裡不需要再 append path 了，因為上面已經做過了
    from src.ingestion.parser import load_and_chunk_documents
    
    logging.basicConfig(level=logging.INFO)
    
    # 1. 讀取文件
    print("📂 正在載入文件並切塊...")
    nodes = load_and_chunk_documents()
    
    if nodes:
        extractor = SemanticExtractor()
        # 測試：只跑第 2 個 Chunk (避開封面)
        target_idx = 1 if len(nodes) > 1 else 0
        target_node = nodes[target_idx]
        
        print(f"\n🤖 正在對 Chunk {target_idx} 進行 AI 萃取 (Text: {target_node.text[:50]}...)\n")
        result = extractor.extract(target_node)
        
        if result:
            print("\n" + "="*50)
            print("🚀 萃取結果 (JSON):")
            print(result.semantic_data.model_dump_json(indent=2))
            print("="*50 + "\n")