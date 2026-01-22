# 整合性架構與設計文件 - OpenManus Linus 式重構

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2025-01-21`
**主要作者 (Lead Author):** `Linus-style 技術架構師`
**審核者 (Reviewers):** `核心開發團隊, Tech Lead`
**狀態 (Status):** `已批准 (Approved)`

---

## 目錄 (Table of Contents)

- [第 1 部分：架構總覽 (Architecture Overview)](#第-1-部分架構總覽-architecture-overview)
  - [1.1 Linus 式設計原則](#11-linus-式設計原則)
  - [1.2 系統架構圖](#12-系統架構圖)
  - [1.3 技術選型與理由](#13-技術選型與理由)
  - [1.4 數據流設計](#14-數據流設計)
- [第 2 部分：詳細設計 (Detailed Design)](#第-2-部分詳細設計-detailed-design)
  - [2.1 核心模組設計](#21-核心模組設計)
  - [2.2 工具系統設計](#22-工具系統設計)
  - [2.3 Web 界面設計](#23-web-界面設計)
  - [2.4 配置管理設計](#24-配置管理設計)
- [第 3 部分：實施規範 (Implementation Guidelines)](#第-3-部分實施規範-implementation-guidelines)

---

**目的**: 本文件將 OpenManus 重構的業務需求轉化為基於 Linus Torvalds 哲學的極簡技術架構，確保系統的簡潔性、可維護性和高性能。

---

## 第 1 部分：架構總覽 (Architecture Overview)

### 1.1 Linus 式設計原則

#### 核心哲學
> **"好的程式設計師知道寫什麼。偉大的程式設計師知道不寫什麼。"** - Linus Torvalds

| 原則 | 具體應用 | 反例 (避免的設計) |
| :--- | :--- | :--- |
| **Good Taste** | 統一工具介面，零特殊情況 | `if tool_name == "browser": special_handling()` |
| **Simplicity First** | 單一入口點，單一配置檔 | 6 個不同的執行方式 |
| **No Broken Abstractions** | 直接的函數調用 | 3 層無意義類繼承 |
| **Data Structures First** | 簡單的字典和列表 | 複雜的 ORM 對象 |

#### 設計約束
```python
# 設計約束檢查清單
DESIGN_CONSTRAINTS = {
    "max_total_lines": 900,           # 總代碼行數
    "max_function_lines": 20,         # 單函數最大行數
    "max_nesting_depth": 3,           # 最大嵌套深度
    "max_dependencies": 10,           # 最大外部依賴數
    "max_startup_time": 2.0,          # 最大啟動時間(秒)
    "max_response_time": 1.0,         # 最大響應時間(秒)
}
```

### 1.2 系統架構圖

#### 整體架構 (Simple & Clean)
```
┌─────────────────────────────────────────────────────────────┐
│                     OpenManus 極簡架構                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Input                                                 │
│      │                                                      │
│      ▼                                                      │
│  ┌─────────────┐                                           │
│  │  main.py    │ ◄──── 唯一入口點 (< 30 lines)              │
│  │  (Entry)    │                                           │
│  └─────────────┘                                           │
│      │                                                      │
│      ▼                                                      │
│  ┌─────────────┐                                           │
│  │core/agent.py│ ◄──── 核心邏輯 (< 100 lines)               │
│  │ (Core Logic)│                                           │
│  └─────────────┘                                           │
│      │                                                      │
│      ├──── LLM Call ────┐                                  │
│      │                   │                                  │
│      ▼                   ▼                                  │
│  ┌─────────────┐    ┌─────────────┐                       │
│  │ core/llm.py │    │core/tools.py│ ◄──── 工具管理 (< 50)   │
│  │(LLM Wrapper)│    │(Tool Mgr)   │                       │
│  └─────────────┘    └─────────────┘                       │
│                          │                                  │
│                          ▼                                  │
│                    ┌─────────────┐                         │
│                    │   tools/    │ ◄──── 工具實現            │
│                    │ python.py   │       每個 < 50 lines     │
│                    │ browser.py  │                         │
│                    │ files.py    │                         │
│                    └─────────────┘                         │
│                                                             │
│  Web Mode (Optional):                                      │
│  ┌─────────────┐    ┌─────────────┐                       │
│  │web/server.py│◄──►│web/static/  │ ◄──── 原生前端          │
│  │(< 50 lines) │    │ index.html  │       < 400 lines      │
│  │             │    │ style.css   │                       │
│  │             │    │ app.js      │                       │
│  └─────────────┘    └─────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 技術選型與理由

