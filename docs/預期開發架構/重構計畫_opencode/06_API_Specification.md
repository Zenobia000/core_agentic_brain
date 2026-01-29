# OpenCode Agent Platform - API 規格文檔

**API 版本:** v1.0
**文檔版本:** 1.0
**日期:** 2026-01-22
**專案:** OpenCode Universal Agent Platform
**作者:** API 設計團隊

---

## 📋 API 概覽

### 基礎資訊

```yaml
Base URL: https://api.opencode.ai/v1
Protocol: HTTP/1.1, HTTP/2, WebSocket
Authentication: JWT Bearer Token
Content-Type: application/json
Rate Limit: 1000 requests/hour per user
```

### API 端點總覽

| 分類 | 端點 | 描述 |
|------|------|------|
| 認證 | `/auth/*` | 使用者認證與授權 |
| 會話 | `/sessions/*` | 會話管理 |
| 任務 | `/tasks/*` | 任務處理與追蹤 |
| Agent | `/agents/*` | AI Agent 管理 |
| 工具 | `/tools/*` | MCP 工具管理 |
| 配置 | `/config/*` | 系統配置 |
| 監控 | `/monitoring/*` | 系統監控與指標 |
| WebSocket | `/ws/*` | 即時通訊 |

---

## 🔐 認證與授權

### JWT Token 結構

```typescript
interface JWTPayload {
  sub: string          // 使用者 ID
  iat: number         // 發行時間
  exp: number         // 過期時間
  iss: string         // 發行者
  permissions: string[] // 權限列表
  sessionId?: string  // 會話 ID (可選)
}

// 使用方式
Authorization: Bearer <jwt_token>
```

### 權限系統

```typescript
enum Permission {
  // 會話權限
  'session:read' = 'session:read',
  'session:create' = 'session:create',
  'session:delete' = 'session:delete',

  // 任務權限
  'task:submit' = 'task:submit',
  'task:read' = 'task:read',
  'task:cancel' = 'task:cancel',

  // Agent 權限
  'agent:read' = 'agent:read',
  'agent:create' = 'agent:create',
  'agent:configure' = 'agent:configure',

  // 工具權限
  'tool:read' = 'tool:read',
  'tool:execute' = 'tool:execute',

  // 配置權限
  'config:read' = 'config:read',
  'config:write' = 'config:write',

  // 管理員權限
  'admin:monitoring' = 'admin:monitoring',
  'admin:users' = 'admin:users'
}
```

---

## 👤 認證 API

### POST /auth/login
使用者登入

```typescript
// Request
interface LoginRequest {
  email: string
  password: string
  remember?: boolean
}

// Response
interface LoginResponse {
  success: boolean
  data: {
    token: string
    refreshToken: string
    expiresIn: number
    user: {
      id: string
      email: string
      name: string
      avatar?: string
      permissions: Permission[]
    }
  }
}

// Example
POST /auth/login
{
  "email": "user@example.com",
  "password": "secure_password"
}

// Response 200 OK
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "rt_abc123...",
    "expiresIn": 3600,
    "user": {
      "id": "user_123",
      "email": "user@example.com",
      "name": "John Doe",
      "permissions": ["session:create", "task:submit"]
    }
  }
}
```

### POST /auth/refresh
刷新 Token

```typescript
// Request
interface RefreshRequest {
  refreshToken: string
}

// Response
interface RefreshResponse {
  success: boolean
  data: {
    token: string
    expiresIn: number
  }
}
```

### POST /auth/logout
使用者登出

```typescript
// Request - 僅需 Authorization header

// Response
interface LogoutResponse {
  success: boolean
  message: string
}
```

---

## 📚 會話管理 API

### GET /sessions
獲取會話列表

