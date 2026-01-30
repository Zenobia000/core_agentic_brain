# OpenManus vs Core Agentic Brain - 設計對比矩陣

**版本**: v1.0
**日期**: 2026-01-30
**目的**: 快速參考兩個系統的關鍵差異

---

## 一句話總結

| 系統 | 核心特點 | 最大優勢 | 最大缺陷 |
|------|---------|---------|---------|
| **OpenManus** | All-in-one general agent | 工具豐富、MCP 整合 | 無 routing、無 reviewer、過度繼承 |
| **Core Agentic Brain** | Multi-agent orchestration | 智慧路由、品質審查、清晰架構 | 缺 clarification、缺 tool policy、plan 純文字 |

---

## 架構設計對比

### Agent 層次結構

| 面向 | OpenManus | Core Agentic Brain | 評價 |
|------|-----------|-------------------|------|
| **繼承層數** | 4 層 (`BaseAgent` -> `ReActAgent` -> `ToolCallAgent` -> `Manus`) | 3 層分離 (`Router` -> `Orchestrator` -> `Agents`) | ✅ CAB 更簡潔 |
| **職責分離** | 混雜在繼承層中 | 清晰分層（routing, orchestration, execution） | ✅ CAB 更清晰 |
| **擴展性** | 繼承擴展 | 組合擴展 | ✅ CAB 更靈活 |
| **複雜度** | 🔴 高（每層都改 think/act） | 🟢 低（職責明確） | ✅ CAB 勝出 |

**Linus 評價**: CAB 架構更符合「好品味」- 沒有不必要的繼承層。

---

### Routing 與任務分析

| 面向 | OpenManus | Core Agentic Brain | 評價 |
|------|-----------|-------------------|------|
| **任務分析** | ❌ 無 | ✅ 雙階段（理解 + 路由） | ✅ CAB 大幅領先 |
| **Ambiguity 檢測** | ❌ 無 | ✅ 有（但無 action） | 🟡 CAB 有但未用好 |
| **System 1/2 分離** | ❌ 無 | ✅ 有 | ✅ CAB 領先 |
| **Intent 識別** | ❌ 無 | ✅ 7 種 intent type | ✅ CAB 領先 |
| **策略選擇** | 單一 flow | 4 種策略（direct, sequential, orchestrated, react） | ✅ CAB 更智能 |

**Linus 評價**: OpenManus 是「一把瑞士刀」，CAB 是「工具箱」- 工具箱更符合 Unix 哲學。

---

### Clarification 機制

| 面向 | OpenManus | Core Agentic Brain | 評價 |
|------|-----------|-------------------|------|
| **ask_human 工具** | ✅ 有 | ❌ 無 | 🔴 CAB 缺少 |
| **Clarification policy** | ❌ 無（靠模型自覺） | ❌ 無（有檢測但無 gate） | ❌ 都很爛 |
| **Ambiguity gate** | ❌ 無 | ⚠️ 有檢測但不阻止 | 🔴 CAB 更糟（知道卻不做） |
| **問題格式化** | 簡單 text input | N/A | 🟡 OpenManus 略勝 |

**關鍵問題**: 兩個系統都缺「強制澄清」機制。

**改進方向**:
- CAB 需要: ask_user 工具（學 OpenManus）+ Clarification Gate（新增）
- OpenManus 需要: Ambiguity detection + Gate policy

---

### 計劃管理

| 面向 | OpenManus | Core Agentic Brain | 評價 |
|------|-----------|-------------------|------|
| **計劃結構** | ✅ JSON + 狀態追蹤 | ❌ 純文字 | 🔴 CAB 嚴重落後 |
| **步驟狀態** | ✅ 4 種（not_started, in_progress, completed, blocked） | ❌ 無 | 🔴 CAB 缺少 |
| **進度追蹤** | ✅ 百分比、計數 | ❌ 無 | 🔴 CAB 缺少 |
| **Plan validation** | ⚠️ 無 required_info | ❌ 無任何驗證 | 🔴 CAB 更糟 |
| **PlanningTool** | ✅ 獨立工具（create, update, mark_step） | ❌ 無 | 🔴 CAB 缺少 |

**關鍵差異**: OpenManus 的計劃「可執行」，CAB 的計劃「只是文案」。

