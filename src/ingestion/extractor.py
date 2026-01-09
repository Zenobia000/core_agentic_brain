import os
import logging
import asyncio
from typing import List
from llama_index.core.schema import BaseNode
from openai import AsyncOpenAI

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def extract_nq1d(nodes: List[BaseNode]) -> List[BaseNode]:
    """
    使用 LLM (GPT-4o) 為每一個 Chunk 生成「標準化問題 (NQ1D)」。
    這些問題將被存入 node.metadata["questions"]，用於後續的精準檢索。
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ 未設定 OPENAI_API_KEY，無法執行語意萃取")
        return nodes

    client = AsyncOpenAI(api_key=api_key)
    
    logger.info(f"🤖 正在為 {len(nodes)} 個節點生成 NQ1D 問題...")

    # 定義處理單個節點的函數 (包含重試機制)
    async def process_node(node: BaseNode, index: int):
        # 簡單的防呆：如果內容太短，就不生成問題了
        if len(node.text) < 50:
            node.metadata["questions"] = []
            return

        prompt = f"""
        你是一個專業的資料分析師。請閱讀以下技術文件片段，並生成 3 個「使用者最可能會問的問題」。
        這些問題必須能由該片段回答。

        文件片段：
        ---
        {node.text[:1500]} 
        ---

        回應格式要求：
        1. 只回傳問題，一行一個。
        2. 不要加編號 (1. 2. 3.) 或其他廢話。
        3. 使用繁體中文。
        """

        try:
            response = await client.chat.completions.create(
                model="gpt-4o", # 或 gpt-3.5-turbo
                messages=[
                    {"role": "system", "content": "你是一個精準的問題生成助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            # 處理回傳文字，變成 List
            questions = [line.strip() for line in content.split('\n') if line.strip()]
            
            # 存入 metadata
            node.metadata["questions"] = questions
            # node.metadata["questions_text"] = "\n".join(questions) # 備用字串欄位
            
            logger.info(f"✅ Chunk {index+1} 生成了 {len(questions)} 個問題")

        except Exception as e:
            logger.error(f"❌ Chunk {index+1} 生成失敗: {e}")
            node.metadata["questions"] = []

    # 為了避免打爆 OpenAI Rate Limit，我們用 Semaphore 限制併發數 (例如一次 5 個)
    sem = asyncio.Semaphore(5)

    async def sem_task(node, index):
        async with sem:
            await process_node(node, index)

    # 建立所有任務並執行
    tasks = [sem_task(node, i) for i, node in enumerate(nodes)]
    await asyncio.gather(*tasks)

    logger.info("🎉 所有節點的 NQ1D 萃取完成！")
    return nodes