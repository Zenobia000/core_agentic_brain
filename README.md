# Core Agentic Brain

> **「能做事、管得住、查得到」**

基於 OpenManus 擴展的企業級自主代理作業系統。

**GitHub**: `core_agentic_brain`

---

## 🏗️ 架構概覽

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Users / Systems                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 API Gateway (Auth / Rate Limit / Tenant)                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│            Agent Runtime (Manus Core++) - Loop Engine + State Machine   │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │Policy Plane │  │ Ops Plane   │  │ Governance  │  ← Control Plane    │
│  │RBAC/ABAC    │  │Observability│  │Prompt/Skill │                     │
│  │Data Class   │  │Cost + SLO   │  │Versioning   │                     │
│  └─────────────┘  └─────────────┘  └─────────────┘                     │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    ┌─────────────────────────────────────┐    │
│  │   Skill Registry    │    │          Tool Gateway               │    │
│  │ Schemas+Tests+Ver   │    │   MCP/HTTP/gRPC Adapters+Contracts  │    │
│  └─────────────────────┘    └─────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    ┌─────────────────────────────────────┐    │
│  │  Sandbox Runtime    │    │        Memory System                │    │
│  │ Isolated Exec/FileIO│    │ Short-term + Episodic + Long-term   │    │
│  │   Network Policy    │    │           (RAG)                     │    │
│  └─────────────────────┘    └─────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 專案結構

```
OpenManus/
└── app/
    │
    ├── agent/              # ✅ Agent 核心 (原 OpenManus)
    │   ├── base.py         # BaseAgent
    │   ├── react.py        # ReActAgent
    │   ├── toolcall.py     # ToolCallAgent
    │   ├── manus.py        # Manus (主 Agent)
    │   └── ...
    │
    ├── tool/               # ✅ 工具集合 (原 OpenManus)
    │   ├── base.py
    │   ├── bash.py
    │   ├── python_execute.py
    │   ├── web_search.py
    │   └── ...
    │
    ├── memory/             # 🆕 Memory System
    │   ├── short_term.py   # 短期記憶 (對話上下文)
    │   ├── episodic.py     # 情節記憶 (task_N_output.json)
    │   ├── long_term.py    # 長期記憶 (RAG)
    │   └── context_manager.py  # Context Engineering
    │
    ├── control_plane/      # 🆕 Control Plane
    │   └── __init__.py     # Policy + Ops + Governance
    │
    ├── tool_gateway/       # 🆕 Tool Gateway
    │   └── __init__.py     # MCP/HTTP/gRPC 適配器
    │
    ├── skill_registry/     # 🆕 Skill Registry
    │   └── __init__.py     # 技能註冊與管理
    │
    ├── runtime/            # 🆕 Agent Runtime
    │   └── __init__.py     # Loop Engine + Task Spec + Verifier
    │
    ├── flow/               # ✅ Flow 編排 (原 OpenManus)
    ├── prompt/             # ✅ Prompt 模板 (原 OpenManus)
    ├── sandbox/            # ✅ Sandbox (原 OpenManus)
    ├── mcp/                # ✅ MCP Server (原 OpenManus)
    │
    ├── schema.py           # ✅ 資料模型
    ├── llm.py              # ✅ LLM 抽象層
    └── config.py           # ✅ 配置管理
```

---

## 🚀 新增模組說明

### 1. Memory System (`app/memory/`)

三層記憶架構：

```python
from app.memory import ContextManager, ShortTermMemory, EpisodicMemory, LongTermMemory

# 初始化
ctx = ContextManager()
await ctx.initialize(episodic_path="./task_history")

# 對話管理
ctx.add_message("user", "幫我分析這份報告")
ctx.add_message("assistant", "好的，我來分析...")

# 任務記錄
task = ctx.create_task(goal="分析報告")
task.start()
task.add_step("plan", "規劃分析步驟")
task.complete(result="分析完成")

# 知識存儲
await ctx.store_knowledge("重要的領域知識...", source="manual")

# 組裝上下文
context_window = await ctx.assemble_context(
    query="分析這份報告",
    include_knowledge=True,
    include_experience=True
)
messages = context_window.to_messages()
```

### 2. Control Plane (`app/control_plane/`)

治理與可觀測性：