**改進方向**: CAB 必須實施結構化計劃（Tier 2 priority）。

---

### 品質審查

| 面向 | OpenManus | Core Agentic Brain | 評價 |
|------|-----------|-------------------|------|
| **Reviewer 存在** | ❌ 無 | ✅ 有 | ✅ CAB 領先 |
| **Hard constraints** | N/A | ❌ 無（只有 quality score） | 🔴 CAB 該有卻沒做好 |
| **Revision loop** | ❌ 無 | ✅ 有（最多 2 次） | ✅ CAB 領先 |
| **Approval criteria** | N/A | ⚠️ 太軟（什麼都 APPROVED） | 🔴 CAB 有機制但不嚴格 |

**關鍵差異**: CAB 有 reviewer 機制（領先），但缺乏硬性約束（浪費優勢）。

**改進方向**: Reviewer 加入 hard-fail rubric（Tier 1 priority）。

---

### 工具系統

| 面向 | OpenManus | Core Agentic Brain | 評價 |
|------|-----------|-------------------|------|
| **內建工具數** | 9+ (Python, Bash, Browser, Chart, MCP, Planning, Ask, Terminate, Editor) | 4 (Files, Python, WebSearch, Terminate) | 🟡 OpenManus 更豐富 |
| **MCP 支援** | ✅ 原生整合 | ⚠️ 可選（未預設） | 🟡 OpenManus 更完整 |
| **ToolCollection** | ✅ 統一管理 | ⚠️ 分散在 Kernel | 🟡 OpenManus 更集中 |
| **Tool policy** | ❌ 無強制規則 | ❌ 無 | ❌ 都缺少 |
| **Tool choice** | ✅ 3 種（NONE, AUTO, REQUIRED） | ⚠️ 只有 AUTO | 🟡 OpenManus 更靈活 |

**關鍵差異**: OpenManus 工具更豐富，但兩者都缺 policy。

**改進方向**:
- CAB: 加 ask_user (Tier 1) + Tool-Use Policy (Tier 2)
- OpenManus: 加 Tool-Use Policy

---

### ReAct Loop 實作

| 面向 | OpenManus | Core Agentic Brain | 評價 |
|------|-----------|-------------------|------|
| **Think-Act 分離** | ✅ 明確（think() / act()） | ✅ 明確 | 🟢 都好 |
| **終止條件** | `no tool_calls` OR `terminate tool` | 同左 | 🟢 都一樣 |
| **Token budget** | ❌ 無 | ✅ 有（可配置） | ✅ CAB 領先 |
| **Repetition 檢測** | ❌ 基本（duplicate content） | ✅ 進階（ToolCallSignature） | ✅ CAB 領先 |
| **Circuit breaker** | ❌ 無 | ✅ 有（consecutive errors） | ✅ CAB 領先 |
| **Max steps** | 20 | 10（可配置） | 🟢 都合理 |

**關鍵差異**: CAB 的 ReAct loop 更健壯（token budget, circuit breaker）。

**問題**: 兩者都是「模型不想用工具就結束」- 缺強制 tool-use policy。

---

### Prompt 工程

| 面向 | OpenManus | Core Agentic Brain | 評價 |
|------|-----------|-------------------|------|
| **Prompt 管理** | Python 字串（hardcoded） | ✅ YAML 檔案（外部化） | ✅ CAB 更靈活 |
| **System prompt** | 簡短（2句話） | 詳細（YAML template） | 🟡 各有優勢 |
| **Prompt loader** | ❌ 無 | ✅ 有（`core/prompt_loader.py`） | ✅ CAB 領先 |
| **可維護性** | 🔴 需重編譯 | 🟢 改 YAML 即生效 | ✅ CAB 領先 |

**Linus 評價**: CAB 的 prompt 外部化是正確設計 - "機制與策略分離"。

---

## 核心功能矩陣

### 功能完整性

