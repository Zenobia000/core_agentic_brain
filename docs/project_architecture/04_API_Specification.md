# API 規格文件 (API Specification)
# Core Agentic Brain - API Reference v1.0

**文件版本:** 1.0
**日期:** 2026-01-27
**API 版本:** v1
**基礎 URL:** `http://localhost:8000/api`

---

## 概覽

Core Agentic Brain API 提供 RESTful 和 WebSocket 介面，支援 AI 對話、工具執行和系統管理功能。

### 認證

```http
Authorization: Bearer <token>
```

### 請求格式

- Content-Type: `application/json`
- Accept: `application/json`

### 響應格式

```json
{
  "status": "success|error",
  "data": {},
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description"
  },
  "metadata": {
    "timestamp": "2026-01-27T12:00:00Z",
    "version": "1.0"
  }
}
```

---

## REST API 端點

### 1. 對話 API

#### 1.1 發送訊息

發送訊息給 AI 並獲取回應。

**端點:** `POST /api/chat`

**請求:**

```json
{
  "message": "string",
  "session_id": "string (optional)",
  "context": {
    "max_tokens": 2000,
    "temperature": 0.7
  },
  "mode": "minimal|standard|enterprise"
}
```

**響應:**

```json
{
  "status": "success",
  "data": {
    "response": "AI response text",
    "session_id": "uuid",
    "tool_calls": [
      {
        "tool": "python",
        "result": {}
      }
    ],
    "metadata": {
      "tokens_used": 150,
      "execution_time": 1.2,
      "model": "gpt-4"
    }
  }
}
```

**錯誤碼:**

| 碼 | 描述 |
|---|------|
| 400 | 無效的請求參數 |
| 401 | 未授權 |
| 429 | 速率限制 |
| 500 | 內部錯誤 |

**範例:**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, what is 2+2?",
    "session_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

---

#### 1.2 獲取對話歷史

獲取指定會話的對話歷史。

**端點:** `GET /api/chat/history/{session_id}`

**參數:**

| 參數 | 類型 | 描述 |
|-----|------|------|
| session_id | string | 會話 ID |
| limit | int | 返回訊息數量（預設 20） |
| offset | int | 偏移量（預設 0） |

**響應:**

```json
{
  "status": "success",
  "data": {
    "session_id": "uuid",
    "messages": [
      {
        "id": "msg_001",
        "role": "user",
        "content": "Hello",
        "timestamp": "2026-01-27T12:00:00Z"
      },
      {
        "id": "msg_002",
        "role": "assistant",
        "content": "Hi there!",
        "timestamp": "2026-01-27T12:00:01Z"
      }
    ],
    "total": 42,
    "has_more": true
  }
}
```

---

#### 1.3 清除對話

清除指定會話的對話歷史。

**端點:** `DELETE /api/chat/history/{session_id}`

**響應:**

```json
{
  "status": "success",
  "data": {
    "message": "Session cleared",
    "session_id": "uuid"
  }
}
```

---

### 2. 工具 API

#### 2.1 列出可用工具

獲取所有可用的工具列表。

**端點:** `GET /api/tools`

**響應:**

```json
{
  "status": "success",
  "data": {
    "tools": [
      {
        "name": "python",
        "description": "Execute Python code",
        "enabled": true,
        "parameters": {
          "type": "object",
          "properties": {
            "code": {
              "type": "string",
              "description": "Python code to execute"
            }
          },
          "required": ["code"]
        }
      },
      {
        "name": "files",
        "description": "File system operations",
        "enabled": true,
        "parameters": {}
      }
    ]
  }
}
```

---

#### 2.2 執行工具

直接執行指定的工具。

**端點:** `POST /api/tools/{tool_name}/execute`

**請求:**

```json
{
  "parameters": {
    "code": "print('Hello, World!')"
  },
  "timeout": 30
}
```

**響應:**

