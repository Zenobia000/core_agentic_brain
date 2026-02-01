# OKR 架構重構 WBS (Work Breakdown Structure)

**日期**: 2026-02-01
**版本**: v3.2
**狀態**: Phase 1-10 完成 (全部)

---

## 核心理念

**企業管理者視角**：
- **管理者（系統）**：分析問題、排序優先級、定義 OKR
- **超級員工（AI）**：自行決定路徑、確保完成工作
- **品質保證**：OKR checklist 作為唯一驗收標準

**設計哲學**：定義 WHAT（目標），不限制 HOW（方法）

---

## 架構圖

```
User Request
     │
     ▼
┌─────────────┐
│   Router    │  管理者職責：分析 + OKR 定義 + 路由決策
│             │  ✓ 問題理解 (refine_query)
│             │  ✓ 歧義檢測 → 澄清門
│             │  ✓ 路由決策 (System 1/2)
│  [YAML prompts: prompts/router.yaml]
└─────────────┘
     │
     ▼
┌─────────────┐
│   Kernel    │  協調器：組件註冊 + OKR 注入
│             │  ✓ Schema 偵測
│             │  ✓ OKR prompt 注入到 context.metadata
│             │  ✓ Agent 調度
└─────────────┘
     │
     ▼
┌─────────────┐
│  Planner    │  規劃專家：基於 OKR 規劃步驟
│             │  ✓ 檢查 prerequisites
│             │  ✓ 使用 planning_okr prompt
│             │  ✓ 每步驟對應 Key Result
│  [YAML prompts: prompts/planner.yaml]
└─────────────┘
     │
     ▼
┌─────────────┐
│  Executor   │  超級員工：完全自主達成目標
│             │  ✓ ReAct 循環
│             │  ✓ 自行決定工具和順序
│             │  ✓ 對 OKR 負責
│  [YAML prompts: prompts/executor.yaml]
└─────────────┘
     │
     ▼
┌─────────────┐
│  Reviewer   │  品質保證：純 OKR 驗證
│             │  ✓ 使用 review_okr prompt
│             │  ✓ 逐項檢查 checklist
│             │  ✓ 不做業務判斷
│  [YAML prompts: prompts/reviewer.yaml]
└─────────────┘
```

---

## Phase 1: 清理舊模式 ✅ 完成

| 項目 | 狀態 | 說明 |
|------|------|------|
| 刪除 `core/agent.py` | ✅ | 被 `agents/base.py` 取代 |
| 清理 `core/schema.py` | ✅ | 移除 `intake`, `expected_output`, `_get_legacy_prompt()` |
| 更新 `orchestration.py` | ✅ | 使用 `okr_prompt` 取代 legacy 方法 |
| 更新 `executor.py` | ✅ | 從 metadata 直接獲取 `okr_prompt` |
| 修復 `agents/base.py` | ✅ | 移除 `CoreAgent` 死代碼引用 |
| 更新 `web/server.py` | ✅ | 使用 Kernel 架構取代舊 Agent |
| 更新測試檔案 | ✅ | `test_agent.py` 標記為 deprecated |

### 刪除的檔案/代碼
- `core/agent.py` (整個檔案)
- `core/example_manager.py` (之前已刪除)
- `prompts/examples/` (之前已刪除)
- `schema.py` 中的 `intake`, `expected_output` 欄位
- `schema.py` 中的 `get_intake_prompt()`, `get_output_prompt()` 方法

---

## Phase 2: 遷移硬編碼提示詞 ✅ 完成

| 項目 | 狀態 | 說明 |
|------|------|------|
| 創建 `prompts/router.yaml` | ✅ | 包含 system, refine_query, clarification, fallback |
| 更新 `router/llm_analyzer.py` | ✅ | 使用 PromptLoader 取代硬編碼提示詞 |

