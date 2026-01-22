# API 設計規格書 - OpenManus Linus 式重構

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2025-01-21`
**主要作者 (Lead Author):** `API 設計師 & Linus-style 架構師`
**審核者 (Reviewers):** `Tech Lead, 前端開發者`
**狀態 (Status):** `已批准 (Approved)`

---

## 目錄 (Table of Contents)

1. [API 設計原則 (API Design Principles)](#第-1-部分api-設計原則-api-design-principles)
2. [WebSocket API 規格 (WebSocket API Specification)](#第-2-部分websocket-api-規格-websocket-api-specification)
3. [HTTP API 規格 (HTTP API Specification)](#第-3-部分http-api-規格-http-api-specification)
4. [命令行接口規格 (CLI Interface Specification)](#第-4-部分命令行接口規格-cli-interface-specification)
5. [工具接口規格 (Tool Interface Specification)](#第-5-部分工具接口規格-tool-interface-specification)

---

**目的**: 定義 OpenManus 系統的所有接口規格，確保接口設計遵循 Linus 式簡潔原則，提供清晰、一致、易用的 API。

---

## 第 1 部分：API 設計原則 (API Design Principles)

### 1.1 Linus 式 API 哲學

#### 核心原則
> **"好的 API 是顯而易見的。偉大的 API 是讓人感覺這就是它應該的樣子。"**

| 設計原則 | 具體應用 | 反例 (避免) |
| :--- | :--- | :--- |
| **一致性** | 所有接口使用相同的錯誤格式 | 不同接口不同的錯誤結構 |
| **簡潔性** | 最少的參數完成任務 | 過度參數化的接口 |
| **可預測性** | 相同輸入總是相同輸出 | 有副作用的查詢接口 |
| **自我解釋** | 接口名稱清楚表達功能 | 需要文檔才能理解的接口 |

#### API 設計約束
```python
API_DESIGN_CONSTRAINTS = {
    "max_endpoint_count": 10,      # 最多 10 個端點
    "max_parameters": 5,           # 單個接口最多 5 個參數
    "response_time_target": "1s",  # 響應時間目標
    "error_message_length": 200,   # 錯誤消息最大長度
}
```

### 1.2 統一的錯誤處理

#### 錯誤響應格式
```json
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "message": "用戶友好的錯誤描述",
    "details": "技術細節（可選）",
    "suggestion": "解決建議（可選）"
  },
  "timestamp": "2025-01-21T10:30:00Z"
}
```

#### 標準錯誤類型
```python
STANDARD_ERROR_TYPES = {
    "ValidationError": "輸入驗證失敗",
    "AuthenticationError": "認證失敗",
    "RateLimitError": "請求頻率超限",
    "InternalError": "內部服務錯誤",
    "NetworkError": "網路連接問題",
    "TimeoutError": "請求超時",
    "NotFoundError": "資源不存在",
}
```

### 1.3 統一的成功響應格式

#### 標準成功響應
```json
{
  "success": true,
  "data": {
    // 實際響應數據
  },
  "metadata": {
    "timestamp": "2025-01-21T10:30:00Z",
    "version": "1.0",
    "request_id": "req_123456"
  }
}
```

---

## 第 2 部分：WebSocket API 規格 (WebSocket API Specification)

### 2.1 WebSocket 連接

#### 連接端點
```
ws://localhost:8000/ws
```

#### 連接生命週期
```javascript
// 連接建立
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    console.log('✅ WebSocket 已連接');
    // 連接成功，可以發送消息
};

ws.onclose = (event) => {
    console.log('❌ WebSocket 已斷開', event.code, event.reason);
    // 實施重連邏輯
};