| 功能 | OpenManus | Core Agentic Brain | 優先級 |
|------|-----------|-------------------|--------|
| **Clarification (ask user)** | 🟡 有工具無 policy | 🔴 無工具無 policy | P0 - 緊急 |
| **Structured Planning** | 🟢 完整 | 🔴 無 | P0 - 緊急 |
| **Quality Review** | 🔴 無 | 🟡 有但太軟 | P1 - 重要 |
| **Smart Routing** | 🔴 無 | 🟢 完整 | - 已優勢 |
| **Tool Policy** | 🔴 無 | 🔴 無 | P1 - 重要 |
| **Token Management** | 🔴 無 | 🟢 完整 | - 已優勢 |
| **Error Handling** | 🟡 基本 | 🟢 健壯 | - 已優勢 |
| **MCP Integration** | 🟢 原生 | 🟡 可選 | P2 - 次要 |

**優先級說明**:
- P0: Tier 1（今天必須做）
- P1: Tier 2（本週完成）
- P2: Tier 3（未來考慮）

---

## 問題診斷對比

### 從執行 Log 看問題

| 症狀 | OpenManus 表現 | CAB 表現 | 根本原因 |
|------|---------------|---------|---------|
| **模糊請求直接回答** | ✅ 會發生（無檢測） | ✅ 會發生（有檢測無行動） | 缺 clarification gate |
| **工具不被使用** | ✅ 會發生（靠 prompt） | ✅ 會發生（靠 prompt） | 缺 tool-use policy |
| **不合理輸出被接受** | N/A（無 reviewer） | ✅ 會發生（reviewer 太軟） | 缺 hard constraints |
| **計劃不被遵守** | ⚠️ 較少（有狀態追蹤） | ✅ 常發生（計劃是文字） | Plan 無結構 |

**結論**: CAB 的問題更嚴重 - 「有機制卻不用」比「沒機制」更糟糕。

---

## 學習建議矩陣

### 從 OpenManus 學習

| 設計點 | 重要性 | 實施難度 | Tier | 說明 |
|--------|--------|---------|------|------|
| **ask_human 工具** | 🔴 Critical | 🟢 簡單 | Tier 1 | 10 分鐘，立即可用 |
| **結構化計劃** | 🔴 Critical | 🟡 中等 | Tier 1-2 | 30 分鐘，需改 schema |
| **狀態追蹤** | 🟡 Important | 🟡 中等 | Tier 2 | 整合到 structured plan |
| **ToolCollection** | 🟢 Nice-to-have | 🟢 簡單 | Tier 3 | 可選，現有設計已足夠 |
| **ToolChoice.REQUIRED** | 🟡 Important | 🟢 簡單 | Tier 2 | 配合 tool policy 使用 |
| **MCP 整合** | 🟢 Nice-to-have | 🔴 困難 | 未來 | 非核心功能 |

---

### 不該學習的

| 設計點 | 為什麼不學 | Linus 原則 |
|--------|-----------|-----------|
| **4 層繼承** | 過度抽象，無實際價值 | "Complexity is the enemy" |
| **無 Reviewer** | CAB 已有更好設計 | "Never break what works" |
| **Hardcoded prompts** | CAB 已外部化 | "Mechanism and policy separation" |
| **無 routing** | 所有任務用同一 flow 效率差 | "Simplicity ≠ Uniformity" |

---

## 數據結構對比

### Plan 表示法

#### OpenManus: 結構化（機器可執行）
```python
plan = {
    "plan_id": "plan_1738234567",
    "title": "Kyoto 4-Day Trip",
    "steps": [
        "Book flights from Taipei to Osaka",
        "Reserve accommodation in Kyoto",
        "Plan temple visits"
    ],
    "step_statuses": ["completed", "in_progress", "not_started"],
    "step_notes": ["Flight AB123 booked", "Checking Hotel X", ""]
}

# 可執行檢查
plan["step_statuses"][0] == "completed"  # True
progress = sum(s == "completed" for s in plan["step_statuses"]) / len(plan["steps"])  # 33%
```

**優點**: 可追蹤、可驗證、可視化
**缺點**: 步驟缺 `required_info`（不知道缺什麼資訊才能執行）

---

#### Core Agentic Brain: 文字（人類可讀）
```python
context.metadata["plan"] = """
### Adventure Travel Itinerary Planning

#### Step 1: Understand User Preferences
1. Clarify destination...
2. Identify adventure activity types...
...
"""
```

**優點**: 人類可讀性高
**缺點**:
- 無法機器驗證
- 無法追蹤進度
- 無法檢查完整性

---

### 建議的混合方案

