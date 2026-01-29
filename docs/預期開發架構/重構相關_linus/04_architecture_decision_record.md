# 架構決策記錄 - OpenManus Linus 式重構

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2025-01-21`
**主要作者 (Lead Author):** `Linus-style 架構師`
**審核者 (Reviewers):** `Tech Lead, 核心開發團隊`
**狀態 (Status):** `已批准 (Approved)`

---

## 目錄 (Table of Contents)

1. [ADR 方法論 (ADR Methodology)](#第-1-部分adr-方法論-adr-methodology)
2. [核心架構決策 (Core Architecture Decisions)](#第-2-部分核心架構決策-core-architecture-decisions)
3. [技術選型決策 (Technology Selection Decisions)](#第-3-部分技術選型決策-technology-selection-decisions)
4. [實施策略決策 (Implementation Strategy Decisions)](#第-4-部分實施策略決策-implementation-strategy-decisions)

---

**目的**: 記錄 OpenManus 重構專案中所有重要的架構決策，確保決策邏輯清晰可追溯，並遵循 Linus Torvalds 的技術哲學。

---

## 第 1 部分：ADR 方法論 (ADR Methodology)

### 1.1 決策記錄原則

#### Linus 式決策哲學
> **"技術決策應該基於實際需求和工程直覺，而非流行趨勢或理論完美。"**

| 決策原則 | 具體應用 | 評估標準 |
| :--- | :--- | :--- |
| **實用主義優先** | 選擇解決實際問題的技術 | 是否直接解決當前痛點 |
| **簡潔性導向** | 偏好更簡單的解決方案 | 代碼行數、複雜度、依賴數量 |
| **可維護性** | 考慮長期維護成本 | 新人理解時間、修改難度 |
| **性能影響** | 評估對系統性能的影響 | 啟動時間、響應時間、資源使用 |

#### 決策文檔模板
```markdown
# ADR-XXX: [決策標題]

## 狀態
[提案中 / 已接受 / 已棄用 / 已取代]

## 背景
[為什麼需要做這個決策？當前問題是什麼？]

## 決策
[我們選擇了什麼方案？]

## 理由
[為什麼選擇這個方案？Linus 哲學如何支持這個選擇？]

## 後果
[這個決策帶來的正面和負面影響]

## 替代方案
[考慮過但拒絕的其他選項]
```

---

## 第 2 部分：核心架構決策 (Core Architecture Decisions)

### ADR-001: 採用函數式 + 簡單類的架構模式

#### 狀態
✅ **已接受** (2025-01-21)

#### 背景
原系統採用了 3 層類繼承 `Manus(ToolCallAgent(Agent(BaseModel)))`，造成：
- 複雜的繼承關係難以理解
- 過度抽象，為了抽象而抽象
- 修改困難，牽一髮動全身
- 新開發者學習成本高

#### 決策
採用函數式編程 + 簡單數據類的混合架構：
- 核心邏輯使用純函數實現
- 數據結構使用簡單的 `@dataclass`
- Agent 類只作為函數組織器，不承載複雜邏輯
- 工具系統完全基於函數

#### 理由 (Linus 哲學支持)
- **Good Taste**: 消除不必要的抽象層
- **Simplicity First**: 函數比類繼承更簡單直接
- **Data Structures First**: "數據結構決定算法"
- **No Broken Abstractions**: 避免洩漏抽象的問題

#### 後果
**正面影響**:
- 代碼更容易理解和測試
- 函數級別的可組合性
- 更好的性能（減少對象創建開銷）
- 更容易並發處理

**負面影響**:
- 可能需要更多的參數傳遞
- 某些 OOP 模式無法使用

#### 替代方案
- **保留原有繼承結構**: 拒絕，複雜性過高
- **純函數式**: 拒絕，Python 不是純函數式語言
- **微服務架構**: 拒絕，過度設計

### ADR-002: 統一入口點設計

#### 狀態
✅ **已接受** (2025-01-21)

#### 背景
原系統有 6 個不同的入口點：
- `main.py`
- `run_flow.py`
- `run_mcp.py`
- `run_mcp_server.py`
- `sandbox_main.py`
- `web_run.py`

用戶不知道該使用哪一個，造成困惑和維護負擔。

#### 決策
建立單一入口點 `main.py`，通過命令行參數控制不同模式：
- `python main.py` - 互動模式
- `python main.py --prompt "..."` - 直接執行模式
- `python main.py --web` - Web 服務模式

#### 理由 (Linus 哲學支持)
- **Never Break Userspace**: 用戶只需要記住一個命令
- **Simplicity First**: 單一入口點比多個入口點簡單
- **Good Taste**: 消除特殊情況，統一用戶體驗

#### 後果
**正面影響**:
- 用戶體驗大幅改善
- 文檔和教學更簡單
- 維護成本降低
- 部署更簡單

**負面影響**:
- 需要重構現有的啟動邏輯
- 參數解析稍微複雜

### ADR-003: 零特殊情況的工具系統

#### 狀態
✅ **已接受** (2025-01-21)

#### 背景
原系統工具處理充滿特殊情況：
```python
if tool_name == "BrowserUseTool":
    # 特殊處理邏輯
