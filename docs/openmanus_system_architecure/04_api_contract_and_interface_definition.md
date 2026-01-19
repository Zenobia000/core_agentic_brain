# API 契約與接口定義 (API Contract & Interface Definition) - OpenManus

---

**文件版本 (Document Version):** `v1.0`

**最後更新 (Last Updated):** `2025-10-14`

**主要作者 (Lead Author):** `OpenManus Team`

**審核者 (Reviewers):** `Community Contributors`

**狀態 (Status):** `已批准 (Approved)`

---

## 目錄 (Table of Contents)

1.  [概述 (Overview)](#1-概述-overview)
2.  [CLI 介面 (CLI Interface)](#2-cli-介面-cli-interface)
3.  [Agent 程式介面 (Agent Python API)](#3-agent-程式介面-agent-python-api)
4.  [MCP Server 介面 (MCP Server Interface)](#4-mcp-server-介面-mcp-server-interface)

---

## 1. 概述 (Overview)

### 1.1 文件目的 (Document Purpose)
*   定義 OpenManus 對外提供的互動介面，包括命令行 (CLI)、程式調用 (Library) 和 MCP 協議介面。

---

## 2. CLI 介面 (CLI Interface)

*   **入口點**: `main.py`
*   **命令格式**:
    ```bash
    python main.py [--prompt PROMPT]
    ```
*   **參數**:
    *   `--prompt`: (Optional) 初始任務提示詞。若未提供，將進入互動模式詢問。

---

## 3. Agent 程式介面 (Agent Python API)

*供其他 Python 程式整合使用*

### 3.1 `Manus` Agent
*   **Class**: `app.agent.manus.Manus`
*   **方法**: `run(request: str) -> str`
    *   **Input**: `request` (String) - 用戶的任務描述。
    *   **Output**: `result` (String) - 任務執行結果摘要。
    *   **非同步**: 是 (`async def`)。

#### 使用範例
```python
import asyncio
from app.agent.manus import Manus

async def main():
    agent = await Manus.create()
    result = await agent.run("Research the history of AI")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. MCP Server 介面 (MCP Server Interface)

*   **協議**: Model Context Protocol (MCP)
*   **傳輸方式**: `stdio` (標準輸入輸出)
*   **提供的工具 (Tools)**:
    1.  `bash`: 執行 Bash 命令。
    2.  `browser`: 控制瀏覽器進行網頁操作。
    3.  `editor`: 文件編輯 (字串替換)。
    4.  `terminate`: 結束任務。

### 4.1 工具定義範例 (Bash)
*   **Name**: `bash`
*   **Description**: Execute a bash command
*   **Parameters**:
    *   `command` (string, required): The bash command to execute.
