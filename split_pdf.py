"""
PDF 分割工具
用於將大型 PDF 切割成小份，避免 MCP timeout 問題

使用方式:
    python split_pdf.py data/raw/2015_ResNet.pdf --pages 5
    python split_pdf.py data/raw/2017_Transformer.pdf --pages 3
"""

import argparse
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("請先安裝 pypdf: pip install pypdf")
    exit(1)


def split_pdf(input_path: str, pages_per_chunk: int = 5, output_dir: str = None):
    """
    將 PDF 分割成多個小檔案
    
    Args:
        input_path: 原始 PDF 路徑
        pages_per_chunk: 每個分割檔案的頁數
        output_dir: 輸出目錄 (預設為原始檔案同目錄)
    
    Returns:
        list: 分割後的檔案路徑列表
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"找不到檔案: {input_path}")
    
    # 設定輸出目錄
    if output_dir:
        output_dir = Path(output_dir)
    else:
        output_dir = input_path.parent
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 讀取 PDF
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)
    
    print(f"📄 檔案: {input_path.name}")
    print(f"📊 總頁數: {total_pages}")
    print(f"✂️  每份頁數: {pages_per_chunk}")
    
    output_files = []
    chunk_num = 1
    
    for start_page in range(0, total_pages, pages_per_chunk):
        end_page = min(start_page + pages_per_chunk, total_pages)
        
        # 建立新的 PDF
        writer = PdfWriter()
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])
        
        # 輸出檔名
        stem = input_path.stem
        output_name = f"{stem}_part{chunk_num:02d}_p{start_page+1}-{end_page}.pdf"
        output_path = output_dir / output_name
        
        # 寫入檔案
        with open(output_path, "wb") as f:
            writer.write(f)
        
        output_files.append(str(output_path))
        print(f"  ✅ {output_name} (頁 {start_page+1}-{end_page})")
        
        chunk_num += 1
    
    print(f"\n🎉 完成！共分割成 {len(output_files)} 個檔案")
    return output_files


def main():
    parser = argparse.ArgumentParser(
        description="PDF 分割工具 - 將大型 PDF 切割成小份"
    )
    parser.add_argument(
        "input",
        help="輸入 PDF 檔案路徑"
    )
    parser.add_argument(
        "--pages", "-p",
        type=int,
        default=5,
        help="每個分割檔案的頁數 (預設: 5)"
    )
    parser.add_argument(
        "--output", "-o",
        help="輸出目錄 (預設: 與原始檔案同目錄)"
    )
    
    args = parser.parse_args()
    
    try:
        split_pdf(args.input, args.pages, args.output)
    except FileNotFoundError as e:
        print(f"❌ 錯誤: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        exit(1)


if __name__ == "__main__":
    main()