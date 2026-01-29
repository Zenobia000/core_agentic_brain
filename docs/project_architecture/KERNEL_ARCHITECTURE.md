# 🧠 Kernel 中央調度架構

## 概述

基於 Linus Torvalds 的設計原則，我們實作了 **Kernel 中央調度架構**，解決了原有的溝通問題。

## 問題分析

### 原架構問題
```
Agent ──> PromptLoader ──> prompts/*.yaml
  │
  ├──> ToolManager ──> Tool
                         │
                         └──> PromptLoader ──> prompts/*.yaml
```

**Linus 會說：「這是垃圾！」**
- ❌ 兩條路徑載入提示詞 - 違反 DRY
- ❌ PromptLoader 被多處呼叫 - 沒有單一真相來源
- ❌ Tool 自己載入提示詞 - 責任不清晰

### 新架構解決方案
```
     Request
        │
        ▼
    [Kernel]  ← 單一調度點
    /   |   \
   /    |    \
Agent Tool Prompt
  ↑     ↑     ↑
  └─────┴─────┘
   統一介面，沒有特殊情況
```

## 核心組件

### 1. Kernel (`core/kernel.py`)
**系統核心 - 單一調度器**

```python
class Kernel:
    """系統核心 - 像 Linux Kernel"""

    def __init__(self):
        self.bus = CommunicationBus()    # 統一通訊
        self.prompts = PromptLoader()     # 單一提示詞源
        self.agents = {}                  # 動態代理
        self.tools = {}                   # 純函數工具
```

**職責**：
- 統一資源管理
- 單一調度入口
- 訊息路由

### 2. CommunicationBus (`core/communication.py`)
**中央通訊匯流排**

```python
class Message:
    """統一訊息格式 - 沒有特殊情況"""
    type: MessageType
    content: Any
    source: str
    target: str
    metadata: Dict

class CommunicationBus:
    """統一訊息傳遞"""
    async def send(message: Message) -> Any
```

**特點**：
- 統一訊息格式
- 沒有 if/else 特殊處理
- 清晰的訊息歷史

### 3. PureTool (`tools/pure_base.py`)
**純函數工具基類**

```python
class PureTool:
    """純函數工具 - 無狀態，無副作用"""

    def execute(parameters: Dict) -> Dict:
        # 只做一件事，做好
        pass
```

**Linus 原則應用**：
- 工具不知道提示詞
- 工具不知道代理
- 工具只執行任務

## 設計決策

### 1. 提示詞管理
**決策**：預載入，單一來源
```python
# 啟動時載入所有提示詞
kernel = Kernel()  # 一次載入
prompt = kernel.get_prompt("planner.system")  # 統一獲取
```

### 2. 工具設計
**決策**：純函數，無狀態
```python
# 工具是純函數
tool.execute({"code": "print('hello')"})  # 輸入→輸出
```

### 3. 代理包裝
**決策**：Kernel 感知的包裝器
```python
class KernelAwareAgent:
    # 代理從 Kernel 獲取資源
    # 不直接依賴 PromptLoader
```

## 使用範例

### 基本使用
```python
# 初始化
kernel = Kernel()

# 執行任務
result = await kernel.execute("寫一個排序算法")

# 調用工具
output = await kernel.call_tool("python", {"code": "print(1+1)"})
```

### 訊息傳遞
```python
# 創建訊息
msg = Message(
    type=MessageType.TOOL_CALL,
    content={"code": "print('hello')"},
    source="user",
    target="tool.python"
)

# 發送訊息
result = await kernel.bus.send(msg)
```

## 遷移指南

### 舊代碼
```python
# 代理直接載入提示詞
from core.prompt_loader import get_prompt_loader
loader = get_prompt_loader()
prompt = loader.get("planner.system")

# 工具載入提示詞
self.prompt_loader = get_prompt_loader()
```

### 新代碼
```python
# 透過 Kernel 統一管理
kernel = Kernel()
prompt = kernel.get_prompt("planner.system")

# 工具是純函數
# 不需要載入提示詞
```

## 優勢總結

### 1. Good Taste（好品味）
- ✅ 消除特殊情況
- ✅ 統一介面
- ✅ 清晰的責任劃分

### 2. Simplicity（簡單性）
- ✅ 單一調度點
- ✅ 減少依賴
- ✅ 程式碼更短

### 3. Maintainability（可維護性）
- ✅ 單一真相來源
- ✅ 清晰的資料流
- ✅ 易於測試

## 測試

執行測試：
```bash
python3 test_kernel.py
```

執行範例：
```bash
python3 example_kernel_usage.py
```

## Linus 會怎麼說？

> "Good taste - 你們終於消除了那些該死的特殊情況。"

> "這才是正確的架構 - 資料在管道中流動，而不是到處亂跳。"

> "簡單直接，沒有過度設計的垃圾。"

## 檔案結構

```
core/
├── kernel.py           # 系統核心
├── communication.py    # 通訊協議
├── prompt_loader.py   # 提示詞載入器
└── types.py           # 類型定義

tools/
├── pure_base.py       # 純函數基類
└── builtin/
    └── python_pure.py # Python 工具（純函數版）

tests/
├── test_kernel.py     # 核心測試
└── example_kernel_usage.py # 使用範例
```

## 下一步

1. **完全移除舊依賴**
   - 更新所有代理使用 Kernel
   - 轉換所有工具為純函數

2. **效能優化**
   - 實作提示詞快取
   - 優化訊息路由

3. **擴展功能**
   - 添加更多純函數工具
   - 支援並行執行

---

*"Talk is cheap. Show me the code."* - Linus Torvalds

*架構設計完成，基於 Linus 原則：簡單、實用、無特殊情況。*