```typescript
// Query Parameters
interface SessionsQuery {
  page?: number        // 頁碼 (預設: 1)
  limit?: number       // 每頁數量 (預設: 20)
  status?: 'active' | 'completed' | 'error'
  agent?: string       // 過濾特定 agent
  search?: string      // 搜尋關鍵字
}

// Response
interface SessionsResponse {
  success: boolean
  data: {
    sessions: Session[]
    pagination: {
      total: number
      page: number
      limit: number
      totalPages: number
    }
  }
}

interface Session {
  id: string
  name: string
  status: 'active' | 'completed' | 'error'
  agent: {
    id: string
    name: string
    type: 'build' | 'plan' | 'general'
  }
  createdAt: string
  updatedAt: string
  lastActivity: string
  taskCount: number
  metadata: Record<string, any>
}

// Example
GET /sessions?page=1&limit=10&status=active

// Response 200 OK
{
  "success": true,
  "data": {
    "sessions": [
      {
        "id": "sess_abc123",
        "name": "React 專案重構",
        "status": "active",
        "agent": {
          "id": "build",
          "name": "Build Agent",
          "type": "build"
        },
        "createdAt": "2026-01-22T10:30:00Z",
        "updatedAt": "2026-01-22T11:15:00Z",
        "lastActivity": "2026-01-22T11:15:00Z",
        "taskCount": 5,
        "metadata": {
          "projectPath": "/home/user/project",
          "language": "typescript"
        }
      }
    ],
    "pagination": {
      "total": 25,
      "page": 1,
      "limit": 10,
      "totalPages": 3
    }
  }
}
```

### POST /sessions
建立新會話

```typescript
// Request
interface CreateSessionRequest {
  name: string
  agentId: string
  config?: {
    projectPath?: string
    rules?: string[]
    skills?: string[]
    metadata?: Record<string, any>
  }
}

// Response
interface CreateSessionResponse {
  success: boolean
  data: {
    session: Session
  }
}

// Example
POST /sessions
{
  "name": "新專案開發",
  "agentId": "build",
  "config": {
    "projectPath": "/home/user/new-project",
    "rules": ["follow-typescript-style"],
    "skills": ["code-review", "testing"]
  }
}
```

### GET /sessions/{sessionId}
獲取特定會話詳情

```typescript
// Response
interface SessionDetailResponse {
  success: boolean
  data: {
    session: Session & {
      tasks: Task[]
      configuration: SessionConfiguration
      statistics: SessionStatistics
    }
  }
}

interface SessionConfiguration {
  agent: AgentConfiguration
  rules: Rule[]
  skills: Skill[]
  permissions: Permission[]
}

interface SessionStatistics {
  totalTasks: number
  completedTasks: number
  failedTasks: number
  averageTaskDuration: number
  totalExecutionTime: number
}
```

### DELETE /sessions/{sessionId}
刪除會話

```typescript
// Response
interface DeleteSessionResponse {
  success: boolean
  message: string
}
```

---

## 🎯 任務處理 API

### POST /tasks
提交新任務

```typescript
// Request
interface TaskSubmitRequest {
  sessionId: string
  content: string
  type?: 'chat' | 'command' | 'file_operation'
  context?: {
    files?: string[]
    workingDirectory?: string
    environment?: Record<string, string>
  }
  options?: {
    agentId?: string
    priority?: 'low' | 'normal' | 'high'
    timeout?: number
    async?: boolean
  }
}

// Response
interface TaskSubmitResponse {
  success: boolean
  data: {
    task: Task
  }
}

interface Task {
  id: string
  sessionId: string
  content: string
  type: 'chat' | 'command' | 'file_operation'
  status: 'pending' | 'planning' | 'executing' | 'reviewing' | 'completed' | 'failed' | 'cancelled'
  result?: TaskResult
  executionPath: 'fast' | 'agent'
  createdAt: string
  startedAt?: string
  completedAt?: string
  estimatedCompletion?: string
  progress?: {
    percentage: number
    currentStep?: string
    totalSteps?: number
  }
  metadata: Record<string, any>
}

interface TaskResult {
  success: boolean
  output?: string
  files?: FileChange[]
  commands?: CommandExecution[]
  error?: TaskError
  metrics?: {
    executionTime: number
    toolsUsed: string[]
    resourceUsage: ResourceUsage
  }
}

// Example
POST /tasks
{
  "sessionId": "sess_abc123",
  "content": "幫我重構這個 React 組件，加上 TypeScript 類型",
  "type": "file_operation",
  "context": {
    "files": ["src/components/Button.jsx"],
    "workingDirectory": "/home/user/project"
  },
  "options": {
    "priority": "normal",
    "async": false
  }
}

// Response 201 Created
{
  "success": true,
  "data": {
    "task": {
      "id": "task_xyz789",
      "sessionId": "sess_abc123",
      "content": "幫我重構這個 React 組件，加上 TypeScript 類型",
      "type": "file_operation",
      "status": "pending",
      "executionPath": "agent",
      "createdAt": "2026-01-22T11:20:00Z",
      "metadata": {
        "estimatedDuration": 300
      }
    }
  }
}
```

