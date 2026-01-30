# Schema Complexity Analysis - Linus 式批判

**日期**: 2026-01-30
**結論**: 我們的 Schema 設計過度工程化，違反 Linus 原則

---

## 1. 問題陳述

我們的 `schemas/travel.yaml` 有 **150+ 行**，包含：
- detection keywords
- intake required_fields with detection_patterns
- tool_policy per phase (4 phases)
- output requirements with nested fields
- review criteria (hard_fail, soft_fail)
- quality_scoring

**問題**：這是在用 Config 解決應該用 Prompt 解決的問題。

---

## 2. 市場主流框架對比

### 2.1 各框架的 Agent 定義方式

| 框架 | Prompt 風格 | Config 複雜度 | Schema 強制性 |
|------|------------|---------------|---------------|
| **Claude API** | Optional（可以沒有） | 極簡 | 只有 tool input_schema |
| **OpenAI Assistants** | instructions（string） | 簡單 | 固定 5-6 參數 |
| **AutoGen** | system_message（string） | 簡單 | Agent type 選擇 |
| **CrewAI** | description + expected_output | YAML | 但只有 10-20 行 |
| **LangChain** | 自由字串 | 漸進式 | 無強制 |
| **我們** | 150 行 YAML | 過度 | 自己發明的格式 |

### 2.2 CrewAI 的 Task 定義（業界標準）

```yaml
# CrewAI 的 task 定義 - 簡潔明瞭
research_task:
  description: >
    Conduct research on {topic}.
    Focus on latest developments and key players.
  expected_output: >
    A comprehensive report with:
    - Executive summary
    - Key findings
    - Recommendations
  agent: researcher
```

**10 行，沒有 detection_patterns，沒有 tool_policy，沒有 review_criteria。**

### 2.3 Claude API 的 Tool 定義

```json
{
  "name": "get_weather",
  "description": "Get current weather for a location",
  "input_schema": {
    "type": "object",
    "properties": {
      "location": {"type": "string"}
    },
    "required": ["location"]
  }
}
```

**7 行，只定義 input schema，其他讓 LLM 自己判斷。**

---

## 3. Linus 式批判

### 3.1 違反「簡單優先」原則

> "Complexity is the enemy of reliability."

我們的 schema 試圖預測所有情況：
- 每個欄位的 detection_patterns
- 每個 phase 的 tool_policy
- 每個 review criterion 的 severity

**問題**：LLM 本來就會判斷這些，我們在重複造輪子。

### 3.2 違反「信任下游」原則

> "Don't do in the kernel what can be done in userspace."

我們不應該在 Config 層做 LLM 應該做的事：
- 判斷缺少什麼資訊 → LLM 能做
- 判斷工具使用時機 → LLM 能做
- 判斷輸出品質 → LLM 能做

### 3.3 違反「可維護性」原則

> "Code that is hard to read is hard to maintain."

150 行 YAML 意味著：
- 每新增一個領域，要寫 150 行
- 每次修改邏輯，要改 YAML + Python
- Debug 時要在兩個地方找問題

---

## 4. 我們的 Schema vs 業界做法

### 4.1 我們的做法（過度）

```yaml
# schemas/travel.yaml - 150 行
intake:
  required_fields:
    - name: departure_city
      question_zh: "從哪裡出發？"
      question_en: "Where are you departing from?"
      detection_patterns:
        - "從"
        - "出發"
        - "from"
        - "departing"
        - "starting"
        - "leaving"
# ... 還有 140 行
```

### 4.2 業界做法（簡潔）

**Option A: CrewAI Style（10 行）**
```yaml
travel_planning:
  description: |
    Plan a travel itinerary.
    MUST ask for: departure city, dates, budget scope.
  expected_output: |
    Day-by-day itinerary with budget breakdown.
```

**Option B: Claude Style（0 行 config，全在 prompt）**
```
You are a travel planner.

Before planning, ALWAYS confirm:
1. Departure city
2. Travel dates
3. Budget (total? per person? includes flights?)

Output must include budget breakdown.
```

**Option C: Minimal Schema（5 行）**
```yaml
travel:
  detect: [旅遊, travel, trip]
  require: [departure, dates, budget_scope]
```

---

## 5. 根因分析

### 為什麼我們會設計出 150 行 schema？

