# OpenCode Agent Platform - Quick Start Guide

**Document Version:** 1.0
**Date:** 2026-01-22
**Project:** OpenCode Universal Agent Platform

---

## 🚀 5分鐘快速開始

### 前置需求

- Python 3.11+
- Git
- 現有 OpenCode 安裝 (或待安裝)

### 安裝步驟

#### 1. 克隆專案

```bash
git clone https://github.com/your-org/opencode-agent-platform.git
cd opencode-agent-platform
```

#### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

#### 3. 基本配置

```bash
# 創建配置目錄
mkdir -p .opencode

# 複製範例配置
cp config/examples/basic-config.yaml .opencode/config.yaml

# 設定權限
cp config/examples/basic-permissions.yaml .opencode/permissions.yaml
```

#### 4. 啟動平台

```bash
python -m opencode_agent_platform.main
```

---

## ⚙️ 基本配置

### 最小配置範例

**`.opencode/config.yaml`**:
```yaml
platform:
  version: "2.0"
  compatibility_mode: "claude_code"

routing:
  fast_path_threshold: 1000
  agent_timeout: 300

mcp_servers:
  sandbox:
    type: "local"
    command: ["python", "-m", "mcp_sandbox"]
    auto_start: true
    capabilities: ["bash", "python", "file_ops"]

security:
  default_permission: "ask"
  audit:
    enabled: true
```

### 權限配置範例

**`.opencode/permissions.yaml`**:
```yaml
permissions:
  - scope: "tool"
    action: "execute"
    pattern: "git"
    level: "allow"
    reason: "Git operations are generally safe"

  - scope: "tool"
    action: "execute"
    pattern: "bash"
    level: "ask"
    reason: "Shell commands require approval"

  - scope: "file_pattern"
    action: "read"
    pattern: "**/*.py"
    level: "allow"
    reason: "Python files are safe to read"
```

---

## 🔄 Claude Code 遷移

### 自動遷移工具

```bash
# 遷移現有 Claude Code 配置
python -m opencode_agent_platform.migration.claude_code \
  --source /path/to/claude/project \
  --target /path/to/opencode/project

# 驗證遷移結果
python -m opencode_agent_platform.migration.validate \
  --config .opencode/config.yaml
```

### 手動遷移步驟

#### 1. 遷移規則文件

```bash
# 複製 CLAUDE.md 到 AGENTS.md
cp CLAUDE.md AGENTS.md

# 或創建新的 AGENTS.md
cat > AGENTS.md << 'EOF'
# Repository Agent Configuration

## Agent Rules
- Follow existing code style
- Add comprehensive tests
- Document all public APIs

## Task Preferences
- Prefer TypeScript over JavaScript
- Use functional programming patterns
- Ensure security best practices
EOF
```

#### 2. 遷移 Skills

```bash
# 複製 Claude Code skills
cp -r .claude/skills/ .opencode/skills/

# 創建相容性符號連結
ln -sf ../.opencode/skills .claude/skills
```

#### 3. 更新配置

```bash
# 轉換 Claude Code 設定到 OpenCode 格式
python -c "
import json
import yaml

# 讀取 Claude Code 設定
with open('.claude/settings.json') as f:
    claude_settings = json.load(f)

# 轉換為 OpenCode 格式
opencode_config = {
    'platform': {'version': '2.0', 'compatibility_mode': 'claude_code'},
    'routing': {'fast_path_threshold': 1000},
    'mcp_servers': {
        'sandbox': {
            'type': 'local',
            'command': ['python', '-m', 'mcp_sandbox'],
            'capabilities': ['bash', 'python', 'file_ops']
        }
    }
}

# 寫入 OpenCode 配置
with open('.opencode/config.yaml', 'w') as f:
    yaml.dump(opencode_config, f, default_flow_style=False)
"
```

---

## 🧪 基本使用範例

### 範例 1: 簡單文件操作 (Fast Path)

```python
# 這種簡單操作會走 Fast Path
task = "讀取 README.md 並總結主要內容"

# 平台會自動判斷為簡單任務，直接執行
result = platform.process_task(task)
print(f"執行路徑: {result['execution_path']}")  # 輸出: fast
```

### 範例 2: 複雜重構任務 (Agent Path)

```python
# 這種複雜操作會走 Agent Path
task = """
分析 src/ 目錄中的 Python 代碼並執行以下重構：
1. 添加類型提示
2. 改善錯誤處理
3. 添加單元測試
4. 更新文檔
"""

# 平台會啟動 Agent 編排流程
result = platform.process_task(task)
print(f"執行路徑: {result['execution_path']}")  # 輸出: agent
print(f"執行計劃: {result['plan']['steps']}")
```

### 範例 3: 自定義技能使用

**創建技能文件** `.opencode/skills/code_review.md`:
```markdown
# Code Review Skill

## Description
Perform comprehensive code review with security focus

## Instructions
1. Analyze code for security vulnerabilities
2. Check code style and best practices
3. Verify test coverage
4. Suggest improvements

## Parameters
- `files`: List of files to review
- `focus`: Review focus (security, performance, style)
```

