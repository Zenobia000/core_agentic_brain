from typing import List, Optional
from pydantic import BaseModel, Field

# 這是我們最核心的資料結構 (對應 Roadmap Phase 1.2)

class NQ1DItem(BaseModel):
    """
    Normalized Question for 1 Document:
    代表一個針對該 Chunk 內容的標準化問題。
    """
    canonical_q: str = Field(..., description="標準化問題 (Standardized Question)，語氣需完整且明確。")
    intent: str = Field(..., description="問題意圖，例如: 'definition', 'procedure', 'reasoning', 'fact'.")

class SemanticExtraction(BaseModel):
    """
    LLM 輸出的語意萃取結果
    """
    summary: str = Field(..., description="這段文字的精簡摘要 (1-2 句話)。")
    what: str = Field(..., description="這段文字定義了什麼核心概念或物件？")
    why: str = Field(..., description="為什麼這很重要？或是提到的問題/現象的原因。")
    how: List[str] = Field(..., description="具體的步驟、方法論或運作機制 (列點)。")
    
    # 這裡就是 NQ1D 的核心：讓 LLM 生成「這段文字能回答什麼問題」
    nq1d: List[NQ1DItem] = Field(..., description="基於這段內容生成的 1-3 個標準化問答對 (NQ1D)。")
    
    keywords: List[str] = Field(..., description="關鍵詞標籤，用於 Hybrid Search。")

class ProcessedChunk(BaseModel):
    """
    這是最終寫入向量資料庫的格式
    """
    chunk_id: str
    file_name: str
    page_label: str
    text: str
    # 嵌入 semantic_data 結構
    semantic_data: SemanticExtraction