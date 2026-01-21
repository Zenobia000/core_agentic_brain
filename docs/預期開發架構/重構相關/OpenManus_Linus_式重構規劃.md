# OpenManus Linus 式重構規劃

**評估日期**: 2025-01-21
**評估原則**: CLAUDE.md 中的 Linus Torvalds 技術哲學
**結論**: 現有架構無法挽救，需要完全重寫

---

## 🔥 致命診斷

### 當前狀況：技術債務爆表

**品味評分**: 🔴 垃圾

OpenManus 是典型的"我會做所有事情"綜合症案例。作者想同時支援所有可能的使用場景，結果創造了一個沒人知道怎麼用的怪物。

### 核心問題

1. **入口點混亂** - 6個不同的執行檔案，沒有人知道該用哪個
2. **過度抽象** - 3層無意義的類繼承，為了抽象而抽象
3. **工具系統腫脹** - 硬編碼工具註冊，無法動態擴展
4. **配置地獄** - .env + config.toml + 硬編碼常數分散各處
5. **測試形同虛設** - 測試檔案存在但不能反映真實使用情況

---

## 💀 Linus 式批評

> "這是在解決不存在的問題。真正的問題是沒有人能簡單地用這個東西。"

### 數據結構災難

```python
# 現在：垃圾
class Manus(ToolCallAgent):
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            PythonExecute(),
            BrowserUseTool(),
            # ...硬編碼的工具列表
        )
    )
```

**分析**: 工具應該是簡單的函數映射表，不需要類。這種設計讓動態工具載入變成不可能。

### 特殊情況爆炸

```python
# main.py 中的無意義判斷
prompt = args.prompt if args.prompt else input("Enter your prompt: ")

# 又一個特殊情況列表
special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])
```

**分析**: 每個特殊情況都是設計失敗的證據。好的設計沒有特殊情況。

---

## ⚡ 重構戰略

### 階段 0: 立即處理（生存問題）

**目標**: 讓用戶能夠使用這個工具

1. **統一入口點**
   - 砍掉所有 `run_*.py`
   - 只保留 `python main.py [command]`
   - 所有模式通過命令行參數切換

2. **簡化工具系統**
   - 工具即函數，取消類繼承
   - 統一工具接口：`(input: str) -> str`
   - 動態工具載入

### 階段 1: 核心架構重建（一週內）

**目標**: 建立可維護的核心架構

3. **統一配置管理**
   - 一個 `config.yaml` 解決所有配置
   - 環境變數覆蓋機制
   - 配置驗證和預設值

4. **移除無用抽象**
   - 砍掉 90% 的類定義
   - 保留核心邏輯：prompt -> LLM -> tool_call -> result
   - 消除所有 Pydantic 模型（除非真正需要）

### 階段 2: 品質改善（之後慢慢來）

5. **測試覆蓋**
   - 核心邏輯的單元測試
   - 工具集成測試
   - 配置驗證測試

6. **文檔同步**
   - README 與實際代碼保持一致
   - 添加使用範例
   - API 文檔生成

---

## 🎯 理想架構

### 目錄結構（簡化版）

```
openmanus/
├── main.py              # 唯一入口點
├── config.yaml         # 唯一配置檔
├── core/
│   ├── agent.py        # 核心 agent 邏輯（~100行）
│   ├── tools.py        # 工具註冊和調用（~50行）
│   └── config.py       # 配置管理（~30行）
├── tools/
│   ├── python.py       # Python 執行工具
│   ├── browser.py      # 瀏覽器工具
│   └── ...             # 其他工具，每個都是簡單函數
└── tests/
    └── test_*.py       # 真正的測試
```

### 核心代碼（偽代碼）

```python
# main.py - 應該少於 50 行
def main():
    config = load_config("config.yaml")
    agent = Agent(config)

    while True:
        prompt = get_user_input()
        result = agent.process(prompt)
        print(result)

# core/agent.py - 應該少於 100 行
class Agent:
    def __init__(self, config):
        self.llm = LLM(config.llm)
        self.tools = load_tools(config.tools)

    def process(self, prompt: str) -> str:
        while not self.is_done():
            response = self.llm.chat(prompt)
            if tool_call := self.extract_tool_call(response):
                result = self.tools[tool_call.name](tool_call.args)
                prompt += f"\nTool result: {result}"
            else:
                return response
```

---

## 🚀 實施計劃

### 週次規劃

**第 1 週**: 階段 0 - 生存
- [ ] 建立新的 main.py
- [ ] 實現基本的 Agent 類
- [ ] 移植核心工具（Python、Browser）
- [ ] 基本配置系統

**第 2 週**: 階段 1 - 重建
- [ ] 完整配置管理
- [ ] 工具動態載入
- [ ] MCP 工具集成（如果需要）
- [ ] 基本測試框架

**第 3-4 週**: 階段 2 - 品質
- [ ] 完整測試覆蓋
- [ ] 文檔更新
- [ ] 性能優化
- [ ] 發布準備

### 成功指標

1. **用戶體驗**: `python main.py` 就能工作
2. **代碼量**: 核心代碼少於 500 行
3. **配置**: 一個檔案解決所有配置
4. **擴展性**: 添加新工具只需要實現一個函數
5. **測試**: 核心功能有完整測試覆蓋

---

## ⚠️ 風險和注意事項

### 技術風險

1. **MCP 協議依賴** - 可能需要保留部分複雜性
2. **瀏覽器集成** - 不要為了 "完美" 犧牲簡潔
3. **向後兼容** - 沒有用戶，所以沒有兼容性負擔

### 實施風險

1. **功能丟失** - 某些邊緣功能可能會暫時消失
2. **文檔滯後** - 代碼改變快，文檔跟不上
3. **測試債務** - 可能需要重寫大量測試

### 緩解策略

1. **漸進式重寫** - 保留舊版本作為參考
2. **功能對等** - 確保核心功能不丟失
3. **早期測試** - 每個階段都要有可工作的版本

---

## 🎖️ Linus 的智慧指引

> "好的程式設計師知道寫什麼。偉大的程式設計師知道重寫什麼。"

這個專案需要的不是修補，而是重新思考。當前的複雜性不是來自問題的本質複雜性，而是來自錯誤的抽象和過度設計。

**記住核心原則**:
- 工具就是函數
- 配置就是數據
- 簡潔勝過複雜
- 可工作勝過完美

**最終目標**: 讓任何人都能在 5 分鐘內理解和使用 OpenManus。

---

*"在懷疑時，使用蠻力。" - Ken Thompson*

*"完美的設計不是當你無法再添加任何東西時，而是當你無法再移除任何東西時。" - Antoine de Saint-Exupéry*