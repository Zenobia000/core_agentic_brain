# Kernel Architecture - 核心調度架構

## 架構哲學
基於 Linus Torvalds 的 Linux Kernel 設計原則：
- **中央調度器**：單一真相來源
- **統一介面**：消除特殊情況
- **訊息驅動**：解耦通訊

## 核心組件關係

```
main.py
   ↓
Kernel (kernel.py) ← 中央調度器
   ├── CommunicationBus (communication.py) ← 統一訊息匯流排
   ├── Agent (agent.py) ← 基礎執行單元
   ├── ToolManager (tools.py) ← 工具管理器
   ├── PromptLoader (prompt_loader.py) ← 提示管理器
   └── LLMProvider (llm.py) ← 統一 LLM 介面
```

## 組件職責

### 1. kernel.py (254行) - 中央調度器
**角色**：系統的大腦，像 Linux Kernel 一樣管理所有資源

**核心功能**：
- 統一的任務調度
- 代理生命週期管理
- 工具調用協調
- 提示詞統一存取

**關鍵方法**：
```python
async def execute(request: str) → ExecutionResult
    # 1. 分析任務 (通過 router)
    # 2. 選擇執行策略
    # 3. 調度代理執行
    # 4. 返回統一結果

get_or_create_agent(agent_type: str) → Agent
    # 延遲載入代理
    # 自動降級到 MinimalAgent
```

### 2. communication.py (92行) - 統一訊息匯流排
**角色**：系統的神經網路，所有組件間的通訊通道

**統一訊息格式**：
```python
Message:
    type: MessageType (PROMPT|TOOL_CALL|RESULT|ERROR)
    content: Any
    source: str
    target: str
    metadata: Dict
```

**零特殊情況設計**：
- 所有通訊走同一通道
- 統一的 handler 註冊
- 訊息歷史追蹤

### 3. agent.py (131行) - 基礎執行單元
**角色**：實際的工作單位

**統一介面**：
```python
async def execute(context: TaskContext) → ExecutionResult
```

**Agent 類型**：
- planner.py - 任務規劃
- executor.py - 任務執行
- reviewer.py - 品質審查
- base.py - 抽象基類

### 4. tools.py (69行) - 工具管理器
**角色**：外部能力的統一入口

**工具介面**：
```python
async def execute(**kwargs) → Any
```

**內建工具**：
- files.py - 檔案操作
- python.py - Python 執行
- shell.py - Shell 命令

### 5. llm.py (270行) - 統一 LLM 介面
**角色**：多模型支援的統一入口

**支援的 Provider**：
- OpenAI (預設)
- Anthropic Claude
- Google Gemini
- Azure OpenAI
- Ollama (本地模型)

**統一介面**：
```python
async def generate(messages: List[Dict], tools: Optional[List[Dict]]) → LLMResponse
```

### 6. config.py (124行) - 配置管理
**角色**：統一配置載入

**配置層級**：
1. 預設值 (硬編碼)
2. config.yaml (專案配置)
3. .env (環境變數)
4. 運行時參數

### 7. simple_logger.py (77行) - 極簡日誌
**角色**：人類可讀的日誌系統

**核心功能**：
```python
log(event: str, **data)  # 事件記錄
timer(name: str)         # 效能計時
set_trace(enabled: bool) # 除錯追蹤
```

## 執行流程

```
1. 用戶請求
   main.py 接收用戶輸入
   ↓
2. Kernel 調度
   kernel.execute(request)
   ↓
3. 任務分析
   router.analyzer 判斷複雜度
   ↓
4. 策略選擇
   direct → executor
   sequential → planner + executor
   orchestrated → planner + executor + reviewer
   ↓
5. 代理執行
   通過 CommunicationBus 發送訊息
   代理接收並處理
   ↓
6. 結果返回
   統一的 ExecutionResult 格式
```

## 策略映射 (消除特殊情況)

```python
strategy_to_agent = {
    "direct": "executor",      # 簡單任務直接執行
    "sequential": "executor",   # 順序執行使用執行器
    "orchestrated": "executor", # 編排也是執行器協調
    "parallel": "executor"      # 並行執行器處理
}
# 沒有特殊情況 - 所有策略最終都是執行器
```

## 設計原則

### 1. 延遲載入
- 代理按需創建
- 工具按需載入
- 避免啟動時載入所有模組

### 2. 優雅降級
```python
創建代理失敗 → MinimalAgent
工具不存在 → 返回錯誤訊息
提示不存在 → 使用預設
```

### 3. 統一介面
- 所有代理: `execute(context) → ExecutionResult`
- 所有工具: `execute(**kwargs) → Any`
- 所有通訊: `Message` 格式

### 4. 零配置預設
- 預設使用 executor
- 預設簡單策略
- 預設 OpenAI 模型

## 依賴關係

```
kernel.py 依賴:
  → communication.py (訊息傳遞)
  → router/ (任務分析)
  → agents/ (代理執行)
  → tools/ (工具調用)
  → prompts/ (提示管理)

communication.py 依賴:
  → 無外部依賴 (純粹的訊息管道)

agent.py 依賴:
  → llm.py (LLM 調用)
  → tools.py (工具使用)
  → simple_logger.py (日誌記錄)

tools.py 依賴:
  → 具體工具實作
```

## 為什麼這樣設計？

### Linux Kernel 啟發
1. **中央調度**：像 Linux Kernel 管理進程一樣管理代理
2. **訊息機制**：像 IPC 一樣的統一通訊
3. **模組化**：可插拔的代理和工具

### Linus 哲學實踐
1. **消除特殊情況**：所有策略都映射到執行器
2. **簡單直接**：92行實現完整通訊系統
3. **實用主義**：MinimalAgent 作為後備方案

## 配置系統

### 最小配置 (config.yaml)
```yaml
version: "2.0"
mode: standard

llm:
  provider: openai
  model: gpt-3.5-turbo
  temperature: 0.7
  max_tokens: 2000

tools:
  enabled:
    - python
    - files

routing:
  enabled: true
```

### 環境變數 (.env)
```bash
# 只需設置使用的 Provider 的 API Key
OPENAI_API_KEY=sk-xxx
# ANTHROPIC_API_KEY=sk-ant-xxx
# GOOGLE_API_KEY=xxx
```

## 總結

這個架構實現了：
- ✅ 統一調度 (kernel.py - 254行)
- ✅ 解耦通訊 (communication.py - 92行)
- ✅ 標準介面 (agent.py - 131行, tools.py - 69行)
- ✅ 多模型支援 (llm.py - 270行)
- ✅ 極簡日誌 (simple_logger.py - 77行)
- ✅ 零特殊情況 (策略映射、統一介面)
- ✅ 優雅降級 (MinimalAgent、Fallback)
- ✅ 延遲載入 (按需創建)

**核心代碼總量**：1,270行實現完整的任務調度系統（包含多模型支援）。

**設計亮點**：
1. **Kernel 模式**：像 Linux Kernel 管理資源一樣管理 AI 代理
2. **訊息匯流排**：統一通訊，92行實現完整訊息系統
3. **極簡配置**：3個環境變數 + 20行 YAML
4. **多模型統一**：單一介面支援 5+ LLM Provider