```python
# 結合兩者優點
structured_plan = {
    "plan_id": "plan_123",
    "title": "Kyoto Trip",
    "steps": [
        {
            "description": "Book flights",
            "required_info": ["departure_city", "travel_date", "budget"],  # <- 從 CAB 加入
            "validation_criteria": "Flight confirmation received",          # <- 從 CAB 加入
            "status": "not_started",                                        # <- 從 OpenManus
            "notes": ""                                                     # <- 從 OpenManus
        }
    ],
    "missing_info": ["departure_city", "travel_date"],  # <- 新增：計劃級別缺失
    "ready_to_execute": False                           # <- 新增：是否可執行
}
```

**Linus 評價**: "這才是好品味 - 結構化且可驗證，沒有特殊情況。"

---

## 工具使用模式對比

### Tool Calling Pattern

#### OpenManus
```python
# 模型完全自主
response = await llm.ask_tool(
    messages=[...],
    tools=[...],
    tool_choice=ToolChoice.AUTO  # 模型決定
)

if response.tool_calls:
    # Execute
else:
    # Finish (即使該用工具也結束)
```

**問題**: 模型可以選擇「不用工具」然後瞎編。

---

#### Core Agentic Brain
```python
# 同樣模型自主
llm_response = await self.llm.generate(
    messages=[...],
    tools=[...]
)

if not tool_call_requests:
    logger.info("No tool calls requested. Finishing ReAct loop.")
    break  # 直接結束
```

**問題**: 同樣缺少強制性檢查。

---

#### 建議的 Policy-Driven Pattern
```python
# Step 1: 模型生成
llm_response = await self.llm.generate(messages=[...], tools=[...])

# Step 2: Policy 檢查（新增）
tool_policy = context.metadata.get("tool_policy", {})
required_tools = tool_policy.get("required_tools", [])

if not tool_call_requests:
    # 檢查是否違反 policy
    if required_tools and not any(tc.name in required_tools for tc in all_tool_calls):
        # 強制重試
        local_messages.append({
            "role": "system",
            "content": f"POLICY: You must use one of: {required_tools}"
        })
        continue  # 不要 break
    else:
        break  # 正常結束

# Step 3: 執行工具
```

**Linus 評價**: "這才對 - 把 policy 當 first-class citizen，而不是藏在 prompt 裡。"

---

## Reviewer 評估標準對比

### OpenManus: 無 Reviewer
N/A

---

### Core Agentic Brain: 當前（太軟）

**現狀**:
```yaml
# prompts/reviewer.yaml (當前)
system: |
  Review the execution result and provide feedback.
  Rate quality from 1-10.
  Suggest improvements if needed.
```

**問題**:
- 無硬性通過條件
- 旅遊規劃跨 4 國仍 APPROVED（quality_score=8）
- 只看「文筆」不看「可行性」

---

### 建議的兩層評估（Tier 1 改進）

```yaml
system: |
  ## Layer A: Hard Constraints (FAIL FAST)

  For travel planning, REJECT if:
  - No specific destination (vague "somewhere nice")
  - Geographically infeasible (4 countries in 4 days)
  - No budget breakdown (just "within budget")
  - Unrealistic timeline (long flight + intense activity same day)

  ## Layer B: Quality Score (1-10)

  Only if Layer A passes:
  - Clarity (2 pts)
  - Completeness (3 pts)
  - User experience (2 pts)
  - Efficiency (2 pts)
  - Extra value (1 pt)

  ## Decision Rule:
  - Layer A fail -> verdict = REJECTED (regardless of Layer B score)
  - Layer A pass + score >= 7 -> APPROVED
  - Layer A pass + score < 7 -> REVISION_NEEDED
```

**效果**:
- 跨洲旅遊 -> Layer A fail -> REJECTED（質量再高也沒用）
- 合理但文筆差 -> Layer A pass, score 6 -> REVISION_NEEDED

---

## 執行策略對比

### OpenManus: 單一 Flow

```
User Input
    ↓
Manus Agent (ReAct loop)
    ↓
Output
```

**特點**:
- 簡單直接
- 無任務分析
- 所有任務用同樣流程

**適用場景**: 通用助手、單輪對話

---

### Core Agentic Brain: Multi-Strategy