elif tool_name == "PythonExecute":
    # 另一種特殊處理
```

這違反了 Linus 的 "Good Taste" 原則。

#### 決策
所有工具實現統一介面：`execute(input: str) -> str`
- 輸入統一為字符串
- 輸出統一為字符串
- 錯誤處理統一格式
- 動態載入機制統一

#### 理由 (Linus 哲學支持)
- **Good Taste**: "好的代碼沒有特殊情況"
- **Uniform Interface**: 統一介面降低認知負擔
- **Composability**: 統一介面使工具可組合

#### 後果
**正面影響**:
- 新工具開發極其簡單
- 工具可以被任意組合
- 測試更容易
- 擴展性大幅提升

**負面影響**:
- 某些工具可能需要字符串解析輸入
- 類型安全性略微降低

### ADR-004: 單一配置檔案策略

#### 狀態
✅ **已接受** (2025-01-21)

#### 背景
原系統配置分散在多個文件中：
- `.env` - 環境變數
- `config.toml` - 主要配置
- 代碼中硬編碼的常數

配置管理混亂，難以追蹤和修改。

#### 決策
採用單一 YAML 配置檔案 `config.yaml`：
- 所有配置集中在一個檔案
- 支持環境變數替換
- 清晰的配置分組
- 人類可讀的格式

#### 理由
- **Single Source of Truth**: 配置的唯一事實來源
- **Simplicity**: 一個檔案比多個檔案簡單
- **Maintainability**: 集中管理更容易維護

#### 後果
**正面影響**:
- 配置管理大幅簡化
- 部署更容易
- 配置錯誤更容易排查

**負面影響**:
- 需要 YAML 解析依賴

---

## 第 3 部分：技術選型決策 (Technology Selection Decisions)

### ADR-005: 拒絕前端框架，採用原生 HTML/CSS/JavaScript

#### 狀態
✅ **已接受** (2025-01-21)

#### 背景
需要選擇前端技術棧來實現 Web 界面。主要候選方案：
- React + TypeScript + 復雜工具鏈
- Vue.js + 構建系統
- Angular + 完整框架
- 原生 HTML/CSS/JavaScript

#### 決策
選擇原生 HTML/CSS/JavaScript，完全不使用任何框架。

#### 理由 (Linus 哲學支持)
- **Simplicity First**: 原生技術最簡單，無額外複雜性
- **No Dependencies**: 零前端依賴，減少複雜性
- **Full Control**: 完全控制每一行代碼
- **Performance**: 無框架開銷，最佳性能
- **Learning Curve**: 任何懂基本 Web 技術的人都能維護

**Linus 式批評其他選項**:
- React: "為什麼聊天界面需要虛擬 DOM？"
- TypeScript: "為 JavaScript 增加不必要的編譯複雜性"
- 構建工具: "瀏覽器已經能直接運行 JavaScript，為什麼需要構建？"

#### 後果
**正面影響**:
- 零依賴，永遠不會有依賴地獄
- 載入速度最快
- 調試最簡單
- 維護成本最低
- 文件大小最小

**負面影響**:
- 需要手動管理 DOM
- 某些現代開發體驗功能缺失

#### 替代方案
- **React**: 拒絕，過度複雜
- **Vue**: 拒絕，不必要的抽象
- **Svelte**: 拒絕，仍然需要構建步驟

### ADR-006: 選擇 FastAPI 但僅用於 WebSocket

#### 狀態
✅ **已接受** (2025-01-21)

#### 背景
需要 Web 框架來支持 WebSocket 通信。選項：
- Django: 完整框架
- Flask: 輕量框架
- FastAPI: 現代異步框架
- 原生 WebSocket 服務器

#### 決策
選擇 FastAPI，但僅使用 WebSocket 功能，不使用其他特性。

#### 理由
- **Minimal Usage**: 只用必要的 WebSocket 功能
- **Performance**: 異步支持，性能優秀
- **Simplicity**: API 簡潔清晰
- **No Over-Engineering**: 不使用 FastAPI 的複雜特性

#### 限制條件
```python
# 明確限制 FastAPI 使用範圍
FASTAPI_USAGE_CONSTRAINTS = {
    "allowed": [
        "WebSocket 端點",
        "靜態文件服務"
    ],
    "forbidden": [
        "復雜的路由系統",
        "依賴注入系統",
        "中間件系統",
        "資料庫整合",
        "身份驗證系統"
    ]
}
```

### ADR-007: 拒絕數據庫，採用文件系統存儲

#### 狀態
✅ **已接受** (2025-01-21)

#### 背景
需要決定是否使用數據庫來存儲對話歷史和配置。

#### 決策
完全不使用任何數據庫系統，包括 SQLite。

#### 理由 (Linus 哲學支持)
- **YAGNI**: "你不會需要它" - 數據庫過度設計
- **Simplicity**: 文件系統比數據庫簡單
- **No Dependencies**: 避免數據庫依賴
- **Stateless Design**: AI 對話本質上是無狀態的

**問題分析**:
- 這是個聊天工具，不是企業級應用
- 對話歷史可以用簡單的日誌文件
- 配置已經在 YAML 檔案中
- 不需要複雜查詢或事務

#### 後果
**正面影響**:
- 部署極其簡單
- 備份就是複製文件
- 沒有數據庫遷移問題
- 故障排除更容易

**負面影響**:
- 無法做複雜的歷史查詢
- 並發訪問需要小心處理

### ADR-008: 依賴庫最小化策略

#### 狀態
✅ **已接受** (2025-01-21)

#### 背景
需要確定允許的外部依賴範圍。

#### 決策
嚴格限制外部依賴，僅允許絕對必要的庫：

```python
APPROVED_DEPENDENCIES = {
    "fastapi": "WebSocket 支持",
    "uvicorn": "ASGI 服務器",
    "pyyaml": "配置檔案解析",
    "requests": "HTTP 客戶端",
}