**使用技能**:
```python
# 調用自定義技能
task = "/code_review files=['src/auth.py'] focus=security"

result = platform.process_task(task)
```

---

## 🛠️ 開發與測試

### 本地開發設置

```bash
# 開發模式安裝
pip install -e .

# 安裝開發依賴
pip install -r requirements-dev.txt

# 執行測試
pytest tests/

# 執行 linting
flake8 opencode_agent_platform/
black opencode_agent_platform/
```

### 創建自定義 MCP Server

**範例 MCP Server** (`custom_mcp_server.py`):
```python
import asyncio
import json
from typing import Dict, Any

class CustomMCPServer:
    def __init__(self):
        self.tools = {
            "hello": self.hello_tool,
            "calculate": self.calculate_tool
        }

    async def hello_tool(self, args: Dict[str, Any]) -> Dict[str, Any]:
        name = args.get("name", "World")
        return {
            "success": True,
            "message": f"Hello, {name}!",
            "timestamp": "2026-01-22T10:30:00Z"
        }

    async def calculate_tool(self, args: Dict[str, Any]) -> Dict[str, Any]:
        operation = args.get("operation", "add")
        a = args.get("a", 0)
        b = args.get("b", 0)

        if operation == "add":
            result = a + b
        elif operation == "multiply":
            result = a * b
        else:
            return {"success": False, "error": "Unsupported operation"}

        return {
            "success": True,
            "result": result,
            "operation": operation
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = request.get("tool")
        args = request.get("arguments", {})

        if tool_name in self.tools:
            return await self.tools[tool_name](args)
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

if __name__ == "__main__":
    server = CustomMCPServer()
    # 實現 MCP 協議通信邏輯
```

**註冊自定義 MCP Server**:
```yaml
# .opencode/config.yaml
mcp_servers:
  custom:
    type: "local"
    command: ["python", "custom_mcp_server.py"]
    capabilities: ["hello", "calculate"]
```

### 創建自定義插件

**範例插件** (`.opencode/plugins/logger/plugin.py`):
```python
from plugins.framework.plugin_manager import PluginBase, hook

class LoggerPlugin(PluginBase):
    async def initialize(self) -> bool:
        print("Logger plugin initialized")
        return True

    async def cleanup(self):
        print("Logger plugin cleaned up")

    @hook("before_tool_execution", priority=10)
    async def log_before_execution(self, tool: str, arguments: dict):
        print(f"🔧 執行工具: {tool}")
        return {"logged": True}

    @hook("after_tool_execution", priority=10)
    async def log_after_execution(self, tool: str, result: any):
        status = "✅ 成功" if result.get("success", True) else "❌ 失敗"
        print(f"{status} 工具執行完成: {tool}")
        return {"logged": True}
```

**插件配置** (`.opencode/plugins/logger/metadata.yaml`):
```yaml
name: "logger"
version: "1.0.0"
description: "Simple logging plugin"
author: "Your Team"
dependencies: []
permissions: []
hooks:
  - "before_tool_execution"
  - "after_tool_execution"
```

**啟用插件**:
```yaml
# .opencode/config.yaml
plugins:
  enabled:
    - "logger"

  logger:
    enabled: true
    log_level: "info"
```

---

## 🔧 故障排除

### 常見問題

#### 1. MCP Server 啟動失敗

**症狀**: `MCPServerError: Failed to start server`

**解決方案**:
```bash
# 檢查 MCP server 依賴
pip install mcp-sandbox

# 檢查配置
python -m opencode_agent_platform.debug.check_mcp_config

# 手動測試 MCP server
python -m mcp_sandbox --test
```

#### 2. 權限被拒絕

**症狀**: `Permission denied for tool execution`

**解決方案**:
```bash
# 檢查權限配置
cat .opencode/permissions.yaml

# 臨時允許所有操作 (僅開發用)
echo "permissions:
  - scope: tool
    pattern: '*'
    level: allow" > .opencode/permissions.yaml
```

#### 3. 任務路由問題

**症狀**: 簡單任務被錯誤路由到 Agent Path

**解決方案**:
```yaml
# 調整路由閾值
routing:
  fast_path_threshold: 2000  # 增加閾值
  complexity_threshold: 0.5  # 降低複雜度門檻
```

### 調試工具

#### 1. 調試模式

```bash
# 啟動調試模式
OPENCODE_DEBUG=true python -m opencode_agent_platform.main

# 詳細日誌
OPENCODE_LOG_LEVEL=debug python -m opencode_agent_platform.main
```

#### 2. 配置驗證

```bash
# 驗證配置文件
python -m opencode_agent_platform.debug.validate_config

# 測試路由邏輯
python -m opencode_agent_platform.debug.test_routing \
  --task "your test task here"

# 檢查權限系統
python -m opencode_agent_platform.debug.test_permissions \
  --tool bash --action execute
```

#### 3. 性能分析

```bash
# 性能分析模式
python -m cProfile -o profile.stats \
  -m opencode_agent_platform.main

# 分析結果
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative')
p.print_stats(20)
"
```