```
User Input
    ↓
LLM Analyzer (雙階段)
    ├─ System 1: Direct execution (簡單任務)
    └─ System 2: Orchestrated (複雜任務)
        ↓
    Planner -> Executor -> Reviewer (with revision loop)
        ↓
    Output
```

**特點**:
- 智慧路由
- 任務類型自適應
- 品質保證機制

**適用場景**: 複雜任務、多輪對話、需要高品質輸出

---

## 程式碼品質對比

### OpenManus

**優點**:
- 模組化清晰（agent, tool, flow, prompt 分離）
- Pydantic 驗證完整
- Type hints 良好

**缺點**:
- 繼承層次過深（4 層）
- 重複邏輯（`ReActAgent.think` vs `ToolCallAgent.think`）
- Prompt hardcoded in Python

**Linus 品味評分**: 🟡 7/10 - "結構清晰，但過度設計了"

---

### Core Agentic Brain

**優點**:
- 職責分離清晰（routing, orchestration, execution）
- Prompt 外部化（YAML）
- 健壯的錯誤處理（circuit breaker, token budget）

**缺點**:
- 缺少基礎工具（ask_user）
- 有檢測無行動（ambiguity gate）
- Plan 純文字（不可驗證）

**Linus 品味評分**: 🟢 8/10 - "架構對了，缺幾個關鍵功能"

---

## 改進建議總表

### Critical (Tier 1) - 立即修復

| 問題 | 學習對象 | 實施方式 | 工時 |
|------|---------|---------|------|
| 缺 ask_user 工具 | OpenManus `ask_human.py` | 創建 `tools/builtin/ask_user.py` | 10min |
| Ambiguity 無 gate | 新設計（OpenManus 也缺） | 在 orchestrator 加 gate | 15min |
| Reviewer 太軟 | 新設計（OpenManus 無 reviewer） | 加 hard-fail rubric | 10min |

**總計**: 35 分鐘
**效果**: 解決 80% 的問題

---

### Important (Tier 2) - 短期改進

| 問題 | 學習對象 | 實施方式 | 工時 |
|------|---------|---------|------|
| 無 tool policy | 新設計（兩者都缺） | 基於 intent_type 定義 policy | 20min |
| Plan 無結構 | OpenManus `PlanningTool` | 定義 StructuredPlan schema | 30min |

**總計**: 50 分鐘
**效果**: 系統可靠性提升

---

### Nice-to-have (Tier 3) - 未來考慮

| 功能 | 學習對象 | 實施方式 | 工時 |
|------|---------|---------|------|
| OrchestrationMode | 新設計 | 加 mode 選擇（fast/strict） | 1h |
| EventBus | OpenManus events | 實作 event-driven clarification | 2h |
| Session Management | OpenManus session | 整合 workspace tracking | 3h |

**總計**: 6 小時
**效果**: 系統配置性與可追蹤性

---

## 測試案例對比

### OpenManus 的測試覆蓋（推測）

**優點**:
- 有 pre-commit hooks（`.pre-commit-config.yaml`）
- 有 CI/CD（`.github/workflows/`）

**缺點**:
- 缺少 end-to-end 測試（針對 ambiguity handling）
- 缺少 policy violation 測試

---

### Core Agentic Brain 的測試覆蓋（當前）

**現有**:
- 單元測試（`tests/unit/`）
- 整合測試（`tests/integration/`）
- E2E 測試（`tests/test_e2e*.py`）

**缺少**:
- Clarification flow 測試
- Tool policy 測試
- Reviewer hard-fail 測試

**建議新增** (見 OPENMANUS_REFACTOR_CHECKLIST.md):
- `test_clarification_gate.py`
- `test_tool_policy.py`
- `test_reviewer_hard_fail.py`

---

## 決策參考快表

### 何時用 OpenManus 的設計？

| 場景 | 用 OpenManus | 用 CAB | 理由 |
|------|-------------|--------|------|
| 通用助手（聊天機器人） | ✅ | ❌ | 單一 agent 足夠 |
| 複雜任務規劃 | ❌ | ✅ | 需要 routing + review |
| 需要 MCP 工具 | ✅ | ⚠️ | OpenManus 原生支援 |
| 需要品質保證 | ❌ | ✅ | CAB 有 reviewer |
| 快速 prototype | ✅ | ❌ | OpenManus 更簡單 |
| 生產環境 | ❌ | ✅ | CAB 更健壯 |