ws.onerror = (error) => {
    console.log('🚨 WebSocket 錯誤', error);
};
```

### 2.2 消息格式規格

#### 2.2.1 客戶端到服務器消息

**聊天消息**
```json
{
  "type": "chat",
  "content": "用戶輸入的消息內容",
  "metadata": {
    "timestamp": "2025-01-21T10:30:00Z",
    "session_id": "optional_session_id"
  }
}
```

**系統命令**
```json
{
  "type": "command",
  "command": "status|reset|stop",
  "parameters": {}
}
```

#### 2.2.2 服務器到客戶端消息

**思考狀態更新**
```json
{
  "type": "thinking",
  "content": "正在分析您的問題...",
  "metadata": {
    "timestamp": "2025-01-21T10:30:00Z",
    "step": 1,
    "total_steps": 3
  }
}
```

**AI 回應**
```json
{
  "type": "response",
  "content": "AI 的回應內容",
  "metadata": {
    "timestamp": "2025-01-21T10:30:00Z",
    "tokens_used": 150,
    "response_time_ms": 1200
  }
}
```

**工具執行通知**
```json
{
  "type": "tool_execution",
  "tool_name": "python",
  "status": "running|completed|failed",
  "input": "print('hello')",
  "output": "hello\n",
  "metadata": {
    "execution_time_ms": 500,
    "timestamp": "2025-01-21T10:30:00Z"
  }
}
```

**錯誤消息**
```json
{
  "type": "error",
  "error": {
    "type": "NetworkError",
    "message": "無法連接到 LLM 服務",
    "suggestion": "請檢查網路連接並稍後重試"
  },
  "metadata": {
    "timestamp": "2025-01-21T10:30:00Z"
  }
}
```

**系統狀態**
```json
{
  "type": "status",
  "status": {
    "connection": "connected|disconnected",
    "ai_service": "available|unavailable",
    "tools_loaded": ["python", "browser", "files"],
    "memory_usage": "45MB"
  },
  "metadata": {
    "timestamp": "2025-01-21T10:30:00Z"
  }
}
```

### 2.3 WebSocket 流程示例

#### 典型對話流程
```javascript
// 1. 客戶端發送聊天消息
ws.send(JSON.stringify({
    type: "chat",
    content: "請用 Python 計算 2+2"
}));

// 2. 服務器發送思考狀態
// <- { type: "thinking", content: "正在分析您的請求..." }

// 3. 服務器發送工具執行通知
// <- { type: "tool_execution", tool_name: "python", status: "running" }

// 4. 服務器發送工具執行結果
// <- { type: "tool_execution", tool_name: "python", status: "completed", output: "4" }

// 5. 服務器發送最終回應
// <- { type: "response", content: "計算結果是 4" }
```

---

## 第 3 部分：HTTP API 規格 (HTTP API Specification)

### 3.1 基礎信息

#### 基礎 URL
```
http://localhost:8000/api/v1
```

#### 通用 HTTP 標頭
```http
Content-Type: application/json
Accept: application/json
User-Agent: OpenManus-Client/1.0
```

### 3.2 端點規格

#### 3.2.1 健康檢查
```http
GET /api/v1/health
```

**響應**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "components": {
      "ai_service": "available",
      "tools": "loaded",
      "websocket": "ready"
    },
    "uptime_seconds": 3600
  }
}
```

#### 3.2.2 系統信息
```http
GET /api/v1/info
```

**響應**:
```json
{
  "success": true,
  "data": {
    "name": "OpenManus",
    "version": "1.0.0",
    "description": "Linus-style AI Agent System",
    "capabilities": {
      "tools": ["python", "browser", "files"],
      "interfaces": ["cli", "web", "api"],
      "models_supported": ["gpt-4", "gpt-3.5-turbo"]
    },
    "limits": {
      "max_tokens": 4000,
      "max_steps": 10,
      "timeout_seconds": 30
    }
  }
}
```

#### 3.2.3 工具列表
```http
GET /api/v1/tools
```

