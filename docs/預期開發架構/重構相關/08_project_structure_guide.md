# 專案結構指南 - OpenManus Linus 式重構

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2025-01-22`
**主要作者 (Lead Author):** `Linus-style 技術架構師`
**狀態 (Status):** `活躍 (Active)`

---

## 目錄 (Table of Contents)

- [1. 指南目的 (Purpose of This Guide)](#1-指南目的-purpose-of-this-guide)
- [2. 核心設計原則 (Core Design Principles)](#2-核心設計原則-core-design-principles)
- [3. 頂層目錄結構 (Top-Level Directory Structure)](#3-頂層目錄結構-top-level-directory-structure)
- [4. 目錄詳解 (Directory Breakdown)](#4-目錄詳解-directory-breakdown)
  - [4.1 核心代碼 - core/](#41-核心代碼---core)
  - [4.2 工具實現 - tools/](#42-工具實現---tools)
  - [4.3 Web 界面 - web/](#43-web-界面---web)
  - [4.4 測試代碼 - tests/](#44-測試代碼---tests)
  - [4.5 腳本 - scripts/](#45-腳本---scripts)
- [5. 文件命名約定 (File Naming Conventions)](#5-文件命名約定-file-naming-conventions)
- [6. 演進原則 (Evolution Principles)](#6-演進原則-evolution-principles)

---

## 1. 指南目的 (Purpose of This Guide)

*   為 OpenManus 重構提供極簡、清晰、可維護的目錄結構
*   遵循 Linus 式哲學：簡潔至上，拒絕過度設計
*   確保任何人能在 5 分鐘內理解整個專案結構

## 2. 核心設計原則 (Core Design Principles)

### Linus 式原則應用

| 原則 | OpenManus 實踐 |
| :--- | :--- |
| **扁平優於嵌套** | 最多 3 層目錄深度 |
| **明確優於隱晦** | 文件名直接表達功能 |
| **簡單優於複雜** | 拒絕無意義的分層 |
| **實用優於理論** | 基於實際需求組織 |

### 反模式警告
```python
# ❌ 絕對避免的結構
FORBIDDEN_PATTERNS = [
    "src/app/services/impl/concrete/",  # 過度嵌套
    "common/utils/helpers/misc/",       # 垃圾桶目錄
    "base/abstract/interfaces/",        # 過度抽象
    "__pycache__/",                     # 未忽略的緩存
]
```

## 3. 頂層目錄結構 (Top-Level Directory Structure)

```plaintext
openmanus/
├── main.py              # ⭐ 唯一入口點 (< 50 lines)
├── config.yaml          # ⭐ 主配置檔
├── requirements.txt     # Python 依賴清單
├── README.md           # 專案說明與快速開始
│
├── core/               # 核心邏輯
│   ├── __init__.py
│   ├── agent.py        # 核心 Agent 邏輯 (< 150 lines)
│   ├── llm.py          # LLM 封裝 (< 80 lines)
│   ├── tools.py        # 工具管理器 (< 50 lines)
│   ├── config.py       # 配置載入 (< 50 lines)
│   │
│   # === Claude Code 進階功能 (可選) ===
│   ├── sub_agents.py   # 子代理管理 (< 100 lines)
│   ├── rules_engine.py # 規則引擎 (< 80 lines)
│   ├── agent_skills.py # 技能系統 (< 100 lines)
│   └── mcp_adapter.py  # MCP 協議適配 (< 100 lines)
│
├── configs/            # 進階配置 (可選)
│   ├── sub_agents.yaml # 子代理定義
│   ├── mcp_tools.yaml  # MCP 工具配置
│   └── skills.yaml     # 技能配置
│
├── rules/              # 規則/提示模板 (可選)
│   ├── code_generation.yaml
│   ├── refactoring.yaml
│   ├── debugging.yaml
│   └── testing.yaml
│
├── skills/             # 動態技能實現 (可選)
│   ├── __init__.py
│   ├── code_analysis.py
│   ├── code_generation.py
│   ├── testing.py
│   └── debugging.py
│
├── prompts/            # 提示模板庫 (可選)
│   ├── base/           # 基礎模板
│   ├── specialized/    # 專門化模板
│   └── examples/       # 範例提示
│
├── tools/              # 基礎工具實現 (每個 < 50 lines)
│   ├── __init__.py
│   ├── python.py       # Python 執行工具
│   ├── browser.py      # 網頁獲取工具
│   ├── files.py        # 文件操作工具
│   └── terminal.py     # 終端命令工具
│
├── web/                # Web 模式 (可選)
│   ├── server.py       # FastAPI 服務器 (< 50 lines)
│   └── static/         # 前端檔案
│       ├── index.html  # 單頁應用 (< 100 lines)
│       ├── style.css   # 樣式 (< 200 lines)
│       └── app.js      # 前端邏輯 (< 300 lines)
│
├── tests/              # 測試檔案
│   ├── __init__.py
│   ├── test_agent.py   # Agent 測試
│   ├── test_llm.py     # LLM 測試
│   ├── test_tools.py   # 工具測試
│   ├── test_sub_agents.py # 子代理測試
│   ├── test_rules.py   # 規則測試
│   └── test_skills.py  # 技能測試
│
├── scripts/            # 開發腳本
│   ├── start.sh        # 啟動腳本
│   ├── test.sh         # 測試腳本
│   ├── clean.py        # 清理腳本
│   ├── validate_config.py # 配置驗證
│   └── skill_generator.py # 技能生成器
│
└── workspace/          # 運行時工作區 (git ignored)
    └── .gitkeep