### GET /tasks/{taskId}
獲取任務狀態

```typescript
// Response
interface TaskStatusResponse {
  success: boolean
  data: {
    task: Task
  }
}

// Example
GET /tasks/task_xyz789

// Response 200 OK
{
  "success": true,
  "data": {
    "task": {
      "id": "task_xyz789",
      "sessionId": "sess_abc123",
      "status": "executing",
      "progress": {
        "percentage": 65,
        "currentStep": "Adding TypeScript interfaces",
        "totalSteps": 4
      },
      "executionPath": "agent",
      "startedAt": "2026-01-22T11:20:05Z",
      "estimatedCompletion": "2026-01-22T11:23:00Z"
    }
  }
}
```

### POST /tasks/{taskId}/cancel
取消任務

```typescript
// Response
interface CancelTaskResponse {
  success: boolean
  message: string
  data: {
    task: Task
  }
}
```

### GET /tasks
獲取任務列表

```typescript
// Query Parameters
interface TasksQuery {
  sessionId?: string
  status?: TaskStatus
  type?: TaskType
  page?: number
  limit?: number
  sortBy?: 'createdAt' | 'updatedAt' | 'priority'
  sortOrder?: 'asc' | 'desc'
}

// Response
interface TasksResponse {
  success: boolean
  data: {
    tasks: Task[]
    pagination: Pagination
  }
}
```

---

## 🤖 Agent 管理 API

### GET /agents
獲取可用 Agent 列表

```typescript
// Response
interface AgentsResponse {
  success: boolean
  data: {
    agents: Agent[]
  }
}

interface Agent {
  id: string
  name: string
  type: 'build' | 'plan' | 'general' | 'custom'
  description: string
  capabilities: string[]
  configuration: AgentConfiguration
  status: 'available' | 'busy' | 'offline'
  metadata: {
    version: string
    author?: string
    tags?: string[]
  }
}

interface AgentConfiguration {
  model: string
  maxTokens: number
  temperature: number
  tools: string[]
  permissions: Permission[]
  systemPrompt?: string
}

// Example
GET /agents

// Response 200 OK
{
  "success": true,
  "data": {
    "agents": [
      {
        "id": "build",
        "name": "Build Agent",
        "type": "build",
        "description": "完整權限的開發助理，適合編碼工作",
        "capabilities": ["code_generation", "file_operations", "tool_execution"],
        "configuration": {
          "model": "claude-3-5-sonnet",
          "maxTokens": 4000,
          "temperature": 0.1,
          "tools": ["bash", "edit", "read"],
          "permissions": ["tool:execute", "config:write"]
        },
        "status": "available"
      },
      {
        "id": "plan",
        "name": "Plan Agent",
        "type": "plan",
        "description": "唯讀模式，適合代碼分析與探索",
        "capabilities": ["code_analysis", "planning", "documentation"],
        "configuration": {
          "model": "claude-3-5-sonnet",
          "maxTokens": 8000,
          "temperature": 0.05,
          "tools": ["read", "search"],
          "permissions": ["session:read", "task:read"]
        },
        "status": "available"
      }
    ]
  }
}
```

### POST /agents
建立自定義 Agent

```typescript
// Request
interface CreateAgentRequest {
  name: string
  description: string
  configuration: AgentConfiguration
  skills?: string[]
  rules?: string[]
}

// Response
interface CreateAgentResponse {
  success: boolean
  data: {
    agent: Agent
  }
}

// Example
POST /agents
{
  "name": "Frontend Specialist",
  "description": "專精前端開發的客製化 Agent",
  "configuration": {
    "model": "claude-3-5-sonnet",
    "maxTokens": 6000,
    "temperature": 0.2,
    "tools": ["bash", "edit", "read"],
    "permissions": ["tool:execute"],
    "systemPrompt": "你是前端開發專家，熟悉 React、TypeScript、TailwindCSS"
  },
  "skills": ["react-development", "typescript-migration"],
  "rules": ["prefer-functional-components", "use-typescript"]
}
```

### PUT /agents/{agentId}
更新 Agent 配置

```typescript
// Request
interface UpdateAgentRequest {
  name?: string
  description?: string
  configuration?: Partial<AgentConfiguration>
  status?: 'available' | 'busy' | 'offline'
}

// Response
interface UpdateAgentResponse {
  success: boolean
  data: {
    agent: Agent
  }
}
```