**響應**:
```json
{
  "success": true,
  "data": {
    "tools": [
      {
        "name": "python",
        "description": "執行 Python 代碼",
        "version": "1.0",
        "status": "available"
      },
      {
        "name": "browser",
        "description": "獲取網頁內容",
        "version": "1.0",
        "status": "available"
      },
      {
        "name": "files",
        "description": "文件讀寫操作",
        "version": "1.0",
        "status": "available"
      }
    ]
  }
}
```

#### 3.2.4 單次聊天（同步）
```http
POST /api/v1/chat/sync
```

**請求**:
```json
{
  "message": "用戶輸入的消息",
  "config": {
    "max_tokens": 2000,
    "temperature": 0.0,
    "tools_enabled": ["python", "files"]
  }
}
```

**響應**:
```json
{
  "success": true,
  "data": {
    "response": "AI 的回應",
    "execution_log": [
      {
        "step": 1,
        "action": "thinking",
        "content": "分析用戶請求"
      },
      {
        "step": 2,
        "action": "tool_call",
        "tool": "python",
        "input": "print(2+2)",
        "output": "4"
      }
    ],
    "metadata": {
      "tokens_used": 150,
      "execution_time_ms": 1500,
      "tools_used": ["python"]
    }
  }
}
```

#### 3.2.5 配置管理
```http
GET /api/v1/config
```

**響應**:
```json
{
  "success": true,
  "data": {
    "agent": {
      "max_tokens": 4000,
      "max_steps": 10,
      "tools": ["python", "browser", "files"]
    },
    "workspace": {
      "path": "./workspace"
    }
  }
}
```

```http
PUT /api/v1/config
```

**請求**:
```json
{
  "agent": {
    "max_tokens": 3000,
    "max_steps": 8
  }
}
```

### 3.3 錯誤響應示例

#### 4xx 客戶端錯誤
```json
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "message": "請求參數無效",
    "details": "message 欄位不能為空",
    "suggestion": "請提供有效的消息內容"
  },
  "metadata": {
    "timestamp": "2025-01-21T10:30:00Z",
    "request_id": "req_123456"
  }
}
```

#### 5xx 服務器錯誤
```json
{
  "success": false,
  "error": {
    "type": "InternalError",
    "message": "AI 服務暫時不可用",
    "suggestion": "請稍後重試或聯繫管理員"
  },
  "metadata": {
    "timestamp": "2025-01-21T10:30:00Z",
    "request_id": "req_123456"
  }
}
```

---

## 第 4 部分：命令行接口規格 (CLI Interface Specification)

### 4.1 基本命令格式

#### 主命令
```bash
python main.py [OPTIONS] [COMMAND]
```

#### 全局選項
```bash
Options:
  --config PATH     配置檔案路徑 [default: config.yaml]
  --verbose, -v     詳細輸出
  --quiet, -q       靜默模式
  --help, -h        顯示幫助信息
  --version         顯示版本信息
```

### 4.2 執行模式

#### 4.2.1 互動模式（默認）
```bash
$ python main.py
OpenManus AI Assistant v1.0
Type 'help' for commands, 'exit' to quit.

manus> 你好
你好！我是 OpenManus AI 助手。我可以幫你執行 Python 代碼、瀏覽網頁內容、操作文件等。有什麼我可以幫助你的嗎？

manus> exit
再見！
```

#### 4.2.2 直接執行模式
```bash
$ python main.py --prompt "計算 2+2"
正在處理您的請求...
計算結果是 4。

$ echo "寫一個 hello world 程序" | python main.py --prompt -
正在處理您的請求...
以下是一個簡單的 Python Hello World 程序：

print("Hello, World!")

我已經為您執行了這個程序：
Hello, World!
```

#### 4.2.3 Web 模式
```bash
$ python main.py --web
🚀 啟動 OpenManus Web 服務...
✅ 服務器運行於: http://localhost:8000
✅ WebSocket 端點: ws://localhost:8000/ws
📖 按 Ctrl+C 停止服務

2025-01-21 10:30:00 - INFO - Web 服務已啟動
2025-01-21 10:30:15 - INFO - WebSocket 連接: 127.0.0.1
```

