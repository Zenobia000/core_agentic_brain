# 技術實作指南 (Technical Implementation Guide)
# Core Agentic Brain - 開發者實作手冊

**文件版本:** 1.0
**日期:** 2026-01-27
**專案名稱:** Core Agentic Brain
**目標讀者:** 開發團隊、貢獻者

---

## 快速開始

### 30 秒部署（極簡模式）

```bash
# 1. 克隆並進入專案
git clone https://github.com/org/core-agentic-brain.git
cd core-agentic-brain

# 2. 安裝依賴
pip install pyyaml requests python-dotenv

# 3. 設定 API Key
echo "OPENAI_API_KEY=your-key-here" > .env

# 4. 啟動
python main.py

# 完成！開始對話
```

---

## 1. 開發環境設置

### 1.1 必要條件

```yaml
最低需求:
  Python: "3.10+"
  記憶體: "1GB"
  磁碟: "100MB"

建議配置:
  Python: "3.11"
  記憶體: "2GB"
  磁碟: "500MB"
  IDE: "VS Code with Python extension"
```

### 1.2 完整開發環境

```bash
# 1. 創建專案目錄
mkdir core-agentic-brain
cd core-agentic-brain

# 2. 初始化 Git
git init

# 3. 創建虛擬環境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 4. 安裝開發依賴
pip install -r requirements-dev.txt

# 5. 設置 pre-commit hooks
pre-commit install

# 6. 創建環境檔案
cp .env.example .env
# 編輯 .env 添加你的 API keys
```

### 1.3 專案結構初始化

```bash
# 創建目錄結構
mkdir -p core/{llm/providers} router agents tools/{builtin,custom}
mkdir -p enterprise/{auth,permissions,audit}
mkdir -p web/static tests/{unit,integration,performance}
mkdir -p docs config scripts

# 創建必要的 __init__.py
touch core/__init__.py router/__init__.py agents/__init__.py
touch tools/__init__.py enterprise/__init__.py
```

---

## 2. 核心實作步驟

### 2.1 Step 1: 實作極簡核心 (Layer 0)

#### main.py - 統一入口（< 50 行）

```python
#!/usr/bin/env python3
"""Core Agentic Brain - 統一入口"""

import sys
import asyncio
from pathlib import Path
from core.agent import Agent
from core.config import load_config

def main():
    """主函數"""
    # 載入配置
    config_path = Path("config.yaml")
    if not config_path.exists():
        config = {}  # 使用預設配置
    else:
        config = load_config(config_path)

    # 初始化 Agent
    agent = Agent(config)

    # CLI 模式
    print("Core Agentic Brain - Minimal Mode")
    print("Type 'exit' to quit\n")

    while True:
        try:
            # 獲取輸入
            user_input = input("You: ")

            # 退出檢查
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break

            # 處理輸入
            response = asyncio.run(agent.process(user_input))

            # 顯示回應
            print(f"AI: {response}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")

if __name__ == "__main__":
    main()
```

#### core/agent.py - 核心邏輯（< 100 行）

```python
"""Agent 核心實作"""

from typing import Optional
from .llm import LLMWrapper
from .tools import ToolManager

class Agent:
    """極簡 Agent 實作"""

    def __init__(self, config: dict = None):
        self.config = config or self._default_config()
        self.llm = LLMWrapper(self.config.get("llm", {}))
        self.tools = ToolManager(self.config.get("tools", {}))
        self.messages = []  # 對話歷史

    async def process(self, user_input: str) -> str:
        """處理用戶輸入並返回回應"""
        # 添加用戶訊息
        self.messages.append({
            "role": "user",
            "content": user_input
        })

        # 準備工具定義
        tools = self.tools.get_definitions() if self.tools.enabled else None

        # 呼叫 LLM
        response = await self.llm.generate(self.messages, tools)

        # 處理工具調用
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_results = []
            for tool_call in response.tool_calls:
                result = await self.tools.execute(
                    tool_call.name,
                    tool_call.parameters
                )
                tool_results.append({
                    "role": "tool",
                    "content": str(result),
                    "tool_call_id": tool_call.id
                })

            # 將工具結果加入對話
            self.messages.extend(tool_results)

            # 再次呼叫 LLM 獲取最終回應
            response = await self.llm.generate(self.messages)

        # 添加助手回應
        self.messages.append({
            "role": "assistant",
            "content": response.content
        })

        # 限制歷史長度（避免記憶體溢出）
        if len(self.messages) > 20:
            self.messages = self.messages[-10:]

        return response.content

    def _default_config(self) -> dict:
        """預設配置"""
        return {
            "llm": {
                "provider": "openai",
                "model": "gpt-3.5-turbo"
            },
            "tools": {
                "enabled": ["python", "files"]
            }
        }

    def reset(self):
        """重置對話"""
        self.messages = []
```