#### 後端技術棧
| 技術 | 選擇 | 理由 | 替代方案 (被拒絕) |
| :--- | :--- | :--- | :--- |
| **語言** | Python 3.11+ | 簡潔語法，豐富生態 | Go (過於底層), Node.js (生態混亂) |
| **Web 框架** | FastAPI (僅 WebSocket) | 最小化 Web 功能 | Django (臃腫), Flask (功能不足) |
| **配置** | PyYAML | 人類可讀，結構化 | JSON (無註釋), TOML (語法複雜) |
| **HTTP 客戶端** | requests | 簡單可靠 | httpx (功能過多), urllib (太底層) |

#### 前端技術棧
| 技術 | 選擇 | 理由 | 替代方案 (被拒絕) |
| :--- | :--- | :--- | :--- |
| **框架** | 原生 HTML/CSS/JS | 零依賴，完全控制 | React (複雜), Vue (不必要), Angular (臃腫) |
| **樣式** | 原生 CSS | 完全定制化 | TailwindCSS (類名冗長), Bootstrap (通用化) |
| **通信** | WebSocket API | 實時雙向通信 | REST API (輪詢效率低), SSE (單向) |

#### 明確拒絕的技術
```python
# 技術黑名單 - Linus 式批評
REJECTED_TECH = {
    "PostgreSQL": "聊天工具不需要企業級數據庫",
    "Redis": "過度的快取層",
    "Docker": "開發環境容器化增加複雜性",
    "TypeScript": "為 JavaScript 加了不必要的編譯步驟",
    "Clean Architecture": "為抽象而抽象",
    "Microservices": "這不是 Netflix",
    "ORM": "SQL 查詢的不必要抽象",
    "DI Container": "依賴注入的過度工程"
}
```

### 1.4 數據流設計

#### 核心數據流 (Command Line Mode)
```python
# 簡化的數據流
def process_flow(user_input: str) -> str:
    """
    核心數據流：用戶輸入 -> AI 響應 -> 工具調用 -> 最終輸出
    """
    context = user_input

    for step in range(MAX_STEPS):
        # LLM 處理
        ai_response = llm.call(context)

        # 提取工具調用
        tool_calls = extract_tool_calls(ai_response)

        if not tool_calls:
            return ai_response  # 終止條件

        # 執行工具
        for call in tool_calls:
            result = tools[call.name](call.input)
            context += f"\n工具結果: {result}"

    return "達到最大步驟限制"
```

#### Web 模式數據流
```javascript
// 前端 WebSocket 流
websocket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
        case 'thinking':
            showThinking(data.content);
            break;
        case 'response':
            addMessage('assistant', data.content);
            hideThinking();
            break;
        case 'error':
            showError(data.content);
            break;
    }
};
```

---

## 第 2 部分：詳細設計 (Detailed Design)

### 2.1 核心模組設計

#### 2.1.1 主入口 (main.py)
**職責**: 統一入口點，參數解析，模式分派
**行數限制**: < 30 行

```python
#!/usr/bin/env python3
"""OpenManus - 統一入口點"""

import argparse
from core.agent import Agent

def main():
    parser = argparse.ArgumentParser(description="OpenManus AI Agent")
    parser.add_argument("--prompt", help="直接執行提示")
    parser.add_argument("--config", default="config.yaml", help="配置檔案")
    parser.add_argument("--web", action="store_true", help="啟動 Web 模式")
    args = parser.parse_args()

    if args.web:
        from web.server import start_server
        start_server()
        return

    agent = Agent(args.config)

    if args.prompt:
        print(agent.process(args.prompt))
    else:
        # 互動模式
        while True:
            try:
                prompt = input("manus> ")
                if prompt.lower() in ['exit', 'quit', 'q']:
                    break
                print(agent.process(prompt))
            except KeyboardInterrupt:
                print("\n再見！")
                break

if __name__ == "__main__":
    main()
```