### DELETE /agents/{agentId}
刪除自定義 Agent

```typescript
// Response
interface DeleteAgentResponse {
  success: boolean
  message: string
}
```

---

## 🔧 工具管理 API

### GET /tools
獲取可用工具列表

```typescript
// Query Parameters
interface ToolsQuery {
  category?: 'file' | 'shell' | 'network' | 'database'
  server?: string  // MCP server name
  available?: boolean
}

// Response
interface ToolsResponse {
  success: boolean
  data: {
    tools: Tool[]
    servers: MCPServer[]
  }
}

interface Tool {
  id: string
  name: string
  description: string
  category: 'file' | 'shell' | 'network' | 'database' | 'custom'
  server: string
  schema: ToolSchema
  permissions: Permission[]
  status: 'available' | 'unavailable' | 'restricted'
}

interface MCPServer {
  id: string
  name: string
  type: 'local' | 'remote'
  url?: string
  status: 'online' | 'offline' | 'error'
  capabilities: string[]
  tools: string[]
  lastPing?: string
}

interface ToolSchema {
  parameters: {
    type: 'object'
    properties: Record<string, {
      type: string
      description: string
      required?: boolean
      default?: any
    }>
  }
  returns: {
    type: string
    description: string
  }
}

// Example
GET /tools?category=file

// Response 200 OK
{
  "success": true,
  "data": {
    "tools": [
      {
        "id": "read_file",
        "name": "Read File",
        "description": "讀取檔案內容",
        "category": "file",
        "server": "local-filesystem",
        "schema": {
          "parameters": {
            "type": "object",
            "properties": {
              "path": {
                "type": "string",
                "description": "檔案路徑",
                "required": true
              }
            }
          },
          "returns": {
            "type": "string",
            "description": "檔案內容"
          }
        },
        "permissions": ["tool:execute"],
        "status": "available"
      }
    ],
    "servers": [
      {
        "id": "local-filesystem",
        "name": "Local Filesystem",
        "type": "local",
        "status": "online",
        "capabilities": ["read", "write", "list"],
        "tools": ["read_file", "write_file", "list_files"]
      }
    ]
  }
}
```

### POST /tools/execute
執行工具

```typescript
// Request
interface ExecuteToolRequest {
  toolId: string
  server?: string
  parameters: Record<string, any>
  sessionId?: string
  timeout?: number
}

// Response
interface ExecuteToolResponse {
  success: boolean
  data: {
    result: any
    executionTime: number
    toolUsed: string
    server: string
  }
  error?: {
    code: string
    message: string
    details?: any
  }
}

// Example
POST /tools/execute
{
  "toolId": "read_file",
  "server": "local-filesystem",
  "parameters": {
    "path": "/home/user/project/src/App.tsx"
  },
  "sessionId": "sess_abc123"
}

// Response 200 OK
{
  "success": true,
  "data": {
    "result": "import React from 'react';\n\nfunction App() {\n  return (\n    <div>Hello World</div>\n  );\n}\n\nexport default App;",
    "executionTime": 45,
    "toolUsed": "read_file",
    "server": "local-filesystem"
  }
}
```

### GET /tools/servers
獲取 MCP 伺服器狀態

```typescript
// Response
interface ServersResponse {
  success: boolean
  data: {
    servers: MCPServer[]
    summary: {
      total: number
      online: number
      offline: number
      error: number
    }
  }
}
```

### POST /tools/servers/{serverId}/restart
重啟 MCP 伺服器

```typescript
// Response
interface RestartServerResponse {
  success: boolean
  message: string
  data: {
    server: MCPServer
  }
}
```

---

## ⚙️ 配置管理 API

### GET /config
獲取系統配置

```typescript
// Query Parameters
interface ConfigQuery {
  section?: 'platform' | 'agents' | 'tools' | 'security'
  includeSecrets?: boolean
}

// Response
interface ConfigResponse {
  success: boolean
  data: {
    config: SystemConfiguration
  }
}

interface SystemConfiguration {
  platform: {
    version: string
    mode: 'development' | 'production'
    features: Record<string, boolean>
  }
  agents: {
    default: string
    available: string[]
    configurations: Record<string, AgentConfiguration>
  }
  tools: {
    mcpServers: Record<string, MCPServerConfig>
    defaultTimeout: number
    maxConcurrent: number
  }
  security: {
    authentication: boolean
    permissions: Record<string, Permission[]>
    auditLevel: 'minimal' | 'standard' | 'detailed'
  }
}

// Example
GET /config?section=platform

// Response 200 OK
{
  "success": true,
  "data": {
    "config": {
      "platform": {
        "version": "1.1.31",
        "mode": "production",
        "features": {
          "agentOrchestration": true,
          "mcpIntegration": true,
          "webInterface": true
        }
      }
    }
  }
}
```