#### core/llm.py - LLM 封裝（< 50 行）

```python
"""LLM 封裝器"""

import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class LLMResponse:
    content: str
    tool_calls: Optional[List[Any]] = None

class LLMWrapper:
    """統一的 LLM 介面"""

    def __init__(self, config: dict):
        self.provider = config.get("provider", "openai")
        self.model = config.get("model", "gpt-3.5-turbo")
        self._init_client()

    def _init_client(self):
        """初始化客戶端"""
        if self.provider == "openai":
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            self.client = openai
        else:
            raise NotImplementedError(f"Provider {self.provider} not supported")

    async def generate(self, messages: List[Dict], tools: Optional[List] = None) -> LLMResponse:
        """生成回應"""
        try:
            if self.provider == "openai":
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7
                }

                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                response = self.client.ChatCompletion.create(**kwargs)
                message = response.choices[0].message

                return LLMResponse(
                    content=message.get("content", ""),
                    tool_calls=message.get("tool_calls")
                )

        except Exception as e:
            return LLMResponse(content=f"Error: {str(e)}")
```

#### core/tools.py - 工具管理（< 50 行）

```python
"""工具管理器"""

from typing import Dict, List, Any
import importlib

class ToolManager:
    """工具註冊與執行"""

    def __init__(self, config: dict):
        self.enabled = config.get("enabled", [])
        self.tools = {}
        self._load_tools()

    def _load_tools(self):
        """載入工具"""
        for tool_name in self.enabled:
            try:
                module = importlib.import_module(f"tools.{tool_name}")
                self.tools[tool_name] = module.Tool()
            except ImportError as e:
                print(f"Warning: Could not load tool {tool_name}: {e}")

    def get_definitions(self) -> List[Dict]:
        """獲取工具定義"""
        definitions = []
        for tool in self.tools.values():
            if hasattr(tool, 'definition'):
                definitions.append(tool.definition)
        return definitions

    async def execute(self, name: str, parameters: Dict) -> Dict:
        """執行工具"""
        if tool := self.tools.get(name):
            try:
                return await tool.execute(parameters)
            except Exception as e:
                return {"error": str(e)}
        return {"error": f"Tool {name} not found"}
```

### 2.2 Step 2: 實作基礎工具

#### tools/python.py - Python 執行工具

```python
"""Python 程式碼執行工具"""

import io
import contextlib
from typing import Dict, Any

class Tool:
    """Python 執行工具"""

    @property
    def definition(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "python",
                "description": "Execute Python code and return the output",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "The Python code to execute"
                        }
                    },
                    "required": ["code"]
                }
            }
        }

    async def execute(self, parameters: Dict[str, Any]) -> Dict:
        """執行 Python 程式碼"""
        code = parameters.get("code", "")

        # 創建輸出捕獲
        output = io.StringIO()

        try:
            # 執行代碼並捕獲輸出
            with contextlib.redirect_stdout(output):
                # 使用受限的執行環境
                exec(code, {"__builtins__": self._safe_builtins()})

            return {
                "success": True,
                "output": output.getvalue()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _safe_builtins(self) -> dict:
        """返回安全的內建函數集"""
        import builtins
        safe_list = [
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'chr', 'dict',
            'dir', 'divmod', 'enumerate', 'filter', 'float', 'format',
            'hex', 'int', 'isinstance', 'len', 'list', 'map', 'max', 'min',
            'oct', 'ord', 'pow', 'print', 'range', 'repr', 'reversed',
            'round', 'set', 'slice', 'sorted', 'str', 'sum', 'tuple', 'type', 'zip'
        ]
        return {name: getattr(builtins, name) for name in safe_list}
```

