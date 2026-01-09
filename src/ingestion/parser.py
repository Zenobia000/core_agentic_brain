import logging
import os
from docling.document_converter import DocumentConverter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFParser:
    def __init__(self):
        self.converter = DocumentConverter()

    def parse(self, file_path: str):
        """
        解析 PDF 並回傳結構化資料列表
        """
        logger.info(f"📄 [Parser] 正在解析 PDF: {file_path}")
        try:
            result = self.converter.convert(file_path)
            doc = result.document
            
            # 先收集所有段落，按頁碼分組
            pages_content = {}
            
            for item in doc.texts:
                text_content = item.text.strip()
                if not text_content or len(text_content) < 10:  # 跳過太短的內容
                    continue
                
                # 取得頁碼
                page_label = "unknown"
                if hasattr(item, 'prov') and item.prov:
                    prov = item.prov[0] if isinstance(item.prov, list) else item.prov
                    if hasattr(prov, 'page_no'):
                        page_label = str(prov.page_no)
                    elif hasattr(prov, 'page'):
                        page_label = str(prov.page)
                
                # 按頁碼分組
                if page_label not in pages_content:
                    pages_content[page_label] = []
                pages_content[page_label].append(text_content)
            
            # 合併同一頁的內容，每 500 字切一個 chunk
            parsed_data = []
            for page_label, texts in pages_content.items():
                # 合併該頁所有文字
                full_text = " ".join(texts)
                
                # 切分成較大的 chunks (每 500 字)
                chunk_size = 500
                for i in range(0, len(full_text), chunk_size):
                    chunk_text = full_text[i:i + chunk_size]
                    if len(chunk_text) > 50:  # 確保 chunk 不會太小
                        parsed_data.append({
                            "text": chunk_text,
                            "metadata": {
                                "file_name": os.path.basename(file_path),
                                "page_label": page_label
                            }
                        })
            
            logger.info(f"📄 [Parser] 解析完成，共 {len(parsed_data)} 個段落")
            return parsed_data

        except Exception as e:
            logger.error(f"❌ [Parser] 解析失敗: {e}")
            return []


if __name__ == "__main__":
    parser = PDFParser()
    test_file = "data/raw/2021_CLIP_small.pdf"
    results = parser.parse(test_file)
    
    print(f"\n📋 解析結果預覽（共 {len(results)} 個 chunks）：")
    for i, item in enumerate(results[:5]):
        print(f"\n--- Chunk {i+1} (Page {item['metadata']['page_label']}) ---")
        print(f"長度: {len(item['text'])} 字")
        print(f"內容: {item['text'][:200]}...")