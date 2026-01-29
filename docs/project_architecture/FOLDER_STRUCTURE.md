# 專案結構說明 (Folder Structure)
# Core Agentic Brain - 極簡架構

**更新日期:** 2026-01-29
**版本:** 2.0

---

## 概覽

遵循 Linus Torvalds 的極簡哲學，專案結構經過大幅簡化：
- 核心程式碼從 1238 行減至 ~600 行
- 移除所有不必要的複雜性
- 保持清晰的分層結構

---

## 目錄結構

```
core_agentic_brain/
│
├── 📄 main.py                 # 統一入口 (< 150 行)
├── 📄 config.yaml            # 極簡配置 (24 行)
├── 📄 .env                   # 環境變數 (3-4 個)
├── 📄 .env.example           # 範例配置 (7 行)
├── 📄 README.md              # 專案說明
├── 📄 USAGE_GUIDE.md         # 使用指南 (111 行)
├── 📄 test_config.py         # 配置測試 (51 行)
│
├── 📁 core/                  # Layer 0: 極簡核心
│   ├── agent.py             # 核心執行引擎 (~100 行)
│   ├── simple_logger.py     # 極簡日誌系統 (77 行) ⭐
│   ├── utils.py            # 統一工具函數 (50 行) ⭐
│   ├── logger.py           # 相容層包裝 (32 行)
│   ├── config.py           # 配置載入
│   ├── llm.py             # LLM 提供者介面
│   ├── tools.py           # 工具管理器
│   ├── types.py           # 型別定義
│   └── prompt_loader.py   # 提示詞載入器
│
├── 📁 router/              # Layer 1: 智慧路由
│   ├── analyzer.py        # 任務複雜度分析
│   └── executor.py        # 路由策略執行 (修復雙重包裝)
│
├── 📁 agents/              # 專門化 Agents
│   ├── base.py            # 基礎 Agent 類別
│   ├── planner.py         # 規劃專家
│   ├── executor.py        # 執行專家
│   └── reviewer.py        # 審查專家
│   └── [orchestrator.py]  # 已移至 deprecated/
│
├── 📁 tools/               # 工具實作
│   ├── base.py            # 工具基礎類別
│   └── builtin/           # 內建工具
│       ├── python.py      # Python 執行工具
│       └── files.py       # 檔案操作工具
│       └── [python_pure.py] # 已移至 deprecated/
│
├── 📁 prompts/             # 提示詞模板
│   ├── planner.yaml       # 規劃提示詞
│   ├── executor.yaml      # 執行提示詞
│   ├── reviewer.yaml      # 審查提示詞
│   └── tools.yaml         # 工具提示詞
│   └── [execution.yaml]   # 已移至 deprecated/
│   └── [planning.yaml]    # 已移至 deprecated/
│   └── [general.yaml]     # 已移至 deprecated/
│
├── 📁 config/              # 配置範例
│   └── README.md          # 配置說明
│
├── 📁 deprecated/          # 已棄用檔案 (備份)
│   ├── agents/
│   │   └── orchestrator.py # Layer 2 功能
│   ├── prompts/
│   │   ├── execution.yaml  # 舊版提示詞
│   │   ├── planning.yaml   # 舊版提示詞
│   │   └── general.yaml    # 舊版提示詞
│   └── tools/
│       ├── pure_base.py    # 測試用工具
│       └── python_pure.py  # 測試用工具
│
├── 📁 docs/                # 文檔
│   ├── optimized_logging.md    # 日誌優化說明
│   └── project_architecture/   # 架構文檔
│       ├── 01_System_Architecture.md    # 系統架構 ⭐
│       ├── FOLDER_STRUCTURE.md         # 本文件
│       └── README.md                    # 架構總覽
│
├── 📁 workspace/           # 執行時工作區
│   └── logs/              # 日誌輸出
│
└── 📁 tests/              # 測試檔案
    └── ...

⭐ = 核心簡化成果
```

---

## 核心模組說明

### 🔷 core/ - Layer 0 核心

| 檔案 | 行數 | 功能 |
|------|------|------|
| simple_logger.py | 77 | 極簡日誌，取代 744 行舊系統 |
| utils.py | 50 | 消除特殊情況的統一函數 |
| logger.py | 32 | 向後相容包裝層 |
| agent.py | ~100 | 核心執行引擎 |
| config.py | ~50 | 極簡配置載入 |

### 🔷 router/ - Layer 1 路由

| 檔案 | 功能 |
|------|------|
| analyzer.py | 分析任務複雜度，決定路由策略 |
| executor.py | 執行路由決策，調度 agents |

### 🔷 agents/ - 專門化代理

| Agent | 職責 |
|-------|------|
| planner.py | 制定執行計畫 |
| executor.py | 執行具體任務 |
| reviewer.py | 審查執行結果 |

---

## 簡化成果

### Before vs After

| 項目 | Before | After | 改進 |
|------|--------|-------|------|
| 總程式碼 | 1238 行 | ~600 行 | -51% |
| 日誌系統 | 744 行 | 77 行 | -90% |
| 配置檔案 | 150+ 行 | 24 行 | -84% |
| 環境變數 | 10+ 個 | 3 個 | -70% |
| 特殊情況 | 多處 if/else | 統一處理 | 100% |

### 已移除的複雜性

1. **過度設計的日誌系統**
   - 移除: ComplexLogger, AgentInteractionLogger
   - 替換: simple_logger.py (77 行)

2. **複雜的配置系統**
   - 移除: 10+ 環境變數, 150+ 行配置
   - 替換: 3 個環境變數, 24 行配置

3. **重複的提示詞檔案**
   - 移除: execution.yaml, planning.yaml, general.yaml
   - 保留: 專門化的 agent 提示詞

4. **測試用工具**
   - 移除: python_pure.py, pure_base.py
   - 保留: 生產用的 python.py, files.py

5. **Layer 2 功能**
   - 移除: orchestrator.py
   - 專注: Layer 0 和 Layer 1

---

## 設計原則

### 1. 極簡至上
- 每個檔案都有明確單一的職責
- 沒有超過 100 行的核心模組
- 優先刪除而非新增

### 2. 零特殊情況
- utils.py 提供統一的配置訪問
- simple_logger.py 提供統一的日誌介面
- 沒有散落的 if/else 判斷

### 3. 向後相容
- logger.py 提供相容層
- 舊程式碼可以繼續運行
- 平滑升級路徑

---

## 使用範例

### 最簡啟動
```bash
# 只需要設定 API Key
export OPENAI_API_KEY=sk-...
python3 main.py
```

### 查看結構
```bash
# 統計程式碼行數
find . -name "*.py" -path "./core/*" | xargs wc -l

# 查看簡化成果
wc -l core/simple_logger.py  # 77 行
wc -l core/utils.py          # 50 行
wc -l config.yaml            # 24 行
```

---

## 維護指南

### 新增功能前問自己：
1. ❓ 這真的需要嗎？
2. ❓ 能否用現有功能實現？
3. ❓ 會增加特殊情況嗎？
4. ❓ 能否再簡化？

### 程式碼審查標準：
- ✅ 沒有特殊情況
- ✅ 使用統一介面
- ✅ 少於 100 行
- ✅ 單一職責

---

## 結語

> "Simplicity is the ultimate sophistication."
> - Leonardo da Vinci

這個專案結構體現了真正的極簡主義。每個檔案、每個目錄都有其存在的必要性，沒有冗餘，沒有過度設計。

**Linus Torvalds 會認可這樣的設計。**