#### tools/files.py - 檔案操作工具

```python
"""檔案操作工具"""

import os
from pathlib import Path
from typing import Dict, Any

class Tool:
    """檔案系統操作工具"""

    @property
    def definition(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "files",
                "description": "Perform file system operations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["read", "write", "list"],
                            "description": "The operation to perform"
                        },
                        "path": {
                            "type": "string",
                            "description": "The file or directory path"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content for write operation"
                        }
                    },
                    "required": ["operation", "path"]
                }
            }
        }

    async def execute(self, parameters: Dict[str, Any]) -> Dict:
        """執行檔案操作"""
        operation = parameters.get("operation")
        path = parameters.get("path", ".")

        # 安全檢查
        if not self._is_safe_path(path):
            return {"error": "Access denied: Path outside working directory"}

        try:
            if operation == "read":
                return self._read_file(path)
            elif operation == "write":
                content = parameters.get("content", "")
                return self._write_file(path, content)
            elif operation == "list":
                return self._list_directory(path)
            else:
                return {"error": f"Unknown operation: {operation}"}
        except Exception as e:
            return {"error": str(e)}

    def _is_safe_path(self, path: str) -> bool:
        """檢查路徑是否安全"""
        try:
            # 確保路徑在當前工作目錄內
            abs_path = Path(path).resolve()
            work_dir = Path.cwd()
            return abs_path.is_relative_to(work_dir)
        except:
            return False

    def _read_file(self, path: str) -> Dict:
        """讀取檔案"""
        with open(path, 'r', encoding='utf-8') as f:
            return {"content": f.read()}

    def _write_file(self, path: str, content: str) -> Dict:
        """寫入檔案"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"success": True, "message": f"File written: {path}"}

    def _list_directory(self, path: str) -> Dict:
        """列出目錄內容"""
        items = []
        for item in os.listdir(path):
            item_path = Path(path) / item
            items.append({
                "name": item,
                "type": "directory" if item_path.is_dir() else "file"
            })
        return {"items": items}
```

---

## 3. 進階功能實作

### 3.1 智慧路由實作 (Layer 1)

#### router/analyzer.py

```python
"""任務分析器實作"""

import re
from enum import Enum
from typing import Dict, Optional

class ExecutionPath(Enum):
    FAST = "fast"
    AGENT = "agent"

class TaskAnalyzer:
    """任務複雜度分析器"""

    def __init__(self):
        # 定義複雜任務的關鍵詞
        self.complex_keywords = [
            "plan", "design", "implement", "analyze",
            "create a system", "build", "architecture"
        ]

        # 多步驟模式
        self.multi_step_patterns = [
            r"first.*then",
            r"step \d+",
            r"and then",
            r"after that",
            r"finally"
        ]

    def analyze(self, task: str, context: Optional[Dict] = None) -> ExecutionPath:
        """分析任務並決定執行路徑"""
        task_lower = task.lower()

        # 檢查是否為複雜任務
        if self._is_complex_task(task_lower):
            return ExecutionPath.AGENT

        # 檢查是否為多步驟任務
        if self._is_multi_step(task_lower):
            return ExecutionPath.AGENT

        # 檢查上下文複雜度
        if context and self._is_complex_context(context):
            return ExecutionPath.AGENT

        # 預設為快速路徑
        return ExecutionPath.FAST

    def _is_complex_task(self, task: str) -> bool:
        """判斷是否為複雜任務"""
        return any(keyword in task for keyword in self.complex_keywords)

    def _is_multi_step(self, task: str) -> bool:
        """判斷是否為多步驟任務"""
        return any(re.search(pattern, task) for pattern in self.multi_step_patterns)

    def _is_complex_context(self, context: Dict) -> bool:
        """判斷上下文是否複雜"""
        # 檢查歷史長度
        if len(context.get("history", [])) > 10:
            return True

        # 檢查是否有多個工具調用
        tool_calls = context.get("tool_calls", 0)
        if tool_calls > 3:
            return True

        return False

    def get_complexity_score(self, task: str) -> float:
        """計算任務複雜度分數 (0.0 - 1.0)"""
        score = 0.0

        # 長度因素 (20%)
        length_score = min(len(task) / 500, 1.0) * 0.2
        score += length_score

        # 關鍵詞因素 (40%)
        keyword_count = sum(1 for kw in self.complex_keywords if kw in task.lower())
        keyword_score = min(keyword_count / 3, 1.0) * 0.4
        score += keyword_score

        # 多步驟因素 (40%)
        step_count = sum(1 for pattern in self.multi_step_patterns
                        if re.search(pattern, task, re.IGNORECASE))
        step_score = min(step_count / 2, 1.0) * 0.4
        score += step_score

        return score
```