```

### 為什麼這樣設計？

1. **單一入口點 (main.py)**: 消除混亂，用戶只需記住一個檔案
2. **扁平結構**: 沒有無意義的嵌套，找檔案快速直接
3. **功能分組**: 相關功能放在一起，不按"類型"分散
4. **最小依賴**: 每個模組職責單一，依賴清晰

## 4. 目錄詳解 (Directory Breakdown)

### 4.1 核心代碼 - core/

**設計約束**:
```python
CORE_CONSTRAINTS = {
    "total_lines": 300,      # 核心代碼總行數
    "max_file_lines": 100,   # 單檔案最大行數
    "max_functions": 10,     # 單檔案最大函數數
    "max_complexity": 5,     # 最大圈複雜度
}
```

**檔案職責**:

| 檔案 | 職責 | 關鍵函數 | 行數限制 |
| :--- | :--- | :--- | :--- |
| `agent.py` | 協調 LLM 與工具 | `process()` | < 100 |
| `llm.py` | OpenAI API 封裝 | `call()` | < 80 |
| `tools.py` | 工具動態載入 | `load_tools()`, `execute()` | < 50 |
| `config.py` | YAML 配置載入 | `load_config()` | < 30 |

### 4.2 工具實現 - tools/

**統一接口**:
```python
def execute(input: str) -> str:
    """所有工具的統一接口"""
    pass
```

**工具清單**:

| 工具 | 功能 | 輸入格式 | 輸出格式 |
| :--- | :--- | :--- | :--- |
| `python.py` | 執行 Python 代碼 | Python 代碼字串 | 執行結果或錯誤 |
| `browser.py` | 獲取網頁內容 | URL | HTML 內容(前2000字) |
| `files.py` | 文件讀寫 | `read/write path [content]` | 內容或成功訊息 |
| `terminal.py` | 執行 shell 命令 | 命令字串 | 命令輸出 |

### 4.3 Web 界面 - web/

**極簡前端原則**:
- 零框架依賴 (原生 HTML/CSS/JS)
- 單一 HTML 檔案
- WebSocket 實時通信
- 黑色 Hacker 主題

**檔案結構**:
```plaintext
web/
├── server.py           # FastAPI WebSocket 服務
└── static/
    ├── index.html      # 所有 HTML (< 100 lines)
    ├── style.css       # 所有樣式 (< 200 lines)
    └── app.js          # 所有邏輯 (< 300 lines)
