"""
環境變數載入模組
確保從專案根目錄載入 .env 檔案
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 找到專案根目錄（包含 pyproject.toml 或 .env 的目錄）
def find_project_root() -> Path:
    """尋找專案根目錄"""
    current = Path(__file__).resolve().parent
    
    # 往上找直到找到 pyproject.toml 或 .env
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
        if (parent / ".env").exists():
            return parent
    
    # 找不到就用當前目錄
    return Path.cwd()


# 專案根目錄
PROJECT_ROOT = find_project_root()

# .env 檔案路徑
DOTENV_PATH = PROJECT_ROOT / ".env"

# 載入 .env
def load_env():
    """載入環境變數"""
    if DOTENV_PATH.exists():
        load_dotenv(DOTENV_PATH)
        return True
    else:
        # 嘗試當前目錄
        load_dotenv()
        return False


# 模組載入時自動執行
_loaded = load_env()

# 驗證 API Key
def get_openai_api_key() -> str:
    """取得 OpenAI API Key"""
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise ValueError(
            f"OPENAI_API_KEY 未設置！\n"
            f"請確認 .env 檔案存在於: {DOTENV_PATH}\n"
            f"並包含: OPENAI_API_KEY=sk-proj-xxx"
        )
    return key


def ensure_env_loaded():
    """確保環境變數已載入（可重複呼叫）"""
    if not os.getenv("OPENAI_API_KEY"):
        load_env()
