# OKR 架構重構 WBS (Work Breakdown Structure)

**日期**: 2026-01-31
**版本**: v3.0
**狀態**: Phase 1-4 完成, Phase 5-6 部分延後

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

## Phase 5: 簡化 Kernel ⏸️ 延後

| 項目 | 狀態 | 說明 |
|------|------|------|
| 移除 `KernelAwareAgent` | ⏸️ | 需要 message bus 架構改動 |
| 簡化 Kernel (442→100 行) | ⏸️ | 需要大規模重構 |
| 移除重複的 LLM/Tool 初始化 | ⏸️ | 需要依賴注入重構 |

### 延後原因
- `KernelAwareAgent` 移除需要修改 message bus 和所有 agent 的註冊方式
- 簡化 Kernel 需要重新設計 execute 流程
- 這些改動風險較高，需要完整測試覆蓋

---

## Phase 6: 遷移澄清門 ⏸️ 延後

| 項目 | 狀態 | 說明 |
|------|------|------|
| 從 `orchestration.py` 遷移到 `router` | ⏸️ | 架構決策，需要更多設計 |

### 當前位置
```
orchestration.py:156-193  # CLARIFICATION GATE
```

### 計劃位置
```
router/llm_analyzer.py  # 在 analyze() 中直接返回 CLARIFICATION_NEEDED
```

### 延後原因
- 需要修改 `RoutingDecision` 返回類型
- 需要 Kernel 能處理 router 直接返回的澄清請求
- 當前實現可用，遷移是優化而非必要

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

## 後續工作建議

### 短期 (建議)
1. 為新的 OKR schema 添加單元測試
2. 為 prompt 載入添加驗證測試
3. 端到端測試驗證完整流程

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