### 新增檔案
```yaml
# prompts/router.yaml
system: |
  You are a query understanding expert. Return JSON only.

refine_query: |
  You are a query understanding expert...
  ## Intent Types
  - greeting, simple_query, information_gathering, task_execution, planning, analysis, creative
  ## JSON Output Format
  {intent_type, ambiguity_level, key_questions, refined_goal, required_depth, thought_process}

clarification: |
  To provide accurate results, I need to confirm...
```

---

## Phase 3: 統一 Schema 為 OKR ✅ 完成

| 項目 | 狀態 | 說明 |
|------|------|------|
| 更新 `schemas/code_task.yaml` | ✅ | 轉換為 OKR v3.0 格式 |
| 更新 `schemas/travel.yaml` | ✅ | 已是 OKR v3.0 格式 |
| 新增偵測關鍵字 | ✅ | 添加 `函數`, `函式`, `類別`, `code` 等 |

### Schema 結構 (OKR v3.0)
```yaml
domain: code
version: "3.0"

detect:
  - 寫程式
  - coding
  - function
  - 函數

objective: |
  Deliver working, tested code...

key_results:
  requirements:
    description: "Clear understanding..."
    checklist:
      - "Functionality clearly defined"
      - "Language/framework confirmed"

  implementation:
    checklist:
      - "Syntax valid and runnable"
      - "No hardcoded credentials"

constraints:
  - "Never output code that cannot run"
  - "Never hardcode secrets"

success_criteria: |
  APPROVED only if ALL checklist items satisfied
```

---

## Phase 4: 重構提示詞設計 ✅ 完成

| 項目 | 狀態 | 說明 |
|------|------|------|
| 更新 `prompts/planner.yaml` | ✅ | 給目標不給步驟，新增 `planning_okr` |
| 更新 `prompts/executor.yaml` | ✅ | 給約束讓 AI 自由發揮 |
| 更新 `prompts/reviewer.yaml` | ✅ | 純 OKR 驗證，新增 `review_okr` |

### 提示詞設計原則

**Planner (規劃)**
```
- Check prerequisites from OKR
- Create plan that addresses each Key Result
- DO NOT tell AI HOW - define WHAT
```

**Executor (執行)**
```
- Full authority over implementation
- Choose tools, decide order, skip unnecessary steps
- Accountable to OKR checklist before terminate
```

**Reviewer (審核)**
```
- ONLY job: validate against OKR checklist
- Each item: PASS or FAIL with reason
- ALL pass + NO constraints violated = APPROVED
```

---

## Phase 5: 簡化 Kernel ✅ 完成 (2026-02-01)

| 項目 | 狀態 | 說明 |
|------|------|------|
| 移除 `KernelAwareAgent` | ✅ | 替換為 `DirectAgent` (無 monkey-patch) |
| 簡化 `_create_agent()` | ✅ | 直接實例化，傳遞依賴 |
| 行數減少 | ✅ | 460 → 427 行 (-33 行) |

### 重構說明
**移除的反模式**:
- 運行時 `get_system_prompt()` 方法替換 (monkey-patch)
- 動態參數檢測 (`inspect.signature`)

**新設計 (`DirectAgent`)**:
```python
class DirectAgent:
    def __init__(self, agent, name: str):
        self.agent = agent
        self.name = name

    async def handle(self, message: Message) -> Any:
        context = message.metadata.get("context", ...)
        return await self.agent.execute(context)
```

**關鍵洞察**:
Agents 已經透過 PromptLoader 直接載入 prompts，
`KernelAwareAgent` 的 prompt 替換邏輯早已過時

**額外修復**:
- `PlannerAgent` 和 `ReviewerAgent` 的 `__init__` 更新為接受 `llm_provider` 和 `kernel` 參數
- 保持與 `BaseAgent` 和 `ExecutorAgent` 簽名一致

---

## Phase 6: 遷移澄清門 ✅ 完成 (2026-02-01)