MAXIMUM_DEPENDENCIES = 10  # 硬性限制
```

#### 理由
- **Dependency Hell Avoidance**: 避免依賴地獄
- **Security**: 減少安全風險面
- **Maintainability**: 更少的維護負擔
- **Performance**: 更小的安裝包

#### 審批流程
新增依賴必須滿足：
1. 解決核心功能需求
2. 無法用簡單代碼替代
3. 維護良好且穩定
4. License 兼容
5. Tech Lead 批准

---

## 第 4 部分：實施策略決策 (Implementation Strategy Decisions)

### ADR-009: 採用"破壞重建"而非"漸進重構"

#### 狀態
✅ **已接受** (2025-01-21)

#### 背景
重構策略選擇：
1. 漸進式重構：逐步改善現有代碼
2. 破壞重建：刪除現有代碼，從頭開始

#### 決策
採用"破壞重建"策略：
- 保留現有代碼作為參考
- 創建全新的代碼庫
- 不嘗試遷移現有邏輯

#### 理由 (Linus 哲學支持)
> **"有時，重寫比重構更快。"** - Linus Torvalds

- **Clean Slate**: 避免歷史包袱
- **Architecture Clarity**: 新架構更清晰
- **Speed**: 重寫可能比修修補補更快
- **Quality**: 新代碼質量更高

#### 風險緩解
- 保留舊代碼作為功能參考
- 分階段實施，確保每階段都可工作
- 重點測試核心功能

### ADR-010: 3 週時間箱開發策略

#### 狀態
✅ **已接受** (2025-01-21)

#### 背景
需要確定開發時程和里程碑。

#### 決策
採用固定 3 週時間箱：
- 第 1 週：核心功能最小可工作版本
- 第 2 週：Web 界面和完整功能
- 第 3 週：優化、測試、文檔

#### 理由
- **Time Constraint Drives Simplicity**: 時間限制促進簡潔設計
- **Regular Milestones**: 每週都有可演示的進展
- **Risk Management**: 早期發現問題

#### 每週目標
```python
WEEKLY_MILESTONES = {
    "week_1": {
        "goal": "python main.py 能工作",
        "features": ["基本對話", "Python 工具", "配置系統"],
        "success_criteria": "核心 demo 可演示"
    },
    "week_2": {
        "goal": "Web 界面完整可用",
        "features": ["WebSocket 通信", "前端界面", "所有工具"],
        "success_criteria": "功能完整的 Web 應用"
    },
    "week_3": {
        "goal": "生產就緒品質",
        "features": ["性能優化", "錯誤處理", "文檔完善"],
        "success_criteria": "通過所有驗收測試"
    }
}
```

### ADR-011: 測試策略：手動優先，自動化輔助

#### 狀態
✅ **已接受** (2025-01-21)

#### 背景
需要確定測試策略和自動化程度。

#### 決策
採用"手動優先，自動化輔助"的測試策略：
- 70% 手動探索測試
- 20% 關鍵路徑自動化測試
- 10% 單元測試

#### 理由
- **Time Constraint**: 3 週內建立完整自動化測試不現實
- **User Experience Focus**: 手動測試更關注用戶體驗
- **Flexibility**: 手動測試更靈活，能發現意外問題
- **Cost-Benefit**: 對於小型系統，過度自動化成本過高

#### 自動化測試範圍
僅對以下功能建立自動化測試：
- 系統啟動流程
- 核心 Agent 邏輯
- 工具載入機制
- 基本錯誤處理

### ADR-012: 代碼審查標準：Linus 式品味測試

#### 狀態
✅ **已接受** (2025-01-21)

#### 背景
需要建立代碼質量標準和審查流程。

#### 決策
每個代碼提交必須通過 "Linus 式品味測試"：

```python
LINUS_TASTE_CHECKLIST = {
    "no_special_cases": "沒有特殊情況 if/elif 分支",
    "single_responsibility": "每個函數只做一件事",
    "self_documenting": "代碼自我解釋，無需註釋",
    "uniform_interfaces": "同類功能使用統一介面",
    "data_structure_first": "優秀的數據結構設計",
    "no_premature_optimization": "沒有過早優化",
    "readable_flow": "邏輯流程清晰可讀"
}
```

#### 審查問題
每次審查問自己：
1. "如果 Linus 看到這段代碼會說什麼？"
2. "這段代碼是否顯而易見？"
3. "有沒有不必要的複雜性？"
4. "新人能快速理解嗎？"

---

## 決策影響分析

### 正面影響匯總
- **開發速度**: 簡化架構加快開發
- **維護成本**: 大幅降低長期維護成本
- **用戶體驗**: 統一簡潔的用戶界面
- **性能**: 減少抽象層提升性能
- **可擴展性**: 統一介面易於擴展

### 風險與緩解
| 風險 | 可能性 | 影響 | 緩解措施 |
| :--- | :--- | :--- | :--- |
| 過度簡化 | 中 | 高 | 持續用戶反饋，快速迭代 |
| 功能不足 | 中 | 中 | 基於實際需求，不預設功能 |
| 學習曲線 | 低 | 低 | 重點關注文檔和例子 |

### 長期策略
- 堅持簡潔性原則
- 定期回顧和重構
- 社區反饋導向演進
- 持續的 Linus 式品味檢查

---

**決策批准**:
- Linus-style 架構師: ✅ 已批准 (2025-01-21)
- Tech Lead: ✅ 已批准 (2025-01-21)
- 開發團隊: ✅ 已批准 (2025-01-21)

**決策生效日期**: 2025-01-21
**下次審查日期**: 2025-02-21 (重構完成後)