### PUT /config
更新系統配置

```typescript
// Request
interface UpdateConfigRequest {
  section: 'platform' | 'agents' | 'tools' | 'security'
  config: Partial<SystemConfiguration>
}

// Response
interface UpdateConfigResponse {
  success: boolean
  message: string
  data: {
    config: SystemConfiguration
  }
}

// Example
PUT /config
{
  "section": "agents",
  "config": {
    "agents": {
      "default": "build",
      "configurations": {
        "build": {
          "model": "claude-3-5-sonnet",
          "maxTokens": 8000,
          "temperature": 0.1
        }
      }
    }
  }
}
```

---

## 📊 監控 API

### GET /monitoring/health
系統健康檢查

```typescript
// Response
interface HealthResponse {
  success: boolean
  data: {
    status: 'healthy' | 'degraded' | 'unhealthy'
    timestamp: string
    services: Record<string, ServiceHealth>
    overall: {
      uptime: number
      version: string
      environment: string
    }
  }
}

interface ServiceHealth {
  status: 'online' | 'offline' | 'degraded'
  lastCheck: string
  responseTime?: number
  error?: string
}

// Example
GET /monitoring/health

// Response 200 OK
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2026-01-22T11:30:00Z",
    "services": {
      "api": {
        "status": "online",
        "lastCheck": "2026-01-22T11:30:00Z",
        "responseTime": 25
      },
      "mcp-gateway": {
        "status": "online",
        "lastCheck": "2026-01-22T11:29:55Z",
        "responseTime": 12
      },
      "redis": {
        "status": "online",
        "lastCheck": "2026-01-22T11:29:58Z",
        "responseTime": 3
      }
    },
    "overall": {
      "uptime": 3600000,
      "version": "1.1.31",
      "environment": "production"
    }
  }
}
```

### GET /monitoring/metrics
系統指標

```typescript
// Query Parameters
interface MetricsQuery {
  timeRange?: '1h' | '6h' | '24h' | '7d' | '30d'
  metrics?: string[]  // 指定要獲取的指標
  granularity?: '1m' | '5m' | '1h' | '1d'
}

// Response
interface MetricsResponse {
  success: boolean
  data: {
    timeRange: string
    granularity: string
    metrics: Record<string, MetricData[]>
  }
}

interface MetricData {
  timestamp: string
  value: number
  tags?: Record<string, string>
}

// Example
GET /monitoring/metrics?timeRange=1h&metrics=api_latency,task_count

// Response 200 OK
{
  "success": true,
  "data": {
    "timeRange": "1h",
    "granularity": "5m",
    "metrics": {
      "api_latency": [
        {
          "timestamp": "2026-01-22T10:30:00Z",
          "value": 45.2
        },
        {
          "timestamp": "2026-01-22T10:35:00Z",
          "value": 38.7
        }
      ],
      "task_count": [
        {
          "timestamp": "2026-01-22T10:30:00Z",
          "value": 12
        },
        {
          "timestamp": "2026-01-22T10:35:00Z",
          "value": 15
        }
      ]
    }
  }
}
```

---

## 🔄 WebSocket API

### WebSocket 連接

```typescript
// 連接 URL
ws://localhost:4000/ws/v1/chat?token=<jwt_token>&sessionId=<session_id>
wss://api.opencode.ai/ws/v1/chat?token=<jwt_token>&sessionId=<session_id>
```

### 事件格式

```typescript
// 基礎事件格式
interface WSEvent {
  type: string
  id: string
  timestamp: string
  data: any
}

// 客戶端發送事件
interface ClientEvent extends WSEvent {
  sessionId: string
}

// 伺服器發送事件
interface ServerEvent extends WSEvent {
  sessionId?: string
}
```

### 聊天事件