```

### 4.4 測試代碼 - tests/

**測試原則**:
```python
TEST_PRINCIPLES = {
    "簡單優先": "手動測試 70%, 自動測試 30%",
    "核心覆蓋": "關鍵路徑 100% 覆蓋",
    "快速執行": "全部測試 < 10 秒",
    "獨立運行": "每個測試可單獨執行"
}
```

**測試組織**:
- 一個源檔案對應一個測試檔案
- 測試函數命名: `test_功能_場景`
- 使用 pytest，無複雜框架

### 4.5 腳本 - scripts/

**實用腳本**:

```bash
# start.sh - 一鍵啟動
#!/bin/bash
python main.py "$@"

# test.sh - 執行測試
#!/bin/bash
pytest tests/ -v

# clean.py - 清理緩存
#!/usr/bin/env python3
import shutil
shutil.rmtree("__pycache__", ignore_errors=True)
```

## 5. 文件命名約定 (File Naming Conventions)

### 嚴格規則

| 類型 | 命名規則 | 正確範例 | 錯誤範例 |
| :--- | :--- | :--- | :--- |
| **Python 模組** | snake_case.py | `tool_manager.py` | `ToolManager.py` |
| **測試檔案** | test_*.py | `test_agent.py` | `agent_test.py` |
| **配置檔案** | 名詞.yaml/json | `config.yaml` | `configuration.yml` |
| **腳本檔案** | 動詞.sh/py | `start.sh`, `clean.py` | `startup_script.sh` |
| **文檔** | UPPERCASE.md | `README.md` | `readme.MD` |

### 禁止的命名
```python
FORBIDDEN_NAMES = [
    "utils.py",      # 太模糊
    "helpers.py",    # 垃圾桶
    "common.py",     # 無意義
    "base.py",       # 過度抽象
    "manager.py",    # 不具體
    "service.py",    # 太通用
]
```

## 6. 演進原則 (Evolution Principles)

### 何時可以改變結構？

1. **添加新工具**: 直接在 `tools/` 下創建新檔案
2. **優化性能**: 保持接口不變的前提下重構
3. **修復 bug**: 最小改動原則

### 何時不能改變結構？

1. **"感覺"不夠優雅**: 實用性 > 優雅
2. **想要更多抽象**: 拒絕過度設計
3. **追求"最佳實踐"**: 簡單就是最佳實踐

### 變更決策流程

```python
def should_change_structure(change_proposal):
    """Linus 式結構變更決策"""

    # 第一問：解決真實問題嗎？
    if not change_proposal.solves_real_problem:
        return False  # "這是在解決不存在的問題"

    # 第二問：會讓代碼更簡單嗎？
    if change_proposal.adds_complexity:
        return False  # "複雜性是萬惡之源"

    # 第三問：會破壞現有功能嗎？
    if change_proposal.breaks_compatibility:
        return False  # "Never break userspace"

    return True
```

### 代碼行數監控

```bash
# 監控腳本 - 確保不超過限制
#!/bin/bash

echo "=== OpenManus 代碼行數統計 ==="
echo "核心代碼 (目標 < 300 行):"
wc -l core/*.py | grep -v __pycache__

echo "單個工具 (目標 < 50 行):"
for file in tools/*.py; do
    lines=$(wc -l < "$file")
    if [ $lines -gt 50 ]; then
        echo "⚠️  $file: $lines 行 (超標!)"
    else
        echo "✅ $file: $lines 行"
    fi
done

echo "總代碼量 (目標 < 900 行):"
find . -name "*.py" -not -path "./tests/*" | xargs wc -l | tail -1
```

---

## 記住 Linus 的智慧

> "如果你需要超過 3 層縮排，你就已經完蛋了，應該修復你的程序。"

> "好的程式設計師知道寫什麼。偉大的程式設計師知道不寫什麼。"

> "完美不是當你無法再添加任何東西時，而是當你無法再移除任何東西時。"

---

**批准簽字**:
- Linus-style Tech Lead: 待批准
- 核心開發團隊: 待批准

**實施檢查清單**:
- [ ] 核心代碼 < 300 行
- [ ] 單個檔案 < 100 行
- [ ] 單個函數 < 20 行
- [ ] 目錄深度 <= 3 層
- [ ] 零循環依賴
- [ ] 5 分鐘可理解