### 3.2 代理系統實作

#### agents/planner.py

```python
"""規劃代理實作"""

from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Step:
    """執行步驟"""
    id: int
    description: str
    tool: Optional[str] = None
    dependencies: List[int] = None

@dataclass
class Plan:
    """執行計劃"""
    goal: str
    steps: List[Step]

class PlannerAgent:
    """規劃代理"""

    def __init__(self, core_agent):
        self.core = core_agent

    async def plan(self, task: str) -> Plan:
        """為任務創建執行計劃"""
        # 使用 LLM 生成計劃
        prompt = f"""
        Create a step-by-step plan for the following task:
        Task: {task}

        Format your response as numbered steps.
        For each step, indicate if a specific tool is needed.
        """

        response = await self.core.llm.generate([
            {"role": "system", "content": "You are a planning assistant."},
            {"role": "user", "content": prompt}
        ])

        # 解析回應為步驟
        steps = self._parse_steps(response.content)

        return Plan(goal=task, steps=steps)

    def _parse_steps(self, content: str) -> List[Step]:
        """解析文本為步驟列表"""
        steps = []
        lines = content.strip().split('\n')

        for i, line in enumerate(lines):
            # 簡單解析：尋找數字開頭的行
            if re.match(r'^\d+\.', line):
                step_text = re.sub(r'^\d+\.\s*', '', line)

                # 檢測工具需求
                tool = None
                if 'python' in step_text.lower():
                    tool = 'python'
                elif 'file' in step_text.lower():
                    tool = 'files'

                steps.append(Step(
                    id=i + 1,
                    description=step_text,
                    tool=tool
                ))

        return steps
```

---

## 4. 配置管理

### 4.1 配置載入器

#### core/config.py

```python
"""配置管理"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config(config_path: Path = None) -> Dict[str, Any]:
    """載入配置檔案"""
    if not config_path:
        config_path = Path("config.yaml")

    # 預設配置
    default_config = {
        "mode": "minimal",
        "core": {
            "llm": {
                "provider": "openai",
                "model": "gpt-3.5-turbo"
            },
            "tools": {
                "enabled": ["python", "files"]
            }
        }
    }

    # 如果配置檔案存在，載入並合併
    if config_path.exists():
        with open(config_path, 'r') as f:
            user_config = yaml.safe_load(f)
            config = merge_configs(default_config, user_config)
    else:
        config = default_config

    # 載入環境變量
    config = load_env_vars(config)

    return config

def merge_configs(default: Dict, user: Dict) -> Dict:
    """合併配置（用戶配置優先）"""
    result = default.copy()

    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result

def load_env_vars(config: Dict) -> Dict:
    """從環境變量載入敏感資訊"""
    # 載入 .env 檔案
    from dotenv import load_dotenv
    load_dotenv()

    # API Keys
    if api_key := os.getenv("OPENAI_API_KEY"):
        if "core" not in config:
            config["core"] = {}
        if "llm" not in config["core"]:
            config["core"]["llm"] = {}
        config["core"]["llm"]["api_key"] = api_key

    return config

def validate_config(config: Dict) -> bool:
    """驗證配置有效性"""
    required_fields = [
        "mode",
        "core.llm.provider",
        "core.llm.model"
    ]

    for field in required_fields:
        keys = field.split('.')
        value = config
        for key in keys:
            if key not in value:
                print(f"Missing required config field: {field}")
                return False
            value = value[key]

    return True
```