```typescript
// 客戶端 -> 伺服器：發送訊息
interface ChatMessageEvent extends ClientEvent {
  type: 'chat:message'
  data: {
    content: string
    type: 'text' | 'command'
    context?: {
      files?: string[]
      workingDirectory?: string
    }
  }
}

// 伺服器 -> 客戶端：回應訊息
interface ChatResponseEvent extends ServerEvent {
  type: 'chat:response'
  data: {
    content: string
    type: 'text' | 'markdown' | 'code'
    metadata?: {
      agent: string
      executionTime: number
      toolsUsed: string[]
    }
  }
}

// 範例
// 客戶端發送
{
  "type": "chat:message",
  "id": "msg_123",
  "timestamp": "2026-01-22T11:40:00Z",
  "sessionId": "sess_abc123",
  "data": {
    "content": "幫我建立一個 React 組件",
    "type": "command",
    "context": {
      "workingDirectory": "/home/user/project/src"
    }
  }
}

// 伺服器回應
{
  "type": "chat:response",
  "id": "resp_456",
  "timestamp": "2026-01-22T11:40:05Z",
  "sessionId": "sess_abc123",
  "data": {
    "content": "我將為您創建一個 React 組件。讓我先了解您需要什麼類型的組件？",
    "type": "markdown",
    "metadata": {
      "agent": "build",
      "executionTime": 120
    }
  }
}
```

### 任務事件

```typescript
// 客戶端 -> 伺服器：提交任務
interface TaskSubmitEvent extends ClientEvent {
  type: 'task:submit'
  data: TaskSubmitRequest
}

// 伺服器 -> 客戶端：任務進度
interface TaskProgressEvent extends ServerEvent {
  type: 'task:progress'
  data: {
    taskId: string
    status: TaskStatus
    progress: {
      percentage: number
      currentStep?: string
      totalSteps?: number
    }
    estimatedCompletion?: string
  }
}

// 伺服器 -> 客戶端：任務完成
interface TaskCompleteEvent extends ServerEvent {
  type: 'task:complete'
  data: {
    taskId: string
    result: TaskResult
    executionTime: number
  }
}

// 伺服器 -> 客戶端：任務錯誤
interface TaskErrorEvent extends ServerEvent {
  type: 'task:error'
  data: {
    taskId: string
    error: {
      code: string
      message: string
      details?: any
    }
  }
}
```

### Agent 事件

```typescript
// 客戶端 -> 伺服器：切換 Agent
interface AgentSwitchEvent extends ClientEvent {
  type: 'agent:switch'
  data: {
    agentId: string
    configuration?: Partial<AgentConfiguration>
  }
}

// 伺服器 -> 客戶端：Agent 狀態
interface AgentStatusEvent extends ServerEvent {
  type: 'agent:status'
  data: {
    agentId: string
    status: 'available' | 'busy' | 'offline'
    currentTask?: string
  }
}
```

### 系統事件

```typescript
// 伺服器 -> 客戶端：系統狀態
interface SystemStatusEvent extends ServerEvent {
  type: 'system:status'
  data: {
    status: 'healthy' | 'degraded' | 'unhealthy'
    services: Record<string, ServiceHealth>
    notifications?: Notification[]
  }
}

// 伺服器 -> 客戶端：連接事件
interface ConnectionEvent extends ServerEvent {
  type: 'connection:established' | 'connection:lost' | 'connection:restored'
  data: {
    message: string
    reconnectIn?: number
  }
}
```

---

## 🚨 錯誤處理

### HTTP 錯誤格式

```typescript
interface APIError {
  success: false
  error: {
    code: string
    message: string
    details?: any
    timestamp: string
    requestId: string
  }
}

// 常見錯誤代碼
enum ErrorCode {
  // 認證錯誤 (401)
  'AUTH_REQUIRED' = 'AUTH_REQUIRED',
  'TOKEN_EXPIRED' = 'TOKEN_EXPIRED',
  'INVALID_TOKEN' = 'INVALID_TOKEN',

  // 權限錯誤 (403)
  'INSUFFICIENT_PERMISSIONS' = 'INSUFFICIENT_PERMISSIONS',
  'RESOURCE_FORBIDDEN' = 'RESOURCE_FORBIDDEN',

  // 資源錯誤 (404)
  'SESSION_NOT_FOUND' = 'SESSION_NOT_FOUND',
  'TASK_NOT_FOUND' = 'TASK_NOT_FOUND',
  'AGENT_NOT_FOUND' = 'AGENT_NOT_FOUND',

  // 驗證錯誤 (422)
  'INVALID_INPUT' = 'INVALID_INPUT',
  'MISSING_REQUIRED_FIELD' = 'MISSING_REQUIRED_FIELD',

  // 服務錯誤 (500)
  'INTERNAL_ERROR' = 'INTERNAL_ERROR',
  'SERVICE_UNAVAILABLE' = 'SERVICE_UNAVAILABLE',
  'TIMEOUT_ERROR' = 'TIMEOUT_ERROR'
}

// 範例錯誤回應
// Response 401 Unauthorized
{
  "success": false,
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "JWT token has expired",
    "details": {
      "expiredAt": "2026-01-22T10:30:00Z"
    },
    "timestamp": "2026-01-22T11:30:00Z",
    "requestId": "req_abc123"
  }
}
```