#### 2.1.2 核心 Agent (core/agent.py)
**職責**: 主要業務邏輯，LLM 交互，工具調度
**行數限制**: < 100 行

```python
import yaml
import importlib
from typing import Dict, Callable, List, Optional
from dataclasses import dataclass

@dataclass
class Config:
    """配置數據類 - 簡單的數據結構"""
    llm_model: str
    api_key: str
    max_tokens: int
    max_steps: int
    tools: List[str]

class Agent:
    """核心 Agent - 遵循單一職責原則"""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.llm = self._init_llm()
        self.tools = self._load_tools()

    def process(self, prompt: str) -> str:
        """核心處理邏輯 - 無特殊情況"""
        context = prompt

        for step in range(self.config.max_steps):
            response = self.llm.call(context)

            if tool_calls := self._extract_tool_calls(response):
                for call in tool_calls:
                    result = self.tools[call['name']](call['input'])
                    context += f"\n工具結果: {result}"
            else:
                return response

        return "達到最大步驟限制"

    def _load_config(self, path: str) -> Config:
        """載入配置 - 簡單直接"""
        with open(path) as f:
            data = yaml.safe_load(f)
        return Config(**data['agent'])

    def _load_tools(self) -> Dict[str, Callable]:
        """動態載入工具 - 零硬編碼"""
        tools = {}
        for tool_name in self.config.tools:
            module = importlib.import_module(f"tools.{tool_name}")
            tools[tool_name] = getattr(module, "execute")
        return tools
```

#### 2.1.3 LLM 封裝 (core/llm.py)
**職責**: OpenAI API 封裝，錯誤處理
**行數限制**: < 80 行

```python
import os
import json
from typing import List, Dict
import requests

class LLM:
    """LLM 封裝 - 簡單可靠"""

    def __init__(self, model: str, api_key: str, max_tokens: int):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.max_tokens = max_tokens
        self.base_url = "https://api.openai.com/v1"

    def call(self, prompt: str) -> str:
        """調用 LLM - 直接 HTTP 調用"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": 0.0
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        except Exception as e:
            return f"LLM 錯誤: {str(e)}"
```

### 2.2 工具系統設計

#### 2.2.1 工具管理器 (core/tools.py)
**職責**: 工具註冊，統一介面
**行數限制**: < 50 行

```python
from typing import Dict, Callable

# 全局工具註冊表 - 簡單的字典
TOOLS: Dict[str, Callable] = {}

def register_tool(name: str):
    """工具註冊裝飾器 - 統一註冊機制"""
    def decorator(func: Callable[[str], str]):
        TOOLS[name] = func
        return func
    return decorator

def get_tool(name: str) -> Callable:
    """獲取工具 - 簡單查找"""
    return TOOLS.get(name)

def list_tools() -> List[str]:
    """列出所有工具"""
    return list(TOOLS.keys())
```

#### 2.2.2 工具實現規範
**統一介面**: `execute(input: str) -> str`
**每個工具**: < 50 行

```python
# tools/python.py - Python 執行工具
import subprocess
import tempfile
import os

def execute(code: str) -> str:
    """執行 Python 代碼 - 安全沙盒"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            result = subprocess.run(
                ['python', f.name],
                capture_output=True,
                text=True,
                timeout=30
            )

            os.unlink(f.name)

            if result.returncode == 0:
                return result.stdout
            else:
                return f"錯誤: {result.stderr}"

    except Exception as e:
        return f"執行錯誤: {str(e)}"

# tools/browser.py - 瀏覽器工具
import requests

def execute(url: str) -> str:
    """獲取網頁內容 - 簡化版本"""
    try:
        response = requests.get(url, timeout=10)
        return response.text[:2000]  # 限制長度
    except Exception as e:
        return f"瀏覽錯誤: {str(e)}"

# tools/files.py - 文件工具
def execute(command: str) -> str:
    """文件操作 - read/write 命令"""
    parts = command.split(' ', 2)
    action = parts[0]

    if action == 'read' and len(parts) > 1:
        try:
            with open(parts[1], 'r') as f:
                return f.read()
        except Exception as e:
            return f"讀取錯誤: {str(e)}"

    elif action == 'write' and len(parts) > 2:
        try:
            with open(parts[1], 'w') as f:
                f.write(parts[2])
            return "寫入成功"
        except Exception as e:
            return f"寫入錯誤: {str(e)}"

    return "不支持的操作"
```