### 4.2 範例配置檔案

#### config.yaml

```yaml
# Core Agentic Brain 配置檔案
version: "1.0"

# 運行模式: minimal | standard | enterprise
mode: minimal

# 核心配置
core:
  # LLM 配置
  llm:
    provider: openai  # openai | anthropic | local
    model: gpt-3.5-turbo
    temperature: 0.7
    max_tokens: 2000

  # 工具配置
  tools:
    enabled:
      - python
      - files
    timeout: 30  # 秒

# 路由配置（standard 模式以上）
routing:
  enabled: false
  fast_path_threshold: 1000  # tokens
  complexity_threshold: 0.5  # 0.0-1.0

# 企業功能（enterprise 模式）
enterprise:
  # 權限系統
  permissions:
    enabled: false
    default_level: ask  # allow | ask | deny
    rules:
      - pattern: "tool:python:*"
        level: allow
      - pattern: "tool:system:*"
        level: deny

  # 審計日誌
  audit:
    enabled: false
    storage: file  # file | syslog | database
    path: ./logs/audit.log
    retention_days: 30

  # MCP 整合
  mcp:
    enabled: false
    servers:
      - name: local
        url: localhost:5000
        auth: token
```

---

## 5. 測試實作

### 5.1 單元測試範例

#### tests/test_agent.py

```python
"""Agent 單元測試"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from core.agent import Agent

class TestAgent:
    """Agent 核心測試"""

    @pytest.fixture
    def agent(self):
        """創建測試用 Agent"""
        config = {
            "llm": {"provider": "mock", "model": "test"},
            "tools": {"enabled": []}
        }
        return Agent(config)

    @pytest.mark.asyncio
    async def test_simple_message(self, agent):
        """測試簡單訊息處理"""
        with patch.object(agent.llm, 'generate') as mock_generate:
            mock_generate.return_value = AsyncMock(
                content="Hello, World!",
                tool_calls=None
            )

            response = await agent.process("Hello")

            assert response == "Hello, World!"
            assert len(agent.messages) == 2  # user + assistant

    @pytest.mark.asyncio
    async def test_tool_execution(self, agent):
        """測試工具執行"""
        # 模擬工具調用
        tool_call = Mock(
            id="call_123",
            name="python",
            parameters={"code": "print('test')"}
        )

        with patch.object(agent.llm, 'generate') as mock_generate:
            # 第一次調用返回工具請求
            mock_generate.side_effect = [
                AsyncMock(content="", tool_calls=[tool_call]),
                AsyncMock(content="Executed successfully", tool_calls=None)
            ]

            with patch.object(agent.tools, 'execute') as mock_execute:
                mock_execute.return_value = {"output": "test"}

                response = await agent.process("Run print('test')")

                mock_execute.assert_called_once_with(
                    "python",
                    {"code": "print('test')"}
                )
                assert response == "Executed successfully"

    def test_message_history_limit(self, agent):
        """測試訊息歷史限制"""
        # 添加超過限制的訊息
        for i in range(25):
            agent.messages.append({"role": "user", "content": f"Message {i}"})

        # 觸發清理
        agent._cleanup_history()

        # 確認只保留最近的訊息
        assert len(agent.messages) == 10

    def test_default_config(self):
        """測試預設配置"""
        agent = Agent()  # 無配置

        assert agent.config["llm"]["provider"] == "openai"
        assert "python" in agent.config["tools"]["enabled"]
```

