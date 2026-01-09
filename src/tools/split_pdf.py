import os
import sys
from pathlib import Path
from pypdf import PdfReader, PdfWriter

# 設定路徑
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "raw"

def create_small_pdf(filename: str, output_name: str, num_pages: int = 5):
    input_path = DATA_DIR / filename
    output_path = DATA_DIR / output_name
    
    if not input_path.exists():
        print(f"❌ 找不到檔案: {input_path}")
        return

    reader = PdfReader(input_path)
    writer = PdfWriter()

    # 取前 N 頁 (如果總頁數不夠，就全取)
    limit = min(len(reader.pages), num_pages)
    
    print(f"✂️ 正在裁切前 {limit} 頁...")
    for i in range(limit):
        writer.add_page(reader.pages[i])

    with open(output_path, "wb") as f:
        writer.write(f)
    
    print(f"✅ 已建立迷你版 PDF: {output_path}")

if __name__ == "__main__":
    # 執行切割
    create_small_pdf("2021_CLIP.pdf", "2021_CLIP_small.pdf", num_pages=5)