```json
{
  "status": "success",
  "data": {
    "tool": "python",
    "result": {
      "success": true,
      "output": "Hello, World!\n"
    },
    "execution_time": 0.05
  }
}
```

**錯誤碼:**

| 碼 | 描述 |
|---|------|
| 404 | 工具不存在 |
| 403 | 權限不足 |
| 408 | 執行超時 |

---

#### 2.3 獲取工具詳情

獲取特定工具的詳細資訊。

**端點:** `GET /api/tools/{tool_name}`

**響應:**

```json
{
  "status": "success",
  "data": {
    "name": "python",
    "description": "Execute Python code in a sandboxed environment",
    "version": "1.0",
    "enabled": true,
    "permissions": ["execute", "read"],
    "limits": {
      "max_execution_time": 30,
      "max_memory": "100MB"
    },
    "statistics": {
      "total_executions": 1234,
      "average_execution_time": 0.8,
      "success_rate": 0.95
    }
  }
}
```

---

### 3. 系統 API

#### 3.1 健康檢查

檢查系統健康狀態。

**端點:** `GET /api/health`

**響應:**

```json
{
  "status": "success",
  "data": {
    "healthy": true,
    "components": {
      "core": "healthy",
      "llm": "healthy",
      "tools": "healthy",
      "router": "healthy"
    },
    "version": "1.0.0",
    "uptime": 3600,
    "timestamp": "2026-01-27T12:00:00Z"
  }
}
```

---

#### 3.2 系統狀態

獲取詳細的系統狀態資訊。

**端點:** `GET /api/status`

**響應:**

```json
{
  "status": "success",
  "data": {
    "mode": "standard",
    "features": {
      "routing": true,
      "permissions": false,
      "audit": false,
      "mcp": false
    },
    "metrics": {
      "active_sessions": 5,
      "total_requests": 10234,
      "average_response_time": 1.2,
      "memory_usage": "85MB",
      "cpu_usage": "12%"
    },
    "limits": {
      "max_sessions": 100,
      "rate_limit": "100/min"
    }
  }
}
```

---

#### 3.3 系統配置

獲取或更新系統配置。

**端點:** `GET /api/config`

**響應:**

```json
{
  "status": "success",
  "data": {
    "mode": "standard",
    "core": {
      "llm": {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.7
      },
      "tools": {
        "enabled": ["python", "files", "browser"]
      }
    },
    "routing": {
      "enabled": true,
      "fast_path_threshold": 1000
    }
  }
}
```

**端點:** `PATCH /api/config`

**請求:**

```json
{
  "mode": "enterprise",
  "core": {
    "llm": {
      "temperature": 0.5
    }
  }
}
```

**響應:**

```json
{
  "status": "success",
  "data": {
    "message": "Configuration updated",
    "changes": ["mode", "core.llm.temperature"]
  }
}
```

---

### 4. 會話管理 API

#### 4.1 創建會話

創建新的對話會話。

**端點:** `POST /api/sessions`

**請求:**

```json
{
  "name": "Project Discussion",
  "metadata": {
    "project": "core-brain",
    "user": "developer"
  }
}
```

**響應:**

```json
{
  "status": "success",
  "data": {
    "session_id": "uuid",
    "name": "Project Discussion",
    "created_at": "2026-01-27T12:00:00Z",
    "metadata": {}
  }
}
```

---

#### 4.2 列出會話

獲取所有活動會話。

**端點:** `GET /api/sessions`

**參數:**

| 參數 | 類型 | 描述 |
|-----|------|------|
| active | boolean | 只返回活動會話 |
| limit | int | 限制數量 |
| sort | string | 排序方式 (created_at, last_activity) |

**響應:**

```json
{
  "status": "success",
  "data": {
    "sessions": [
      {
        "session_id": "uuid1",
        "name": "Session 1",
        "created_at": "2026-01-27T10:00:00Z",
        "last_activity": "2026-01-27T11:30:00Z",
        "message_count": 15
      }
    ],
    "total": 3
  }
}
```