### 5.2 整合測試

#### tests/test_integration.py

```python
"""整合測試"""

import pytest
import asyncio
from pathlib import Path
from core.agent import Agent
from core.config import load_config

class TestIntegration:
    """端到端整合測試"""

    @pytest.fixture
    async def system(self):
        """創建完整系統"""
        config = load_config(Path("tests/fixtures/test_config.yaml"))
        agent = Agent(config)
        return agent

    @pytest.mark.asyncio
    async def test_python_execution(self, system):
        """測試 Python 程式碼執行"""
        response = await system.process("Calculate 2+2 using Python")

        assert "4" in response

    @pytest.mark.asyncio
    async def test_file_operations(self, system, tmp_path):
        """測試檔案操作"""
        # 創建測試檔案
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        # 讀取檔案
        response = await system.process(f"Read the file {test_file}")

        assert "Hello, World!" in response

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, system):
        """測試多輪對話"""
        # 第一輪
        response1 = await system.process("Remember the number 42")
        assert response1

        # 第二輪（應該記得上下文）
        response2 = await system.process("What number did I ask you to remember?")
        assert "42" in response2

    @pytest.mark.asyncio
    async def test_error_handling(self, system):
        """測試錯誤處理"""
        # 測試無效的工具調用
        response = await system.process("Execute invalid Python code: {{{{")

        # 應該優雅地處理錯誤
        assert "error" in response.lower() or "invalid" in response.lower()
```

---

## 6. 部署指南

### 6.1 Docker 部署

#### Dockerfile

```dockerfile
# 多階段構建
FROM python:3.11-slim as builder

WORKDIR /app

# 安裝構建依賴
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 最終映像
FROM python:3.11-slim

WORKDIR /app

# 從 builder 複製依賴
COPY --from=builder /root/.local /root/.local

# 複製應用程式碼
COPY . .

# 設置 PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# 健康檢查
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# 執行
CMD ["python", "main.py"]
```

#### docker-compose.yaml

```yaml
version: '3.8'

services:
  core-brain:
    build: .
    container_name: core-agentic-brain
    environment:
      - MODE=${MODE:-minimal}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./data:/app/data
    ports:
      - "8000:8000"  # 如果啟用 Web 介面
    restart: unless-stopped
    networks:
      - brain-network

  # 可選：Redis 快取（enterprise 模式）
  redis:
    image: redis:7-alpine
    container_name: brain-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - brain-network
    profiles:
      - enterprise

networks:
  brain-network:
    driver: bridge

volumes:
  redis-data:
```

### 6.2 系統服務部署

#### scripts/install.sh

```bash
#!/bin/bash
# Core Agentic Brain 安裝腳本

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查 Python 版本
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python 3 is not installed${NC}"
        exit 1
    fi

    version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    required="3.10"

    if [ "$(printf '%s\n' "$required" "$version" | sort -V | head -n1)" != "$required" ]; then
        echo -e "${RED}Python $version is too old. Required: >= $required${NC}"
        exit 1
    fi

    echo -e "${GREEN}Python $version detected${NC}"
}

# 安裝依賴
install_deps() {
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
}

# 創建配置
setup_config() {
    if [ ! -f config.yaml ]; then
        echo "Creating default configuration..."
        cp config.example.yaml config.yaml
    fi

    if [ ! -f .env ]; then
        echo "Creating environment file..."
        echo "# Add your API keys here" > .env
        echo "OPENAI_API_KEY=your-key-here" >> .env
        echo -e "${YELLOW}Please edit .env and add your API keys${NC}"
    fi
}

# 創建 systemd 服務
create_service() {
    echo "Creating systemd service..."

    cat > /tmp/core-agentic-brain.service << EOF
[Unit]
Description=Core Agentic Brain
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
ExecStart=/usr/bin/python3 $PWD/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo mv /tmp/core-agentic-brain.service /etc/systemd/system/
    sudo systemctl daemon-reload
    echo -e "${GREEN}Service created${NC}"
}

# 主函數
main() {
    echo "Core Agentic Brain Installer"
    echo "============================"

    check_python
    install_deps
    setup_config

    echo ""
    echo -e "${GREEN}Installation complete!${NC}"
    echo ""
    echo "To start the application:"
    echo "  python3 main.py"
    echo ""
    echo "To install as a service:"
    echo "  sudo systemctl enable core-agentic-brain"
    echo "  sudo systemctl start core-agentic-brain"
}

main "$@"
```