### 4.3 互動模式命令

#### 內建命令
```bash
manus> help
可用命令:
  help              顯示此幫助信息
  status            顯示系統狀態
  tools             列出可用工具
  config            顯示當前配置
  history           顯示對話歷史
  clear             清除屏幕
  reset             重置對話上下文
  exit, quit        退出程序

manus> status
系統狀態:
✅ AI 服務: 可用 (gpt-4)
✅ 工具: python, browser, files
💾 記憶體使用: 45MB
⚡ 響應時間: 平均 1.2s

manus> tools
可用工具:
🐍 python    - 執行 Python 代碼
🌐 browser   - 獲取網頁內容
📁 files     - 文件讀寫操作

manus> config
當前配置:
  模型: gpt-4
  最大 Token: 4000
  最大步驟: 10
  工作區: ./workspace
```

### 4.4 退出碼

#### 標準退出碼
```python
EXIT_CODES = {
    0: "成功執行",
    1: "一般錯誤",
    2: "配置錯誤",
    3: "網路錯誤",
    4: "認證錯誤",
    5: "工具執行錯誤",
    130: "用戶中斷 (Ctrl+C)"
}
```

### 4.5 環境變數

#### 支持的環境變數
```bash
# API 配置
OPENAI_API_KEY=sk-...           # OpenAI API 金鑰
OPENMANUS_CONFIG=config.yaml    # 配置檔案路徑

# 行為配置
OPENMANUS_WORKSPACE=./workspace # 工作區目錄
OPENMANUS_LOG_LEVEL=INFO       # 日誌級別
OPENMANUS_TIMEOUT=30           # 超時設定（秒）

# Web 模式配置
OPENMANUS_HOST=0.0.0.0         # Web 服務主機
OPENMANUS_PORT=8000            # Web 服務端口
```

---

## 第 5 部分：工具接口規格 (Tool Interface Specification)

### 5.1 統一工具接口

#### 核心接口定義
```python
def execute(input_str: str) -> str:
    """
    統一工具接口

    Args:
        input_str: 工具輸入（字符串格式）

    Returns:
        str: 工具執行結果（字符串格式）

    Raises:
        ToolExecutionError: 工具執行失敗時拋出
    """
    pass
```

#### 工具元數據
```python
TOOL_METADATA = {
    "name": "tool_name",
    "version": "1.0.0",
    "description": "工具功能描述",
    "input_format": "輸入格式說明",
    "output_format": "輸出格式說明",
    "examples": [
        {
            "input": "示例輸入",
            "output": "示例輸出"
        }
    ]
}
```

### 5.2 內建工具規格

#### 5.2.1 Python 工具 (tools/python.py)

**功能**: 執行 Python 代碼並返回結果

**輸入格式**:
```python
# 直接 Python 代碼
input_str = "print('Hello World')"

# 或者多行代碼
input_str = """
import math
result = math.sqrt(16)
print(f"Square root of 16 is {result}")
"""
```

**輸出格式**:
```python
# 成功執行
"Hello World\n"

# 執行錯誤
"錯誤: NameError: name 'undefined_var' is not defined"

# 執行超時
"執行錯誤: 代碼執行超時 (30秒)"
```

**限制**:
- 最大執行時間: 30 秒
- 不允許危險操作 (文件系統寫入需謹慎)
- 沙盒環境執行

#### 5.2.2 Browser 工具 (tools/browser.py)

**功能**: 獲取網頁內容

**輸入格式**:
```python
# 基本 URL
input_str = "https://example.com"

# 帶參數的請求
input_str = "https://api.example.com/data"
```

**輸出格式**:
```python
# 成功獲取
"<html><head><title>Example</title></head>...</html>"  # 限制前2000字符

# 網路錯誤
"瀏覽錯誤: Connection timeout"

# 不支持的 URL
"瀏覽錯誤: 不支持的協議"
```

