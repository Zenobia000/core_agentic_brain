import logging
import sys
import os
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# 路徑修正 (防止 ModuleNotFoundError)
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

from llama_index.llms.openai import OpenAI
from llama_index.core.prompts import PromptTemplate

# 載入環境變數
load_dotenv()

logger = logging.getLogger(__name__)

# --- 嚴格的 System Prompt ---
# --- 修正後的 System Prompt (完全防呆版) ---
QA_SYSTEM_PROMPT = """
你是一個專業的企業知識助理。請根據下方的【參考資料】回答使用者的問題。

回答規則：
1. **必須基於事實**：只能使用提供的參考資料回答，不要編造。
2. **標註引用來源**：
   - 每當你引用某個片段的資訊時，請查看該片段開頭的 `來源: ...` 欄位。
   - 嚴格依照該欄位的內容標註，格式為 `[檔案名稱, Page 頁碼]`。
   - 不要自己發明檔名，**直接複製**參考資料中顯示的檔名。
3. **結構清晰**：使用條列式或段落分明的方式回答。
4. **繁體中文**：請使用台灣繁體中文回答。

【參考資料】：
---------------------
{context_str}
---------------------
"""

class RAGGenerator:
    def __init__(self):
        # 使用 GPT-4o 確保邏輯與引用準確性 
        self.llm = OpenAI(model="gpt-4o", temperature=0.1)
        self.prompt_tmpl = PromptTemplate(QA_SYSTEM_PROMPT)

    def format_context(self, search_results: List) -> str:
        """
        將 Qdrant 的搜尋結果轉換為純文字 Context 
        """
        context_list = []
        for i, hit in enumerate(search_results):
            payload = hit.payload
            # 組裝每一個片段 (Chunk)
            # 我們把摘要和原文都餵給 LLM，讓它自己判斷細節
            chunk_text = (
                f"--- 文件片段 {i+1} ---\n"
                f"來源: {payload.get('file_name')}, Page {payload.get('page_label')}\n"
                f"摘要: {payload.get('summary')}\n"
                f"內文: {payload.get('text')}\n"
            )
            context_list.append(chunk_text)
        
        # 用換行接起來
        return "\n\n".join(context_list)

    def generate(self, query: str, search_results: List) -> str:
        """
        核心生成邏輯：Context + Query -> LLM -> Answer
        """
        if not search_results:
            return "抱歉，我在知識庫中找不到相關資訊。"

        # 1. 準備 Context
        context_str = self.format_context(search_results)
        
        # 2. 格式化 Prompt
        prompt = self.prompt_tmpl.format(context_str=context_str)
        
        logger.info(f"🤖 正在生成回答 (Context size: {len(context_str)} chars)...")
        
        # 3. 呼叫 LLM
        # 注意：這裡是把 Prompt 和 User Query 接在一起
        response = self.llm.complete(prompt + f"\n\n使用者問題：{query}")
        
        return str(response)

# 單元測試 (End-to-End Test)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # 這裡會用到我們剛寫好的 HybridRetriever
    from src.retrieval.search import HybridRetriever
    
    # 1. 定義問題
    test_query = "CLIP 模型是如何訓練的？"
    print(f"❓ 問題: {test_query}")

    # 2. 執行檢索 (Phase 2)
    print("🔍 Step 1: 檢索中...")
    retriever = HybridRetriever()
    results = retriever.search(test_query, top_k=3)
    
    # 3. 執行生成 (Phase 3)
    print("🤖 Step 2: 生成中...")
    generator = RAGGenerator()
    answer = generator.generate(test_query, results)
    
    print("\n" + "="*50)
    print("💡 最終回答 (Final Answer):")
    print("="*50)
    print(answer)
    print("="*50)