---

### 何時需要 Clarification？

| 場景 | OpenManus 行為 | CAB 當前行為 | CAB 改進後 |
|------|---------------|-------------|-----------|
| "規劃旅遊" | 直接瞎編行程 | 分析出 ambiguity 但仍瞎編 | 🛑 Gate 阻止，要求 clarify |
| "東京有什麼好吃的" | 可能瞎編或用 websearch | 可能瞎編或用 websearch | ✅ Tool policy 強制 websearch |
| "寫一個排序函數" | 直接生成 | 直接生成 | ✅ 直接生成（ambiguity low） |

---

### 何時需要 Tool Policy？

| Intent Type | Required Tools | Min Calls | Rationale |
|-------------|---------------|-----------|-----------|
| `planning` | `["websearch", "ask_user"]` | 1 | Planning 需要資訊或澄清 |
| `information_gathering` | `["websearch"]` | 1 | 必須搜尋外部資訊 |
| `task_execution` | Suggested only | 0 | 可選，視任務而定 |
| `greeting` | None | 0 | 不需要工具 |

---

## 整合建議：最佳實踐

### 混合方案（取兩者之長）

```python
# 架構：學 CAB
- LLM Analyzer (routing)
- Multi-agent orchestration
- Reviewer quality check

# 工具：學 OpenManus
+ ask_user tool
+ ToolCollection 抽象
+ ToolChoice.REQUIRED 選項

# 計劃：混合設計
+ StructuredPlan with:
  - step_statuses (from OpenManus)
  - required_info (new)
  - validation_criteria (new)
  - ready_to_execute flag (new)

# Gate: 新設計（兩者都缺）
+ Clarification Gate (ambiguity check)
+ Tool-Use Policy (intent-based)
+ Hard-Fail Rubric (reviewer layer A)
```

---

## 效能與資源對比

### OpenManus

**優點**:
- 單 agent 開銷小
- 無 routing 延遲

**缺點**:
- 無 token budget（可能超額）
- 無 circuit breaker（錯誤會持續）
- 大任務可能卡住

---

### Core Agentic Brain

**優點**:
- Token budget 控制
- Circuit breaker 保護
- Repetition 檢測

**缺點**:
- Routing 有小延遲（LLM call）
- Multi-agent 有開銷

**Trade-off**: CAB 犧牲一點速度，換取健壯性與品質 - 合理的權衡。

---

## 最終建議

### 如果你是 OpenManus

**急需加入**:
1. LLM-based routing（學 CAB）
2. Reviewer 機制（學 CAB）
3. Tool-use policy（新設計）

---

### 如果你是 Core Agentic Brain

**急需加入**:
1. ask_user 工具（學 OpenManus）
2. Structured plan（學 OpenManus，但加 required_info）
3. Clarification gate（新設計，OpenManus 也缺）
4. Hard-fail reviewer（新設計）

---

### 終極融合版本（理想狀態）

```
Strengths from CAB:
✅ Smart routing (System 1/2)
✅ Multi-agent orchestration
✅ Reviewer quality check
✅ Token budget & circuit breaker
✅ YAML-based prompts

Strengths from OpenManus:
✅ ask_human tool
✅ Structured plan with status tracking
✅ ToolCollection abstraction

New designs (both missing):
✅ Clarification Gate
✅ Tool-Use Policy
✅ Hard-Fail Rubric
✅ Plan validation (required_info + ready_to_execute)

= Perfect Agent System
```

---

**下一步**: 執行 Tier 1（35 分鐘），立即見效。

**驗證標準**:
```bash
# Before
python main.py
>>> 規劃旅遊
# Output: 直接瞎編 4 國行程

# After
python main.py
>>> 規劃旅遊
# Output: "To provide accurate planning, I need to clarify:
#         1. 出發地點？
#         2. 目的地偏好？
#         3. 預算包含機票嗎？"
```

---

**參考文檔**:
- 完整分析: `REFACTOR_PLAN_OPENMANUS_ANALYSIS.md`
- 實施清單: `OPENMANUS_REFACTOR_CHECKLIST.md`
- 本對比矩陣: `OPENMANUS_COMPARISON_MATRIX.md`