---

#### 4.3 刪除會話

刪除指定的會話。

**端點:** `DELETE /api/sessions/{session_id}`

**響應:**

```json
{
  "status": "success",
  "data": {
    "message": "Session deleted",
    "session_id": "uuid"
  }
}
```

---

### 5. 路由 API (Standard/Enterprise)

#### 5.1 分析任務

分析任務複雜度並獲取路由建議。

**端點:** `POST /api/routing/analyze`

**請求:**

```json
{
  "task": "Create a Python function to sort a list",
  "context": {
    "history_length": 5,
    "tool_calls": 2
  }
}
```

**響應:**

```json
{
  "status": "success",
  "data": {
    "path": "agent",
    "complexity_score": 0.7,
    "estimated_time": 5.2,
    "recommended_agents": ["planner", "executor"],
    "reasoning": "Task requires planning and code generation"
  }
}
```

---

### 6. 權限 API (Enterprise)

#### 6.1 檢查權限

檢查特定操作的權限。

**端點:** `POST /api/permissions/check`

**請求:**

```json
{
  "action": "tool:python:execute",
  "context": {
    "user": "user123",
    "resource": "project_files"
  }
}
```

**響應:**

```json
{
  "status": "success",
  "data": {
    "allowed": true,
    "level": "allow",
    "reason": "User has execute permission for Python tool"
  }
}
```

---

#### 6.2 列出權限規則

獲取所有權限規則。

**端點:** `GET /api/permissions/rules`

**響應:**

```json
{
  "status": "success",
  "data": {
    "rules": [
      {
        "id": "rule_001",
        "pattern": "tool:*:execute",
        "level": "ask",
        "conditions": [],
        "description": "Require confirmation for tool execution"
      }
    ]
  }
}
```

---

## WebSocket API

### 1. 即時對話

建立 WebSocket 連接進行即時對話。

**端點:** `WS /ws/chat`

#### 連接

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');
```

#### 訊息格式

**客戶端發送:**

```json
{
  "type": "message",
  "content": "Hello, AI!",
  "session_id": "uuid"
}
```

**服務端響應:**

```json
{
  "type": "response",
  "content": "Hello! How can I help you?",
  "session_id": "uuid",
  "timestamp": "2026-01-27T12:00:00Z"
}
```

**工具執行通知:**

```json
{
  "type": "tool_execution",
  "tool": "python",
  "status": "running|completed|failed",
  "result": {}
}
```

**錯誤訊息:**

```json
{
  "type": "error",
  "code": "ERROR_CODE",
  "message": "Error description"
}
```

#### 心跳機制

```json
{
  "type": "ping"
}
```

```json
{
  "type": "pong"
}
```

---

### 2. 事件串流

訂閱系統事件串流。

**端點:** `WS /ws/events`

#### 事件類型

```json
{
  "type": "session_created",
  "data": {
    "session_id": "uuid",
    "timestamp": "2026-01-27T12:00:00Z"
  }
}
```

```json
{
  "type": "tool_executed",
  "data": {
    "tool": "python",
    "duration": 1.2,
    "success": true
  }
}
```

```json
{
  "type": "error_occurred",
  "data": {
    "error": "LLM timeout",
    "severity": "warning"
  }
}
```

---

## 錯誤處理

### 錯誤格式

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request parameters are invalid",
    "details": {
      "field": "message",
      "reason": "Required field is missing"
    },
    "request_id": "req_123456"
  }
}
```

### 錯誤碼列表

| 錯誤碼 | HTTP 狀態 | 描述 |
|-------|-----------|------|
| INVALID_REQUEST | 400 | 請求參數無效 |
| UNAUTHORIZED | 401 | 未授權的請求 |
| FORBIDDEN | 403 | 權限不足 |
| NOT_FOUND | 404 | 資源不存在 |
| METHOD_NOT_ALLOWED | 405 | 方法不允許 |
| TIMEOUT | 408 | 請求超時 |
| CONFLICT | 409 | 資源衝突 |
| RATE_LIMITED | 429 | 超過速率限制 |
| INTERNAL_ERROR | 500 | 內部伺服器錯誤 |
| SERVICE_UNAVAILABLE | 503 | 服務暫時不可用 |