### 2.3 Web 界面設計

#### 2.3.1 Web 服務器 (web/server.py)
**職責**: WebSocket 服務，靜態文件服務
**行數限制**: < 50 行

```python
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
import uvicorn
import json

app = FastAPI()

# 服務靜態文件
app.mount("/", StaticFiles(directory="web/static", html=True), name="static")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端點 - 簡單通信"""
    await websocket.accept()

    from core.agent import Agent
    agent = Agent("config.yaml")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "prompt":
                prompt = message["content"]

                # 發送思考狀態
                await websocket.send_text(json.dumps({
                    "type": "thinking",
                    "content": "正在思考..."
                }))

                # 處理並響應
                result = agent.process(prompt)
                await websocket.send_text(json.dumps({
                    "type": "response",
                    "content": result
                }))

    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "content": str(e)
        }))

def start_server():
    """啟動服務器"""
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### 2.3.2 前端界面 (web/static/)
**技術**: 原生 HTML/CSS/JavaScript
**總行數**: < 400 行
**風格**: Hacker 主題黑色界面

```html
<!-- web/static/index.html -->
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenManus - AI Assistant</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>OpenManus AI Assistant</h1>
            <div class="status">
                <span id="connection-status">🔴 離線</span>
                <span id="token-usage">Token: 0/4000</span>
            </div>
        </header>

        <main id="chat-area">
            <div id="messages"></div>
            <div id="thinking" class="thinking hidden">
                <span class="thinking-text">思考中...</span>
            </div>
        </main>

        <footer id="input-area">
            <input id="message-input" placeholder="輸入你的問題..." autocomplete="off">
            <button id="send-btn">發送</button>
        </footer>
    </div>

    <script src="app.js"></script>
</body>
</html>
```

### 2.4 配置管理設計

#### 統一配置檔案 (config.yaml)
```yaml
# OpenManus 配置 - 唯一配置來源
agent:
  llm_model: "gpt-4"
  api_key: "${OPENAI_API_KEY}"  # 環境變數替換
  max_tokens: 4000
  max_steps: 10
  tools:
    - python
    - browser
    - files

workspace:
  path: "./workspace"
  auto_cleanup: true

web:
  host: "0.0.0.0"
  port: 8000
  static_dir: "web/static"

logging:
  level: "INFO"
  format: "simple"