### WebSocket 錯誤格式

```typescript
interface WSError extends ServerEvent {
  type: 'error'
  data: {
    code: string
    message: string
    originalEvent?: string
    details?: any
  }
}

// 範例 WebSocket 錯誤
{
  "type": "error",
  "id": "err_123",
  "timestamp": "2026-01-22T11:30:00Z",
  "data": {
    "code": "TASK_EXECUTION_FAILED",
    "message": "Task execution failed due to tool timeout",
    "originalEvent": "task:submit",
    "details": {
      "taskId": "task_xyz789",
      "toolName": "bash",
      "timeout": 30000
    }
  }
}
```

---

## 📝 請求/回應範例

### 完整工作流程範例

```typescript
// 1. 登入
POST /auth/login
{
  "email": "developer@example.com",
  "password": "secure_password"
}

// 2. 建立會話
POST /sessions
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
{
  "name": "React 專案重構",
  "agentId": "build",
  "config": {
    "projectPath": "/home/user/react-app"
  }
}

// 3. 建立 WebSocket 連接
ws://localhost:4000/ws/v1/chat?token=<jwt_token>&sessionId=sess_abc123

// 4. 發送聊天訊息
{
  "type": "chat:message",
  "id": "msg_001",
  "timestamp": "2026-01-22T12:00:00Z",
  "sessionId": "sess_abc123",
  "data": {
    "content": "請幫我將這個 JavaScript 組件轉換為 TypeScript",
    "type": "command",
    "context": {
      "files": ["src/components/Button.jsx"],
      "workingDirectory": "/home/user/react-app"
    }
  }
}

// 5. 接收任務進度
{
  "type": "task:progress",
  "id": "prog_001",
  "timestamp": "2026-01-22T12:00:30Z",
  "sessionId": "sess_abc123",
  "data": {
    "taskId": "task_001",
    "status": "executing",
    "progress": {
      "percentage": 45,
      "currentStep": "Adding TypeScript interfaces",
      "totalSteps": 4
    }
  }
}

// 6. 接收完成結果
{
  "type": "task:complete",
  "id": "comp_001",
  "timestamp": "2026-01-22T12:02:15Z",
  "sessionId": "sess_abc123",
  "data": {
    "taskId": "task_001",
    "result": {
      "success": true,
      "files": [
        {
          "path": "src/components/Button.tsx",
          "action": "created",
          "content": "..."
        }
      ]
    },
    "executionTime": 125000
  }
}
```

---

## 🔄 版本控制

### API 版本控制策略

```yaml
版本格式: "v{major}.{minor}"
當前版本: "v1.0"
支援版本: ["v1.0"]

向後兼容性:
  - 新增欄位: 不影響現有客戶端
  - 廢棄欄位: 6個月過渡期
  - 破壞性變更: 新版本號

版本指定方式:
  - URL 路徑: /api/v1/sessions
  - Header: API-Version: v1.0
  - 查詢參數: ?version=v1.0
```

### 廢棄政策

```typescript
// 廢棄欄位標記
interface DeprecatedField {
  /** @deprecated Use newFieldName instead. Will be removed in v2.0 */
  oldFieldName?: string
  newFieldName: string
}

// 廢棄回應 Header
"Deprecation: true"
"Sunset: Wed, 22 Jul 2026 23:59:59 GMT"
"Link: <https://docs.opencode.ai/api/migration>; rel=\"successor-version\""
```

---

**API 規格文檔完成！** 🎉

此 API 規格提供了完整的 RESTful API 和 WebSocket 通訊協議，支援前後端分離架構下的所有核心功能。開發團隊可以基於此規格進行並行開發，確保前後端介面的一致性和穩定性。