| 項目 | 狀態 | 說明 |
|------|------|------|
| `router/llm_analyzer.py` | ✅ | 新增 `_check_clarification_needed()` 方法 |
| `core/kernel.py` | ✅ | 處理 `strategy="clarification"` 返回 |
| `core/orchestration.py` | ✅ | 移除澄清門邏輯 (-28 行) |
| 測試 | ✅ | 新增 `TestClarificationGate` (3 tests) |

### 設計模式
```
Router (Fail Fast)
├── 階段 1: Query Refinement
├── 階段 2: Clarification Gate  ← 新增
│   └── 高歧義 + 有問題 → strategy="clarification"
└── 階段 3: Routing Decision

Kernel
└── 檢測 strategy="clarification" → 早期返回
```

### 行數變化
```
orchestration.py: 565 → 537 (-28 行)
llm_analyzer.py: 218 → 268 (+50 行)
kernel.py: 442 → 460 (+18 行)
```

---

## Phase 8: 清理死代碼 ✅ 完成 (2026-02-01)

| 項目 | 狀態 | 說明 |
|------|------|------|
| `router/executor.py` | ✅ 刪除 | 與 orchestration.py 重複，只在測試中使用 |
| `router/strategies.py` | ✅ 刪除 | 完全未使用 |
| 測試更新 | ✅ | 標記舊測試為 deprecated |

### router/ 目錄整合後
```
router/
└── llm_analyzer.py  ← 唯一保留 (問題理解 + 路由決策)
```

---

## Phase 7: OKR Prompt 連接修復 ✅ 完成 (2026-01-31)

| 項目 | 狀態 | 說明 |
|------|------|------|
| `agents/planner.py` | ✅ | 使用 `planning_okr` 當 OKR 可用 |
| `agents/reviewer.py` | ✅ | 使用 `review_okr` 當 OKR 可用 |

### 修改內容
- `_build_planning_prompt()`: OKR-first，檢查 `context.metadata["okr_prompt"]`
- `_build_review_prompt()`: OKR-first，接收 context 參數

### Prompt 使用邏輯
```python
if context.metadata.get("okr_prompt"):
    use "planning_okr" / "review_okr"  # OKR 驗證
else:
    use "planning" / "review"  # Fallback
```

---

## 關鍵檔案修改清單

| 檔案 | 動作 | Phase |
|------|------|-------|
| `core/agent.py` | 刪除 | 1 |
| `core/schema.py` | 修改 (移除 legacy) | 1 |
| `core/orchestration.py` | 修改 (使用 okr_prompt) | 1 |
| `agents/base.py` | 修改 (移除 CoreAgent) | 1 |
| `agents/executor.py` | 修改 (簡化 OKR 注入) | 1 |
| `web/server.py` | 修改 (使用 Kernel) | 1 |
| `tests/test_agent.py` | 修改 (標記 deprecated) | 1 |
| `tests/integration/test_main_minimal.py` | 修改 (使用 Kernel) | 1 |
| `prompts/router.yaml` | 新建 | 2 |
| `router/llm_analyzer.py` | 修改 (使用 PromptLoader) | 2 |
| `schemas/code_task.yaml` | 修改 (OKR v3.0) | 3 |
| `prompts/planner.yaml` | 修改 (OKR 驅動) | 4 |
| `prompts/executor.yaml` | 修改 (自主執行) | 4 |
| `prompts/reviewer.yaml` | 修改 (純 OKR 驗證) | 4 |
| `agents/planner.py` | 修改 (OKR-first prompt) | 7 |
| `agents/reviewer.py` | 修改 (OKR-first prompt) | 7 |

---

## 驗證結果

```bash
# 導入測試
✅ core.kernel.Kernel
✅ core.orchestration.MultiAgentOrchestrator
✅ core.schema.detect_schema
✅ core.prompt_loader.get_prompt_loader
✅ agents.executor.ExecutorAgent
✅ agents.planner.PlannerAgent
✅ agents.reviewer.ReviewerAgent
✅ router.llm_analyzer.LLMTaskAnalyzer

# Schema 偵測測試
✅ 規劃旅遊 → travel
✅ 寫程式 → code
✅ 寫一個排序函數 → code

# Prompt 載入測試
✅ router.system
✅ router.refine_query
✅ executor.system
✅ planner.system
✅ reviewer.system
```