```python
from app.control_plane import PolicyEngine, OpsPlane, GovernancePlane

# Policy - RBAC/ABAC
policy = PolicyEngine.create_default()
allowed, reason = policy.check_permission("agent", "tool", "use")
allowed, reason = policy.is_tool_allowed("bash")

# Ops - 可觀測性
ops = OpsPlane()
trace = ops.start_trace("task_execution")
ops.record_cost(input_tokens=100, output_tokens=50, model="gpt-4")
ops.log_audit("tool_call", "bash", "manus_agent", success=True)
ops.end_trace()

# Governance - 版本控制
gov = GovernancePlane()
prompt = gov.register_prompt("system_prompt", "You are a helpful assistant...")
prompt.publish()
```

### 3. Tool Gateway (`app/tool_gateway/`)

統一工具介面：

```python
from app.tool_gateway import ToolGateway, LocalToolAdapter

# 註冊工具
gateway = ToolGateway()
gateway.register_local_tool("my_tool", my_function)

# 執行工具
result = await gateway.execute("my_tool", {"arg1": "value1"})
print(result.success, result.data)
```

### 4. Skill Registry (`app/skill_registry/`)

技能管理：

```python
from app.skill_registry import SkillRegistry, SkillCategory

# 註冊技能
registry = SkillRegistry()
skill = registry.register(
    name="web_search",
    description="搜尋網路資訊",
    category=SkillCategory.SEARCH
)

# 從工具集合自動發現
from app.tool import ToolCollection
tools = ToolCollection(...)
count = registry.discover_from_tool_collection(tools)

# 導出為 OpenAI 格式
openai_tools = registry.to_openai_tools()
```

### 5. Agent Runtime (`app/runtime/`)

標準化執行：

```python
from app.runtime import AgentRuntime, TaskSpec, LoopEngine, CriteriaBasedVerifier

# 定義任務規格
task = TaskSpec(
    goal="分析報告並生成摘要",
    constraints=["不超過 500 字", "使用繁體中文"],
    success_criteria=["包含關鍵發現", "有結論建議"],
    budget={"max_tokens": 5000, "max_time_seconds": 60}
)

# 建立 Runtime
runtime = AgentRuntime()
runtime.loop_engine.verifier = CriteriaBasedVerifier()

# 執行
result = await runtime.execute_task(task, manus_agent)
print(result["success"], result["result"])
```

---

## 🔄 執行循環

```
規劃 → 執行 → 驗證 → 修正 (循環)

┌─────────────────┐     ┌─────────────────┐
│    Tools        │     │     Agent       │
│ task_1_output   │────▶│    Tool1        │
│ task_2_output   │     │    Tool2        │
│ task_3_output   │     │    ...          │
└─────────────────┘     └─────────────────┘
        ↑                       │
        │                       ▼
        │               ┌─────────────────┐
        │               │   Verifier      │
        │               │   pass/fail     │
        │               └─────────────────┘
        │                       │
        │                       ▼
        │               ┌─────────────────────────────────────────┐
        └───────────────│  Memory (Context Engineering)           │
                        │  - Short-term (對話)                    │
                        │  - Episodic (任務歷史)                  │
                        │  - Long-term (RAG)                      │
                        └─────────────────────────────────────────┘
```

---

## 📝 快速開始

### Linux / macOS

```bash
# 1. 進入目錄
cd OpenManus

# 2. 執行設置腳本 (建立 venv + 安裝依賴)
chmod +x setup.sh
./setup.sh

# 3. 啟動虛擬環境
source venv/bin/activate

# 4. 編輯配置 (填入 API Key)
nano config/config.toml

# 5. 執行
python main.py
```

### Windows

```powershell
# 1. 進入目錄
cd OpenManus

# 2. 執行設置腳本
setup.bat

# 3. 啟動虛擬環境
venv\Scripts\activate

# 4. 編輯配置
notepad config\config.toml

# 5. 執行
python main.py
```

### 手動設置

```bash
# 建立虛擬環境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 複製配置
cp config/config.example.toml config/config.toml
```

---

## 📚 文件

- `docs/openmanus_system_architecure/` - OpenManus 系統架構文件
- `docs/預期開發架構/` - 目標架構設計文件
- `sunny_prompt/` - Prompt 工程模板

---

## 🎯 設計原則

1. **能做事** - 強大的 Agent Runtime 和工具集
2. **管得住** - Policy + Sandbox + Approval 確保行為符合規範
3. **查得到** - 完整的追蹤、稽核、成本計量

---

## 📄 License

Apache-2.0