---

## 速率限制

### 限制規則

| 端點 | 限制 | 時間窗口 |
|------|------|----------|
| /api/chat | 100 | 1 分鐘 |
| /api/tools/*/execute | 50 | 1 分鐘 |
| /api/config | 10 | 1 分鐘 |
| WebSocket | 1000 訊息 | 1 分鐘 |

### 響應標頭

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1706355600
```

### 超限響應

```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded",
    "retry_after": 30
  }
}
```

---

## SDK 範例

### Python SDK

```python
from core_brain import Client

# 初始化客戶端
client = Client(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# 發送訊息
response = client.chat(
    message="Hello, what's the weather?",
    session_id="my-session"
)
print(response.content)

# 執行工具
result = client.execute_tool(
    tool="python",
    parameters={"code": "print('Hello')"}
)
print(result.output)

# WebSocket 對話
async with client.ws_chat() as ws:
    await ws.send("Hello")
    response = await ws.receive()
    print(response)
```

### JavaScript SDK

```javascript
import { CoreBrainClient } from '@core-brain/sdk';

// 初始化客戶端
const client = new CoreBrainClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key'
});

// 發送訊息
const response = await client.chat({
  message: 'Hello, what is 2+2?',
  sessionId: 'my-session'
});
console.log(response.content);

// WebSocket 連接
const ws = client.connectWebSocket();

ws.on('message', (data) => {
  console.log('Received:', data);
});

ws.send({
  type: 'message',
  content: 'Hello, AI!'
});
```

### cURL 範例

```bash
# 基本對話
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "What is the capital of France?"
  }'

# 執行工具
curl -X POST http://localhost:8000/api/tools/python/execute \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "code": "import datetime; print(datetime.datetime.now())"
    }
  }'

# 獲取系統狀態
curl http://localhost:8000/api/status
```

---

## API 版本控制

### 版本策略

- 當前版本: `v1`
- 版本格式: `/api/v{version}/endpoint`
- 預設版本: 最新穩定版

### 版本標頭

```http
API-Version: v1
```

### 棄用政策

- 棄用通知: 至少 3 個月前
- 支援期限: 棄用後 6 個月
- 遷移指南: 提供詳細文檔

---

## 安全性

### 認證方式

1. **API Key**
   ```http
   X-API-Key: your-api-key
   ```

2. **Bearer Token**
   ```http
   Authorization: Bearer your-jwt-token
   ```

3. **Session Cookie**
   ```http
   Cookie: session_id=uuid
   ```

### CORS 設定

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, X-API-Key
```

### 安全標頭

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

---

## 測試環境

### 測試伺服器

- URL: `https://api-test.core-brain.dev`
- 認證: 使用測試 API Key

### 測試資料

```json
{
  "test_session_id": "test-123e4567-e89b",
  "test_api_key": "test_key_abc123"
}
```

### Postman Collection

下載 [Core Brain API.postman_collection.json](https://example.com/postman)

---

## 變更日誌

### v1.0.0 (2026-01-27)
- 初始版本發布
- 基本對話 API
- 工具執行 API
- WebSocket 支援

### 即將推出 (v1.1.0)
- GraphQL 支援
- 批次請求
- 串流響應
- 檔案上傳

---

## 聯繫與支援

- 文檔: https://docs.core-brain.dev
- GitHub: https://github.com/org/core-agentic-brain
- 問題回報: https://github.com/org/core-agentic-brain/issues
- Email: api-support@core-brain.dev

---

**文檔狀態:** 已發布
**最後更新:** 2026-01-27
**維護者:** API 團隊