---

## Phase 9: OKR 單元測試 ✅ 完成 (2026-02-01)

| 項目 | 狀態 | 說明 |
|------|------|------|
| `tests/unit/test_okr_schema.py` | ✅ 新建 | 17 個測試 - Schema 偵測、OKR 生成 |
| `tests/unit/test_okr_prompts.py` | ✅ 新建 | 14 個測試 - Prompt 載入、格式化、一致性 |

### 測試覆蓋
```
test_okr_schema.py (17 tests)
├── TestDomainSchema: 基本建立、關鍵字匹配、OKR 生成
├── TestSchemaLoader: 單例模式、domain 列表、匹配
├── TestDetectSchema: travel/code 偵測、OKR checklist
└── TestOKRIntegration: travel/code 結構驗證

test_okr_prompts.py (14 tests)
├── TestOKRPromptLoading: router/planner/reviewer prompts
├── TestOKRPromptFormatting: 變數替換
├── TestOKRPromptFlow: 完整流程
└── TestOKRPromptConsistency: OKR vs fallback 一致性
```

---

## Phase 10: E2E 測試與效能驗證 ✅ 完成 (2026-02-01)

| 項目 | 狀態 | 說明 |
|------|------|------|
| `tests/integration/test_okr_e2e.py` | ✅ 新建 | 16 個測試 - 完整 OKR 流程驗證 |
| `tests/performance/test_benchmark.py` | ✅ 修復 | 更新為使用 schema detection |

### E2E 測試覆蓋
```
test_okr_e2e.py (16 tests)
├── TestOKRDetectionFlow: travel/code 偵測、context 注入
├── TestOKRPromptBuilding: planner/reviewer OKR prompt 使用
├── TestOKRFlowWithMocks: router 分析、orchestrator 注入
├── TestOKRValidation: OKR sections、checklist、constraints
├── TestAgentOKRIntegration: planner/reviewer/executor OKR 整合
└── TestOKRFallback: 無 OKR 時的 fallback 行為
```

### 測試修復
- `test_prompt_integration.py` - 更新為正確的 prompt key (`planner.planning`)
- `test_react.py` - 更新 message summarization 測試閾值 (> 15 messages)
- `test_system1_2_routing.py` - 改為運行時 API key 檢查
- `test_orchestration_fix.py` - 延遲載入 dotenv 到測試函數內

### 測試遷移
已遷移到 `tests/deprecated/`:
- `test_tool_manager.py` (引用不存在的 `core.tool_manager`)
- `test_routing.py` (引用舊的 `router.analyzer`)
- `test_tools.py` (引用不存在的 `BaseTool`)
- `test_types.py` (引用不存在的 `ToolDefinition`)

### 效能基準
```
Schema Detection: 0.018ms mean (500 iterations)
Cold Start: 47.563ms total
```

### 測試結果
```
Core tests: 68 passed
Total OKR tests: 47 passed (17 schema + 14 prompts + 16 e2e)
```

---

## 後續工作建議

### 短期 (建議)
1. ~~為新的 OKR schema 添加單元測試~~ ✅
2. ~~為 prompt 載入添加驗證測試~~ ✅
3. ~~端到端測試驗證完整流程~~ ✅

### 中期 (Phase 5-6 延續)
1. 重構 message bus 支持直接 agent 註冊
2. 移除 `KernelAwareAgent` 猴補丁
3. 遷移澄清門到 router

### 長期 (架構優化)
1. 簡化 Kernel 職責
2. 統一錯誤處理模式
3. 添加 OKR 驗證的自動化測試

---

## 參考文件

- 原始計劃: `~/.claude/plans/snappy-finding-map.md`
- Schema 定義: `schemas/*.yaml`
- Prompt 定義: `prompts/*.yaml`
- 核心架構: `core/kernel.py`, `core/orchestration.py`