**限制**:
- 超時時間: 10 秒
- 內容長度: 最多 2000 字符
- 僅支持 HTTP/HTTPS

#### 5.2.3 Files 工具 (tools/files.py)

**功能**: 文件讀寫操作

**輸入格式**:
```python
# 讀取文件
input_str = "read /path/to/file.txt"

# 寫入文件
input_str = "write /path/to/file.txt 文件內容"

# 列出目錄
input_str = "list /path/to/directory"
```

**輸出格式**:
```python
# 讀取成功
"文件內容..."

# 寫入成功
"寫入成功"

# 文件不存在
"讀取錯誤: 文件不存在"

# 權限錯誤
"寫入錯誤: 權限不足"
```

### 5.3 自定義工具開發

#### 工具模板
```python
# tools/custom_tool.py
def execute(input_str: str) -> str:
    """
    自定義工具實現

    Args:
        input_str: 用戶輸入

    Returns:
        str: 執行結果
    """
    try:
        # 解析輸入
        parsed_input = parse_input(input_str)

        # 執行邏輯
        result = perform_operation(parsed_input)

        # 返回結果
        return format_output(result)

    except Exception as e:
        return f"工具執行錯誤: {str(e)}"

def parse_input(input_str: str):
    """解析輸入參數"""
    # 實現輸入解析邏輯
    pass

def perform_operation(parsed_input):
    """執行核心操作"""
    # 實現工具核心邏輯
    pass

def format_output(result):
    """格式化輸出"""
    # 格式化結果為字符串
    pass
```

#### 工具註冊
```python
# 在 config.yaml 中註冊新工具
agent:
  tools:
    - python
    - browser
    - files
    - custom_tool  # 新增的自定義工具
```

### 5.4 工具執行流程

#### 工具調用序列
```python
# 1. 工具發現
available_tools = load_tools_from_config()

# 2. 工具載入
tool_function = importlib.import_module(f"tools.{tool_name}").execute

# 3. 工具執行
try:
    result = tool_function(input_str)
    return f"工具執行成功: {result}"
except Exception as e:
    return f"工具執行失敗: {str(e)}"
```

#### 錯誤處理標準
```python
TOOL_ERROR_HANDLING = {
    "timeout": "工具執行超時，請檢查輸入或稍後重試",
    "permission": "權限不足，請檢查文件權限或運行權限",
    "network": "網路連接問題，請檢查網路設置",
    "validation": "輸入格式不正確，請參考工具使用說明",
    "resource": "資源不足，請釋放系統資源後重試"
}
```

---

## API 使用示例

### WebSocket 完整對話示例
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    // 發送聊天請求
    ws.send(JSON.stringify({
        type: "chat",
        content: "請用 Python 計算斐波那契數列的前 10 項"
    }));
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    switch (message.type) {
        case 'thinking':
            console.log('🤔', message.content);
            break;
        case 'tool_execution':
            console.log('🛠️', message.tool_name, message.status);
            if (message.output) {
                console.log('📤', message.output);
            }
            break;
        case 'response':
            console.log('💬', message.content);
            break;
        case 'error':
            console.error('❌', message.error.message);
            break;
    }
};
```

### HTTP API 使用示例
```python
import requests

# 健康檢查
response = requests.get('http://localhost:8000/api/v1/health')
print(response.json())

# 同步聊天
response = requests.post('http://localhost:8000/api/v1/chat/sync', json={
    'message': '今天天氣如何？',
    'config': {
        'max_tokens': 1000,
        'tools_enabled': ['browser']
    }
})
print(response.json())
```

---

**批准簽字**:
- API 設計師: ✅ 已批准 (2025-01-21)
- Tech Lead: ✅ 已批准 (2025-01-21)
- 前端開發者: ✅ 已批准 (2025-01-21)

**API 版本**: v1.0
**向後兼容承諾**: 在 v2.0 之前保持 API 穩定性