---

## 📚 進階配置

### 企業級配置範例

```yaml
# .opencode/config.yaml (企業版)
platform:
  version: "2.0"
  compatibility_mode: "claude_code"
  log_level: "info"

routing:
  fast_path_threshold: 500
  agent_timeout: 600
  max_planning_depth: 10

security:
  default_permission: "ask"
  audit:
    enabled: true
    retention_days: 365
    encryption_key: "${AUDIT_ENCRYPTION_KEY}"

  require_approval_for:
    - destructive_operations
    - external_network_access
    - system_administration

mcp_servers:
  sandbox:
    type: "local"
    command: ["python", "-m", "mcp_sandbox"]
    capabilities: ["bash", "python", "file_ops"]
    resource_limits:
      memory: "1GB"
      cpu_percent: 25
      network: false

  enterprise:
    type: "remote"
    url: "https://internal.company.com/mcp"
    auth:
      type: "oauth"
      client_id: "${ENTERPRISE_CLIENT_ID}"
      client_secret: "${ENTERPRISE_CLIENT_SECRET}"
    capabilities: ["jira", "confluence", "database"]

agents:
  planner:
    model: "claude-3-5-sonnet"
    max_tokens: 8000
    temperature: 0.05
    system_prompt_file: ".opencode/prompts/enterprise_planner.md"

plugins:
  enabled:
    - "enterprise_policy"
    - "monitoring"
    - "security_scanner"

monitoring:
  metrics:
    enabled: true
    export_url: "https://metrics.company.com/api/v1/metrics"
    export_interval: 30
```

### 多環境配置

```bash
# 開發環境
export OPENCODE_ENV=development
export OPENCODE_CONFIG_PATH=.opencode/config.dev.yaml

# 測試環境
export OPENCODE_ENV=testing
export OPENCODE_CONFIG_PATH=.opencode/config.test.yaml

# 生產環境
export OPENCODE_ENV=production
export OPENCODE_CONFIG_PATH=.opencode/config.prod.yaml
```

---

## 🚀 部署指南

### Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/.opencode

EXPOSE 8080
CMD ["python", "-m", "opencode_agent_platform.main"]
```

```bash
# 構建與運行
docker build -t opencode-agent-platform .
docker run -p 8080:8080 \
  -v $(pwd)/.opencode:/app/.opencode \
  opencode-agent-platform
```

### Kubernetes 部署

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opencode-agent-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app: opencode-agent-platform
  template:
    metadata:
      labels:
        app: opencode-agent-platform
    spec:
      containers:
      - name: opencode
        image: opencode/agent-platform:latest
        ports:
        - containerPort: 8080
        env:
        - name: OPENCODE_ENV
          value: "production"
        volumeMounts:
        - name: config
          mountPath: /app/.opencode
      volumes:
      - name: config
        configMap:
          name: opencode-config
```

```bash
# 部署到 Kubernetes
kubectl apply -f k8s/
kubectl get pods -l app=opencode-agent-platform
```

---

## 📊 監控與維護

### 健康檢查

```bash
# 檢查服務狀態
curl http://localhost:8080/health

# 檢查各組件狀態
curl http://localhost:8080/health/detailed
```

### 監控指標

```bash
# 獲取 Prometheus 指標
curl http://localhost:8080/metrics

# 關鍵指標
- opencode_task_routing_total
- opencode_operation_duration_seconds
- opencode_mcp_server_up
- opencode_permission_decisions_total
```

### 日誌管理

```bash
# 查看應用日誌
tail -f .opencode/app.log

# 查看審計日誌
tail -f .opencode/audit.log

# 日誌輪轉配置 (logrotate)
echo "/path/to/.opencode/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
}" > /etc/logrotate.d/opencode
```

---

## 🤝 社群與支援

### 獲取幫助

- **GitHub Issues**: [報告問題](https://github.com/your-org/opencode-agent-platform/issues)
- **討論區**: [社群討論](https://github.com/your-org/opencode-agent-platform/discussions)
- **文檔**: [完整文檔](https://docs.opencode-agent.com)

### 貢獻指南

```bash
# Fork 專案
git clone https://github.com/your-username/opencode-agent-platform.git

# 創建功能分支
git checkout -b feature/amazing-feature

# 提交變更
git commit -m "Add amazing feature"

# 推送分支
git push origin feature/amazing-feature

# 創建 Pull Request
```

### 版本升級

```bash
# 檢查當前版本
python -m opencode_agent_platform.version

# 升級到最新版本
pip install --upgrade opencode-agent-platform

# 遷移配置 (如需要)
python -m opencode_agent_platform.migration.upgrade \
  --from-version 1.0 --to-version 2.0
```

---

**快速開始完成！** 🎉

現在您已經具備了 OpenCode Agent Platform 的基本使用能力。如需更深入的功能，請參閱完整的技術文檔。

**下一步建議**:
1. 嘗試複雜的多步驟任務
2. 創建自定義 MCP Server
3. 開發專屬插件
4. 設置監控與告警
5. 探索企業級功能