1. **不信任 LLM**：覺得要告訴 LLM 每個細節
2. **過度防禦**：想預防所有可能的錯誤
3. **錯誤抽象**：把「領域知識」抽象成「配置」而非「提示」

### 正確的思維

| 錯誤思維 | 正確思維 |
|---------|---------|
| "用 Config 控制 LLM 行為" | "用 Prompt 指導 LLM 行為" |
| "Schema 定義每個細節" | "Schema 只定義最小必要" |
| "不信任 LLM 判斷" | "信任 LLM，用 Review 把關" |

---

## 6. 建議方案

### 6.1 方案 A：極簡 Schema（推薦）

```yaml
# schemas/travel.yaml - 10 行
domain: travel
detect: [旅遊, 旅行, travel, trip, vacation]
intake_prompt: |
  Before planning, confirm: departure city, dates, budget scope.
output_prompt: |
  Include: day-by-day itinerary, budget breakdown, booking info.
```

**優點**：
- 10 行，不是 150 行
- 領域知識在 prompt，不是 detection_patterns
- 可維護、可擴展

### 6.2 方案 B：無 Schema（全 Prompt）

```python
# prompts/planner.yaml
system: |
  You are a planning specialist.

  ## Domain: Travel Planning
  Before planning any trip, ALWAYS ask for:
  - Departure city
  - Travel dates
  - Budget scope (total? per person? includes flights?)

  ## Domain: Code Task
  Before writing code, ALWAYS confirm:
  - Target language
  - Expected behavior
  - Any constraints

  ## Output Quality
  Every plan must include:
  - Itemized budget breakdown
  - Specific times and locations
  - Booking requirements
```

**優點**：
- 零配置文件
- 領域知識全在一個地方（prompt）
- LLM 自己判斷該問什麼

### 6.3 方案 C：Hybrid（折衷）

```yaml
# schemas/domains.yaml - 所有領域在一個文件
domains:
  travel:
    detect: [旅遊, travel]
    required_info: [departure, dates, budget]

  code:
    detect: [寫程式, implement, coding]
    required_info: [language, requirements]

  research:
    detect: [研究, research, analyze]
    required_info: [topic, scope]
```

**優點**：
- 一個文件，所有領域
- 只保留最小必要信息
- 具體指導在 prompt 中

---

## 7. 決策矩陣

| 方案 | 複雜度 | 可維護性 | 擴展性 | Linus 評分 |
|------|--------|----------|--------|-----------|
| 現狀（150 行/領域） | 高 | 低 | 差 | 🔴 |
| 方案 A（10 行/領域） | 低 | 高 | 好 | 🟢 |
| 方案 B（全 Prompt） | 極低 | 最高 | 最好 | 🟢 |
| 方案 C（Hybrid） | 低 | 高 | 好 | 🟢 |

---

## 8. 結論與行動建議

### Linus 的判決

```
"你在用 150 行 Config 解決 10 行 Prompt 能解決的問題。
這不是工程，這是過度設計。
刪掉 90% 的 Schema，把知識放回 Prompt。"
```

### 建議行動

1. **立即**：將 `schemas/*.yaml` 簡化為 10 行以內
2. **短期**：將領域知識移入 `prompts/*.yaml`
3. **長期**：評估是否完全移除 schema 系統

### 簡化後的目標

```
Before: 150 行 YAML + 200 行 Python (schema.py)
After:  10 行 YAML 或 0 行（全 Prompt）

Before: 新增領域需要 150 行 YAML + 修改 Python
After:  新增領域只需在 prompt 加幾行
```

---

## 9. 參考資料

- [CrewAI Tasks Documentation](https://docs.crewai.com/concepts/tasks)
- [Anthropic Tool Use](https://docs.anthropic.com/claude/docs/tool-use)
- [OpenAI Assistants API](https://platform.openai.com/docs/assistants)
- [LangGraph Tutorial](https://langchain-ai.github.io/langgraph/)

---

## 10. 附錄：刪除清單

如果採用方案 A 或 B，以下內容應該刪除：

```
schemas/travel.yaml      # 從 150 行 → 10 行
schemas/code_task.yaml   # 從 100 行 → 10 行
core/schema.py           # 從 300 行 → 50 行（或刪除）

移入 prompts/:
- detection_patterns     → 刪除，LLM 自己判斷
- tool_policy           → 刪除，用 prompt 指導
- output_requirements   → 移入 reviewer.yaml
- review_criteria       → 移入 reviewer.yaml
```
