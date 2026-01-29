# Core Agentic Brain - 架構文檔總覽

**版本:** 2.0
**更新日期:** 2026-01-29
**哲學:** Linus Torvalds 極簡主義

---

## 🎯 專案願景

> "Good taste has no special cases."
> - Linus Torvalds

Core Agentic Brain 是一個極簡的 AI Agent 平台，透過消除特殊情況、簡化配置、統一介面，實現真正的優雅設計。

### 核心成果
- **程式碼:** 1238 → ~600 行 (-51%)
- **日誌系統:** 744 → 77 行 (-90%)
- **配置:** 10+ 環境變數 → 3 個
- **響應速度:** < 1 秒
- **日誌輸出:** 8-15 行/請求

---

## 📚 文檔結構

### 1. [系統架構](01_System_Architecture.md) ⭐
極簡分層架構的完整說明，包含 Linus 哲學實踐與簡化成果。

**重點內容:**
- Layer 0 極簡核心 (< 300 行)
- Layer 1 智慧路由
- 簡化前後對比
- 效能指標

### 2. [專案結構](FOLDER_STRUCTURE.md) ⭐
詳細的目錄組織與檔案說明。

**重點內容:**
- 精簡後的檔案結構
- 核心模組說明
- 已移除的複雜性
- 維護指南

### 3. [系統設計](02_System_Design.md)
詳細的設計決策與實作細節。

### 4. [技術實作指南](03_Technical_Implementation_Guide.md)
開發者實作參考。

### 5. [API 規格](04_API_Specification.md)
介面定義與使用說明。

---

## 🚀 快速開始

### 最簡配置
```bash
# 1. 設定 API Key
export OPENAI_API_KEY=sk-...

# 2. 啟動系統
python3 main.py
```

### 驗證簡化成果
```bash
# 查看核心模組行數
wc -l core/simple_logger.py  # 77 行
wc -l core/utils.py          # 50 行
wc -l config.yaml            # 24 行

# 測試執行
echo "你好" | python3 main.py
```

---

## 🏗 架構精華

### Layer 0: 極簡核心
```python
# 3 行啟動一個 Agent
from core.agent import Agent
agent = Agent(config)
response = agent.run("你好")
```

**核心檔案:**
- `simple_logger.py` - 77 行極簡日誌
- `utils.py` - 50 行統一工具
- `agent.py` - ~100 行執行引擎

### Layer 1: 智慧路由
```python
# 智慧任務分配
analyzer = TaskAnalyzer()
decision = analyzer.analyze(context)
result = executor.execute(decision, context)
```

**路由元件:**
- `analyzer.py` - 任務分析
- `executor.py` - 策略執行
- 專門化 Agents (planner, executor, reviewer)

---

## 💎 Linus 哲學實踐

### 1. 消除特殊情況

**Before:**
```python
if config and 'llm' in config:
    if 'core' in config and 'llm' in config['core']:
        llm_config = config['core']['llm']
    elif 'llm' in config:
        llm_config = config['llm']
    else:
        llm_config = {}
```

**After:**
```python
llm_config = get_config_value(config, "core", "llm")
```

### 2. 極簡日誌

**Before:** 744 行複雜系統
**After:** 77 行簡單函數

```python
def log(event: str, **data):
    """記錄事件 - 就這麼簡單"""
    entry = {'ts': time.strftime('%H:%M:%S'), 'event': event, **data}
    print(format_entry(entry))
```

### 3. 最小配置

**Before:** 10+ 環境變數, 150+ 行 YAML
**After:** 3 個環境變數, 24 行 YAML

```bash
OPENAI_API_KEY=sk-...  # 必要
LOG_HUMAN=true         # 可選
LOG_DEBUG=false        # 可選
```

---

## 📊 簡化指標

| 類別 | 原始 | 現在 | 減少 |
|------|------|------|------|
| 核心程式碼 | 1238 行 | ~600 行 | 51% |
| 日誌系統 | 744 行 | 77 行 | 90% |
| 配置系統 | 150+ 行 | 24 行 | 84% |
| 環境變數 | 10+ 個 | 3 個 | 70% |
| 請求日誌 | 50+ 行 | 8-15 行 | 70% |

---

## 🔄 最近更新

### v2.0 (2026-01-29)
- ✅ 實施 Linus Torvalds 程式碼審查
- ✅ 簡化日誌系統 (744 → 77 行)
- ✅ 統一配置訪問 (消除特殊情況)
- ✅ 修復 agent_logger 錯誤
- ✅ 清理過時檔案
- ✅ 更新所有架構文檔

### v1.0 (2026-01-27)
- 初始架構設計
- Layer 0/1/2 分層實作

---

## 🛠 維護原則

### 新功能檢查清單
- [ ] 真的需要嗎？
- [ ] 能用現有功能實現嗎？
- [ ] 會增加特殊情況嗎？
- [ ] 能再簡化嗎？

### 程式碼標準
- 無特殊情況
- 統一介面
- < 100 行/模組
- 單一職責

---

## 📖 延伸閱讀

- [Linus Torvalds on Good Taste](https://medium.com/@bartobri/applying-the-linus-tarvolds-good-taste-coding-requirement-99749f37684a)
- [The Art of Unix Programming](http://www.catb.org/~esr/writings/taoup/html/)
- [Clean Code](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)

---

## 🏆 結語

> "Perfection is achieved not when there is nothing more to add,
> but when there is nothing left to take away."
> - Antoine de Saint-Exupéry

Core Agentic Brain 不只是一個 AI Agent 平台，更是極簡設計哲學的實踐。透過持續簡化、消除特殊情況、保持好品味，我們創造了一個真正優雅的系統。

**Linus 會說：「終於有人懂了。」**

---

*本文檔持續更新中，歡迎貢獻與回饋。*