---

## 7. 效能優化

### 7.1 快取實作

```python
"""快取系統"""

from functools import lru_cache
from typing import Any, Optional
import hashlib
import json
import time

class Cache:
    """簡單記憶體快取"""

    def __init__(self, ttl: int = 300):
        """
        Args:
            ttl: Time to live in seconds
        """
        self.ttl = ttl
        self.cache = {}

    def get(self, key: str) -> Optional[Any]:
        """獲取快取值"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any):
        """設置快取值"""
        self.cache[key] = (value, time.time())

    def clear(self):
        """清空快取"""
        self.cache.clear()

    @staticmethod
    def make_key(*args, **kwargs) -> str:
        """生成快取鍵"""
        data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(data.encode()).hexdigest()

# 使用裝飾器實作快取
def cached(ttl: int = 300):
    """快取裝飾器"""
    cache = Cache(ttl)

    def decorator(func):
        async def wrapper(*args, **kwargs):
            key = cache.make_key(*args, **kwargs)

            # 檢查快取
            if result := cache.get(key):
                return result

            # 執行函數
            result = await func(*args, **kwargs)

            # 存入快取
            cache.set(key, result)

            return result
        return wrapper
    return decorator
```

### 7.2 並發優化

```python
"""並發處理優化"""

import asyncio
from typing import List, Callable, Any

class ConcurrentExecutor:
    """並發執行器"""

    def __init__(self, max_workers: int = 5):
        self.semaphore = asyncio.Semaphore(max_workers)

    async def execute_parallel(self, tasks: List[Callable]) -> List[Any]:
        """並行執行多個任務"""
        async def run_with_limit(task):
            async with self.semaphore:
                return await task()

        results = await asyncio.gather(
            *[run_with_limit(task) for task in tasks],
            return_exceptions=True
        )

        return results

    async def execute_batch(self, func: Callable, items: List[Any], batch_size: int = 10) -> List[Any]:
        """批次執行"""
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[func(item) for item in batch],
                return_exceptions=True
            )
            results.extend(batch_results)

        return results

# 使用範例
async def optimized_multi_tool_execution(tools: List[str], params: List[dict]):
    """優化的多工具執行"""
    executor = ConcurrentExecutor(max_workers=3)

    # 創建任務列表
    tasks = [
        lambda t=tool, p=param: tool_manager.execute(t, p)
        for tool, param in zip(tools, params)
    ]

    # 並行執行
    results = await executor.execute_parallel(tasks)

    return results
```

---

## 8. 監控與除錯

### 8.1 日誌系統

```python
"""日誌配置"""

import logging
import sys
from pathlib import Path

def setup_logging(level: str = "INFO", log_file: str = None):
    """設置日誌系統"""
    # 創建 logger
    logger = logging.getLogger("core_agentic_brain")
    logger.setLevel(getattr(logging, level.upper()))

    # 格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 檔案處理器（如果指定）
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# 使用
logger = setup_logging(level="DEBUG", log_file="app.log")
```

### 8.2 性能分析

