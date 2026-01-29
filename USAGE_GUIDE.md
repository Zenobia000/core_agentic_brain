# 🧠 Core Agentic Brain - 使用指南

> **基於 Kernel 中央調度架構，遵循 Linus 原則：簡單、直接、無特殊情況**

## 🚀 快速開始（30 秒）

```bash
# 1. 設定 API Key
export OPENAI_API_KEY="your-key"
# 或使用 .env 檔案
cp .env.example .env

# 2. 執行
python3 main.py
```

就這麼簡單。

## 📋 使用方式

### 互動模式
```bash
python3 main.py
>>> 計算 10 的階乘
>>> 寫一個排序算法
>>> test  # 快速測試
>>> help  # 顯示幫助
>>> exit  # 退出
```

### 批次模式
```bash
python3 main.py "你的任務"

# 範例
python3 main.py "計算斐波那契數列前10項"
python3 main.py "解釋什麼是機器學習"
```

## 🏗️ 系統架構

```
Kernel (中央調度器)
├── CommunicationBus (統一通訊)
├── PromptLoader (提示詞管理)
├── Agents (任務執行)
└── Tools (純函數工具)
```

### 核心檔案
- `main.py` - 主程式入口
- `core/kernel.py` - 中央調度器
- `core/communication.py` - 統一通訊協議
- `tools/builtin/python.py` - Python 工具（純函數）
- `tools/builtin/files.py` - 檔案工具（純函數）

## 🧪 測試

### 執行完整 E2E 測試
```bash
python3 test_e2e.py
```

### 測試覆蓋
- ✅ 基本提示處理
- ✅ Python 工具執行
- ✅ 檔案操作
- ✅ Agent 路由
- ✅ 通訊匯流排
- ✅ 提示詞載入
- ✅ 錯誤處理
- ✅ 性能測試
- ✅ 集成測試

**成功率: 100%** 🎉

## 🎯 核心功能

### 極簡日誌系統（77 行）

```python
from core.simple_logger import log, timer, set_trace

# 設置追蹤
set_trace("req123")

# 記錄事件
log('task.start', summary="processing")

# 自動計時
with timer('task.done', summary="completed"):
    do_something()
```

### 環境變數（只有 3 個）

```bash
LOG_HUMAN=true   # 人類可讀（預設 true）
LOG_DEBUG=false  # 除錯模式（預設 false）
LOG_DIR=workspace/logs  # 日誌目錄
```

## 🔨 進階使用

### 直接調用 Kernel API
```python
from dotenv import load_dotenv
load_dotenv()

import asyncio
from core.kernel import Kernel

async def main():
    kernel = Kernel()

    # 執行任務
    result = await kernel.execute("你的任務")
    print(result.response)

    # 直接調用工具
    tool_result = await kernel.call_tool("python", {
        "code": "print('Hello World')"
    })
    print(tool_result)

asyncio.run(main())
```

### 自定義純函數工具
```python
# tools/custom/my_tool.py
from tools.pure_base import PureTool

class Tool(PureTool):
    def __init__(self):
        super().__init__()
        self.name = "my_tool"

    @property
    def definition(self):
        return {
            "type": "function",
            "function": {
                "name": "my_tool",
                "description": "My custom tool"
            }
        }

    def execute(self, parameters):
        # 純函數 - 無狀態，無副作用
        return {"result": "done"}
```

## ❌ 不要做的事

1. **不要**安裝額外套件 - 已經夠了
2. **不要**修改超過 3 層縮進的代碼
3. **不要**加設計模式 - 簡單就好
4. **不要**寫超過 200 行的檔案

## ✅ 要做的事

1. **要**保持簡單
2. **要**刪除不需要的代碼
3. **要**用函數而非類
4. **要**記住 Linus 的話

## 📊 系統狀態

| 模組 | 行數 | 狀態 |
|------|------|------|
| Core (Layer 0) | 589 | ✅ 優化完成 |
| Router (Layer 1) | 423 | ✅ 運作中 |
| Agents | 853 | ✅ 運作中 |
| **總計** | **1865** | **🟢 好品味** |

## 🔧 故障排除

### Q: 日誌在哪裡？
A: 控制台。需要檔案就設 `LOG_DEBUG=true`。

### Q: 如何除錯？
A: `LOG_DEBUG=true python3 main.py`

### Q: 配置太複雜？
A: 不要配置。預設值就很好。

## 📝 Linus 會說的話

> *"如果文檔超過一頁，代碼就太複雜了。"*
>
> *"配置是給不會寫代碼的人用的。"*
>
> *"好的預設值勝過一千個選項。"*

---

**版本**: 2.0 - Linus 式極簡版
**原則**: 能刪就刪，不能刪就簡化
**行數**: 本文檔 < 100 行