```

---

## 第 3 部分：實施規範 (Implementation Guidelines)

### 3.1 代碼品質標準

#### Linus 式代碼檢查清單
```python
# 代碼審查檢查清單
CODE_REVIEW_CHECKLIST = {
    "no_special_cases": "沒有 if/elif 特殊情況處理",
    "single_responsibility": "每個函數只做一件事",
    "max_function_lines": "單函數不超過 20 行",
    "max_nesting": "嵌套深度不超過 3 層",
    "no_magic_numbers": "沒有魔術數字",
    "clear_naming": "變數和函數名稱清楚表達意圖",
    "no_comments_needed": "代碼自我解釋，不需要註釋",
    "uniform_interface": "所有同類型模組使用統一介面"
}
```

#### 禁止使用的模式
```python
# 設計模式黑名單
FORBIDDEN_PATTERNS = [
    "Singleton",           # 全域狀態問題
    "Factory Pattern",     # 不必要的抽象
    "Abstract Factory",    # 過度抽象
    "Observer Pattern",    # 複雜的事件系統
    "Strategy Pattern",    # 簡單的函數即可
    "Command Pattern",     # 函數即命令
    "Decorator Pattern",   # Python 有內建 decorator
]
```

### 3.2 性能要求

#### 響應時間標準
| 操作 | 目標時間 | 最大可接受時間 | 測量方法 |
| :--- | :--- | :--- | :--- |
| 系統啟動 | < 1 秒 | < 2 秒 | `time python main.py --prompt "test"` |
| 簡單查詢 | < 0.5 秒 | < 1 秒 | 不包含 LLM 調用的處理時間 |
| 工具執行 | < 0.5 秒 | < 2 秒 | Python 代碼執行、文件操作 |
| Web 響應 | < 0.1 秒 | < 0.5 秒 | 靜態文件服務響應時間 |

#### 資源使用標準
| 資源 | 目標 | 最大限制 | 監控方法 |
| :--- | :--- | :--- | :--- |
| 記憶體使用 | < 50MB | < 100MB | `ps` 命令監控 RSS |
| CPU 使用 | < 10% | < 50% | `top` 命令監控 |
| 磁盤空間 | < 10MB | < 50MB | 不包含工作區文件 |
| 網路連接 | 最小化 | < 10 併發 | 只有必要的 API 調用 |

### 3.3 錯誤處理策略

#### 統一錯誤處理
```python
# 錯誤處理原則
ERROR_HANDLING_PRINCIPLES = {
    "fail_fast": "問題發生時立即失敗，不隱藏錯誤",
    "clear_messages": "錯誤訊息對用戶友好且可行動",
    "no_silent_failures": "絕不默默忽略錯誤",
    "graceful_degradation": "部分功能失效時系統繼續運行",
    "recovery_hints": "提供解決問題的提示"
}

def handle_error(error: Exception, context: str) -> str:
    """統一錯誤處理 - 用戶友好的錯誤訊息"""
    error_map = {
        "ConnectionError": f"網路連接問題: {str(error)}",
        "TimeoutError": f"請求超時: {str(error)}",
        "FileNotFoundError": f"文件未找到: {str(error)}",
        "PermissionError": f"權限不足: {str(error)}",
    }

    error_type = type(error).__name__
    return error_map.get(error_type, f"{context} 錯誤: {str(error)}")
```

### 3.4 測試策略

#### 測試金字塔 (簡化版)
```python
# 測試優先級
TEST_STRATEGY = {
    "manual_testing": "70% - 手動功能測試",
    "integration_tests": "20% - 關鍵路徑集成測試",
    "unit_tests": "10% - 核心函數單元測試"
}

# 必須測試的功能
CRITICAL_TEST_CASES = [
    "main.py 基本啟動",
    "Agent.process() 核心邏輯",
    "工具動態載入",
    "配置檔案解析",
    "WebSocket 通信",
    "錯誤處理機制"
]
```

### 3.5 部署和運行

#### 環境要求
```python
SYSTEM_REQUIREMENTS = {
    "python_version": "3.11+",
    "memory_minimum": "512MB",
    "disk_space": "100MB",
    "network": "網際網路連接 (訪問 OpenAI API)"
}

DEPENDENCIES = [
    "fastapi",      # Web 框架 (WebSocket)
    "uvicorn",      # ASGI 服務器
    "pyyaml",       # 配置檔案解析
    "requests",     # HTTP 客戶端
]
```

#### 啟動腳本
```bash
#!/bin/bash
# scripts/start.sh - 簡單啟動腳本

echo "🚀 啟動 OpenManus..."

# 檢查 Python 版本
python_version=$(python --version 2>&1)
echo "Python 版本: $python_version"

# 檢查依賴
echo "檢查依賴..."
pip show fastapi pyyaml requests uvicorn > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 缺少依賴，正在安裝..."
    pip install -r requirements.txt
fi

# 檢查配置
if [ ! -f "config.yaml" ]; then
    echo "❌ 配置檔案不存在，創建範例配置..."
    cp config.example.yaml config.yaml
    echo "⚠️  請編輯 config.yaml 並設置 API 金鑰"
    exit 1
fi

# 啟動系統
echo "✅ 啟動 OpenManus..."
python main.py "$@"
```

---

**批准簽字**:
- Linus-style Tech Lead: ✅ 已批准 (2025-01-21)
- 核心開發團隊: ✅ 已批准 (2025-01-21)

**下一步**: 開始按照 [實施檢查清單](./implementation-checklist.md) 進行開發