```python
"""性能分析工具"""

import time
import functools
from contextlib import contextmanager

class PerformanceMonitor:
    """性能監控器"""

    def __init__(self):
        self.metrics = {}

    @contextmanager
    def measure(self, name: str):
        """測量執行時間"""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(duration)

    def report(self):
        """生成報告"""
        report = {}
        for name, times in self.metrics.items():
            report[name] = {
                "count": len(times),
                "total": sum(times),
                "average": sum(times) / len(times),
                "min": min(times),
                "max": max(times)
            }
        return report

# 全局監控器
monitor = PerformanceMonitor()

# 使用範例
async def monitored_function():
    with monitor.measure("function_execution"):
        # 執行代碼
        await asyncio.sleep(0.1)

# 裝飾器版本
def profile(name: str = None):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            metric_name = name or func.__name__
            with monitor.measure(metric_name):
                return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## 9. 常見問題與解決方案

### 9.1 問題排查清單

```yaml
常見問題:
  API Key 錯誤:
    症狀: "Invalid API key" 錯誤
    解決:
      - 檢查 .env 檔案中的 API key
      - 確認環境變量已載入
      - 驗證 API key 有效性

  工具載入失敗:
    症狀: "Could not load tool" 警告
    解決:
      - 檢查 tools/ 目錄下的工具模組
      - 確認工具類別名稱為 Tool
      - 驗證 definition 屬性存在

  記憶體溢出:
    症狀: 系統變慢或崩潰
    解決:
      - 限制對話歷史長度
      - 實作訊息清理機制
      - 使用串流處理大檔案

  響應超時:
    症狀: 長時間無響應
    解決:
      - 設置合理的超時時間
      - 實作重試機制
      - 使用快取減少 API 調用
```

### 9.2 除錯技巧

```python
"""除錯輔助函數"""

def debug_print(obj: Any, name: str = "Object"):
    """詳細列印對象資訊"""
    print(f"\n{'='*50}")
    print(f"DEBUG: {name}")
    print(f"Type: {type(obj)}")
    print(f"Value: {obj}")
    if hasattr(obj, '__dict__'):
        print(f"Attributes: {obj.__dict__}")
    print(f"{'='*50}\n")

async def debug_llm_call(messages: List[dict], tools: List[dict] = None):
    """除錯 LLM 調用"""
    print("\n--- LLM Call Debug ---")
    print(f"Messages: {len(messages)}")
    for msg in messages:
        print(f"  {msg['role']}: {msg['content'][:100]}...")
    if tools:
        print(f"Tools: {[t['function']['name'] for t in tools]}")
    print("--- End Debug ---\n")

# 條件除錯
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

if DEBUG:
    debug_print(config, "Configuration")
```

---

## 10. 最佳實踐

### 10.1 代碼風格指南

```python
"""
代碼風格規範：
1. 使用 Black 格式化
2. 使用 Type Hints
3. 編寫 Docstrings
4. 保持函數簡短（< 20 行）
5. 避免深層嵌套（< 3 層）
"""

# ✅ 好的範例
async def process_message(
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """處理用戶訊息

    Args:
        message: 用戶輸入
        context: 可選的上下文

    Returns:
        AI 回應
    """
    if not message:
        return "Empty message"

    # 處理邏輯
    result = await self._process(message, context)
    return result

# ❌ 不好的範例
async def process(msg):
    if msg:
        if len(msg) > 0:
            try:
                # 複雜的嵌套邏輯
                pass
            except:
                pass
```

### 10.2 安全性檢查清單

```yaml
安全檢查:
  輸入驗證:
    - [ ] 檢查輸入長度限制
    - [ ] 過濾特殊字符
    - [ ] 防止注入攻擊

  API 安全:
    - [ ] API key 不硬編碼
    - [ ] 使用環境變量
    - [ ] 實作速率限制

  工具安全:
    - [ ] 沙箱執行環境
    - [ ] 資源限制
    - [ ] 路徑驗證

  數據保護:
    - [ ] 敏感資訊不記錄
    - [ ] 加密傳輸
    - [ ] 安全存儲
```

---

**文檔結束**

這份實作指南提供了完整的開發流程，從環境設置到部署維護。按照指南逐步實作，即可構建一個功能完整、性能優異的通用 Agent 平台。