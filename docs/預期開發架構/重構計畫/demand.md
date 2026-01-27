一句話：**OpenCode 在「CLAUDE.md 記憶／規則、skills、MCP、hooks」這幾塊已經刻意對齊 Claude Code，所以可以當你要的「平替骨架」；要長成像 OpenManus 那種通用型 agent，關鍵是「外掛一層編排大腦」，而不是把 IDE 本體硬改成 agent 框架。**

---

## 1) 先回答你最在意的：OpenCode 能不能做到 Claude Code 那套「可客製化專用 agent」？

你提的核心能力，我把它拆成 4 塊來驗證：

### 1.1 記憶 / 系統提示詞注入（CLAUDE.md）

* **Claude Code**：官方明講內建 system prompt 不公開；你要加自訂指示，就用 `CLAUDE.md` 或 `--append-system-prompt`。([Claude Docs][1])
  而且 Claude Code 會**遞迴向上讀取**多層 `CLAUDE.md`（repo 很大時超好用）。([Claude Docs][2])
* **OpenCode**：它把「規則」做成一等公民（Rules），並且**刻意提供 Claude Code 相容層**：優先讀 `AGENTS.md`，並可 fallback 到 `CLAUDE.md`（相容層可用環境變數關掉）。([opencode.ai][3])

👉 **結論**：你把 Claude Code 當「上下文管理器」的那個靈魂（用檔案來注入規則/記憶），OpenCode **是跟得上的**。

---

### 1.2 Skills（Markdown 技能庫）

* **Claude Code**：skills 用 Markdown 檔定義，放在 `.claude/skills/`，可被 Claude 自動挑選或用 `/skill-name` 叫用。([Claude Docs][4])
* **OpenCode**：也有 skills 機制，而且**直接讀 `.claude/skills` / `~/.claude/skills` 作相容**（同時也有它自己的 `.opencode/skills` 路徑）。([opencode.ai][5])

👉 **結論**：你現在那套「用 Markdown 管 prompt/技能」的工作流，搬到 OpenCode **成本很低**。

---

### 1.3 MCP（把工具/沙箱封裝成可插拔能力）

* **OpenManus**：README 直接給「MCP tool version：`python run_mcp.py`」，也有 multi-agent flow：`python run_flow.py`。([GitHub][6])
* **OpenCode**：工具層明確支援 **MCP servers**（用來接 DB、API、第三方服務）。([opencode.ai][7])

👉 **結論**：你想走「把 agent sandbox / tools / prompts 包成 MCP，讓前端（OpenCode）去調用」這條路，**兩邊在抽象層級上是對齊的**。

---

### 1.4 Hooks / Plugins（治理、守門、可觀測性）

* **OpenCode**：外掛系統很完整：

  * 支援事件訂閱（session / permission / tool execute before/after / tui events…）
  * 甚至可直接加 **custom tools**，也能做 `.env` 防護那種「政策 gate」([opencode.ai][8])

👉 **結論**：你想做「Policy Gate + 工具白名單 + 審計」這種企業內部 agent 必備的治理面，OpenCode **反而更像一個可掛載的 runtime**。

---

### ✅ 1.5 所以 OpenCode 是不是「Claude Code 平替」？

**在「你關心的可客製化骨架」層面：是。**
但我會更精準地講：**OpenCode 更像一個「可開源改造的 Claude Code 底盤」**——尤其在 rules/skills/MCP/plugins 這些 extension points 上，它已經把洞都留好了。([opencode.ai][8])

> 小提醒：Claude Code 還有 `.claude/commands/*.md`、subagents、hooks、settings.json 那一整套官方治理與格式定義（SDK 文件有列位置）。([Claude Docs][4])
> OpenCode 有自己的 commands/agents 規格（文件頁面可對照），但「100% drop-in」通常要靠你做一層轉換或 symlink/adapter。([opencode.ai][9])

---

## 2) 你對 OpenManus 的觀察很準：ReAct 會讓它「每個任務都得想」

OpenManus 目前就是典型「框架型 agent」：

* 一個主循環（main.py）→ 需要配置 `config.toml` → 然後跑一般版 / MCP 版 / multi-agent flow 版([GitHub][6])
  這種設計的優點是通用、清楚；缺點也明顯：**小任務也會被迫進入「規劃→思考→工具→再思考」的循環**（成本、延遲、token 都上去）。

而你要的其實是：

> **像 Claude Code 那樣：平常是「上下文管理 + 工具調用」，只有需要時才升級成「多步 agent」**

---

## 3) 目標架構：把 OpenCode 變成「通用 AI Agent 系統入口」的正確姿勢

### 核心策略（很 Linus）

**不要把 OpenCode 改成 OpenManus。**
要做的是：**讓 OpenCode 保持小而美（terminal/IDE/context manager），把「通用 agent 編排」做成外掛或外部服務。**

> Linus 那套味道就是：**核心要小、介面要穩、功能用模組長出去**。
> 你做 MCP + plugin，本質就是在做「穩定介面」。

---

### 3.1 三層架構（建議）

```mermaid
flowchart LR
  U[User in OpenCode TUI/CLI] --> OC[OpenCode\nContext + Tools + Permissions]
  OC -->|plugin event / command| ORC[Orchestrator\n(Planner+Router+Memory)]
  ORC -->|MCP client| TG[Tool Gateway (MCP)]
  TG --> S1[MCP: Sandbox Bash/Python]
  TG --> S2[MCP: Repo Ops / CI]
  TG --> S3[MCP: DB / Tickets / Internal APIs]
  ORC --> KB[(Memory: AGENTS.md / CLAUDE.md / skills)]
  OC --> AUD[(Audit/Logs)]
```

* **OpenCode**：負責「互動、上下文、工具權限、plugin hooks」([opencode.ai][8])
* **Orchestrator**：你從 OpenManus 拆出來、重做的「規劃大腦」
* **Tool Gateway**：全部工具用 MCP 封裝（沙箱、內部系統、外部 API）

---

## 4) 把你的想法落成工程：需求 → 可行性 → 系統設計 → 詳設（給你一份可當 RSD/SDD 的骨架）

## 4.1 明確需求與目標（RSD 摘要）

### 目標（Goals）

1. **OpenCode 成為單一入口**：同一套規則/skills，既能寫程式，也能做通用任務（查資料、產報告、跑流程）。
2. **任務分級**：

   * fast path：單步工具調用（像 Claude Code 日常）
   * agent path：多步規劃與工具鏈（像 OpenManus）
3. **企業級治理**：權限白名單、工具沙箱、審計紀錄、可觀測性（至少 tool.execute 前後可攔截）([opencode.ai][8])

### 非目標（Non-goals）

* 不把 OpenCode fork 成「巨型框架」
* 不在 v1 就追求「自動無限規劃」——先可控、可重現

### 驗收條件（Acceptance Criteria）

* 同一 repo 內：

  * `AGENTS.md/CLAUDE.md` 能控制行為（coding standards / 任務偏好）([Claude Docs][2])
  * skills 可被自動/手動調用([opencode.ai][5])
* 具備「策略路由」：小事不進 ReAct，大事才進多步
* 所有外部能力都走 MCP，可替換、可測試([opencode.ai][7])

---

## 4.2 可行性分析

### 技術可行性

* OpenCode 已有 plugins + tool hooks + MCP 概念：很適合當「宿主」([opencode.ai][8])
* OpenManus 已提供 MCP 版入口（`run_mcp.py`）與 flow 版入口（`run_flow.py`），拆大腦合理([GitHub][6])

### 經濟可行性（工程成本怎麼省）

* **最省**：Orchestrator 先做「Router + Minimal Planner」
  不追求全自動，只追求「把對的任務丟給對的 sub-agent/skill/tool」

### 時間可行性（不報日期，報工程量）

* S：OpenCode plugin + MCP gateway + 2~3 個工具 server
* M：加入任務路由、可觀測性、最小多代理（2-3 種角色）
* L：完整 flow 編排（含重試、回滾、長任務、狀態機）

---

## 5) 系統設計（System Design）

### 5.1 介面設計：讓「編排大腦」可替換（Linus 友善）

把 Orchestrator 做成**純 MCP server**或一個本地 service，對外只暴露穩定介面：

* `plan(task, context) -> plan_steps`
* `execute(step) -> result`
* `summarize(run) -> short_summary`
* `policy_check(tool_call) -> allow/deny + reason`

OpenCode 端只需要：

* 一個 plugin：攔截 prompt / command → 決定走 fast path 還是丟給 orchestrator([opencode.ai][8])

### 5.2 Prompt/Rules 的統一來源

* 以 `AGENTS.md/CLAUDE.md` 當「repo 級規格書」
* skills 當「可重用 SOP」
* subagents 當「角色卡」

Claude Code 的精神是：**用檔案，而不是改內建 system prompt**([Claude Docs][1])
OpenCode/你這套也應該延續：**一切可版本控制、可 code review。**

---

## 6) 詳細設計（Detailed Design）

### 6.1 Router（最關鍵的那一刀）

你其實需要一個「不那麼聰明、但很準」的路由器：

* **fast path**（直接在 OpenCode 內解）：

  * 改小檔、補測試、重構、查單一文件
* **agent path**（丟 orchestrator）：

  * 需要跨系統（CI/DB/Jira）
  * 需要多步決策、需要回滾
  * 需要長上下文整理（log/多份文件）

> 你討厭 ReAct「每次都想」的痛點，就在這裡解：**先判斷需不需要想。**

### 6.2 Tool Sandbox 全 MCP 化

* bash/python/file ops：一個 MCP server（可加資源限制、目錄白名單）
* 企業內部系統：一系統一 server（權限與審計獨立）

OpenCode 這邊用 plugins 去做：

* tool.execute.before：政策檢查、遮罩敏感路徑([opencode.ai][8])
* tool.execute.after：落 audit log、摘要回傳([opencode.ai][8])

---

## 7) 用 Linus 的眼光「挑毛病」（我覺得你會喜歡這段）

如果用一句很不客氣的話來檢視：

* **不要做一個「看起來很厲害」的 agent 框架。**
  做一個「介面很乾淨」的 orchestrator，才跑得久。

對應到你要的開源疊代目的：

1. **核心小**：OpenCode 不 fork 大改；Orchestrator 獨立 repo、可替換。
2. **介面穩**：MCP / JSON schema 先定，裡面怎麼規劃都能改。
3. **可讀可測**：所有規則與 prompt 都是檔案（AGENTS/CLAUDE/skills），可 review、可回滾。([Claude Docs][2])

---

## 心法內化（五歲小孩也懂）

你就想像你在蓋一台機器人：

* **OpenCode 是「遙控器 + 儀表板」**
* **OpenManus 的精華是「大腦的思考流程」**([GitHub][6])
* **MCP 是「機器人的手跟工具箱」**([opencode.ai][7])

遙控器不用變大腦。
你只要把大腦接上去，手跟工具也接上去。就會動了。

---

## 口訣（3 個重點）

1. **小事別 ReAct**：先 Router，能直做就直做。
2. **工具全 MCP**：能力模組化，才能疊代、治理、換血快。([opencode.ai][7])
3. **規則都進 Git**：AGENTS/CLAUDE/skills 一律可版本控、可 review。([Claude Docs][2])

---

如果你願意我直接再往下補一份「System Design 文件」的可貼上版本（含：資料夾結構、MCP server 合約草案、Router 判斷準則表、最小可行的 subagents/skills 列表），我會用你現在的工作流語言去寫（`.opencode/` + `.claude/` 共存、逐步遷移）。

[1]: https://docs.anthropic.com/en/docs/claude-code/settings?utm_source=chatgpt.com "Claude Code settings - Claude Code Docs"
[2]: https://docs.anthropic.com/en/docs/claude-code/memory?utm_source=chatgpt.com "Manage Claude's memory"
[3]: https://opencode.ai/docs/mcp-servers/?utm_source=chatgpt.com "MCP servers"
[4]: https://docs.anthropic.com/en/docs/claude-code/sdk?utm_source=chatgpt.com "Agent SDK overview - Claude Docs"
[5]: https://opencode.ai/docs/skills/ "Agent Skills | OpenCode"
[6]: https://github.com/FoundationAgents/OpenManus "GitHub - FoundationAgents/OpenManus: No fortress, purely open ground.  OpenManus is Coming."
[7]: https://opencode.ai/docs/tools/ "Tools | OpenCode"
[8]: https://opencode.ai/docs/plugins/ "Plugins | OpenCode"
[9]: https://opencode.ai/docs/commands/?utm_source=chatgpt.com "Commands"

## 一句話結論

**OpenCode 在「CLAUDE.md/.claude 規則 + sub-agent + skills + MCP + permission」這條路上，官方文件已經把關鍵積木都給你了；OpenManus 不一定必要，更像是可參考的「編排腦」樣板——要不要導入，取決於你想省下多少自研編排成本、以及你能不能接受 Python/Prompt/Tool 風格差異。** ([OpenCode][1])

---

## 1) 你要我「幫你確認」的點：OpenCode 能不能做到 Claude Code 那套可客製化？

我用官方文件逐項對照你提的能力（不是靠印象）：

### 1.1 規則檔與上下文管理（CLAUDE.md / AGENTS.md 這類）

OpenCode 的 **Rules** 明確寫：支援 `AGENTS.md`、`OPENCODE.md`，並且**相容 Claude Code 的慣例**（也就是你說的「用 md 來當系統提示詞/規則載體」那個味道）。([OpenCode][1])

### 1.2 sub-Agent / 多代理分工（Task tool + subagent）

OpenCode 的 **Agents** 機制支援 `primary/subagent/hidden`，而且有 **permission.task** 去控管「某個 agent 能不能叫某些 subagent」——這基本就是你要的「可控的子代理編排」。([OpenCode][2])

### 1.3 skills（`.claude/skills` 類）

OpenCode 的 **Skills** 直接講：支援 `.claude/skills/*.md`（Claude Code 相容路徑），也支援 `.opencode/skill/*.md`；並且還能用 `permission.skill` 做 allow/deny/ask。([OpenCode][3])

### 1.4 MCP（把 tools / sandbox / prompts 包成 MCP 給 OpenCode 用）

OpenCode 有完整的 **MCP servers** 設定：local/remote 都支援，`type: local` 時還能用 `command: [...]` 啟動你的 MCP server（npx/bun 都行），remote 也能設 `url/headers/OAuth`。([OpenCode][4])

### 1.5 權限 / 安全閘門（permission）

OpenCode 有 **Permissions**，可對 `edit/bash/...` 設 `allow/ask/deny`，甚至可 wildcard；而且文件也提醒預設行為與可調整方式。([OpenCode][5])

### 1.6 Plugin 擴充（在工具調用前後掛勾、加規則、做路由）

OpenCode 有 **Plugins**，可用事件 hooks 擴充行為（例如你想做「先規劃→再執行」的路由器）。([OpenCode][6])

> 小提醒：目前社群回報 `permission.ask` 這個 hook 在某版本「宣告了但沒觸發」，如果你打算用 plugin 直接攔權限決策，要把這個風險算進去。([GitHub][7])

**結論：**以官方文件來看，OpenCode 已經把你在 Claude Code 覺得好用的「md 規則 + skills + subagent + MCP + permission」核心拼圖補齊了，重疊度非常高。([OpenCode][1])

---

## 2) OpenManus 的必要性？（你問得很準）

你貼的 OpenManus（mannaandpoem/OpenManus）其實在 Archive repo 的 README 就講得很直白：

* 這是「initial complete version」
* 另有 **MCP tool version：`python run_mcp.py`**
* 另有 **multi-agent version：`python run_flow.py`，而且標註 unstable**
* 並且提示最新更新在另一個 repo（FoundationAgents/OpenManus）([GitHub][8])

所以我會把 **OpenManus 的價值**切成兩種：

### 2.1 當「參考樣板」：很值

它把「Agent 需要的三件事：規劃、執行、記憶」用一套可跑的原型兜起來，對你要拆“orchestrator/flow”很有參考價值。([GitHub][8])

### 2.2 當「直接可整合的核心模組」：不一定值（尤其你偏好 md 驅動）

原因很現實：

* OpenManus 的 prompt/tool/agent 管理偏 **Python 實作**、風格與你想要的「md 規則驅動」不同。([GitHub][8])
* 即使它有 `run_mcp.py`，社群也指出它的工具擴充常見路徑仍是繼承內部 BaseTool/execute（等於你要做 MCP-first 還是得加 adapter）。([developer.aliyun.com][9])
* 最關鍵：它自己把 multi-agent 標成 **unstable**，你如果目標是「可長期疊代的開源基座」，反而要慎選。([GitHub][8])

**因此：OpenManus 不一定必要。**
你的目標如果是「把 OpenCode 往通用型 agent 平台推」，更像是：**用 OpenCode 當“上下文/互動/工具入口”，編排腦自己做（或外掛服務化）**。

---

## 3) 你想要的整合藍圖：用 OpenCode 做殼，把“通用型 AI Agent 系統”做成可插拔編排層

你原句其實已經接近答案：

> 「把 agent sandbox tools prompts 包成 mcp 讓 opencode 使用」

我會建議你把整體拆成三層（符合你提的 Linus 思想：核心小、介面穩、可替換）：

```mermaid
flowchart LR
  UI[OpenCode TUI/IDE\n(上下文管理器)] --> ORC[Orchestrator 編排腦\n(你的核心價值)]
  ORC -->|Task/Subagents| SA[Subagents: Planner/Executor/Reviewer]
  ORC -->|MCP tools| MCP[MCP Tool Plane\nsandbox/tools/prompts]
  MCP --> SYS[Internal Systems\n(Jira/DB/CI/CD/Docs)]
  UI -->|Rules/Skills| CTX[AGENTS.md / OPENCODE.md\n.claude/skills/*.md]
  UI -->|Permission| PG[permission allow/ask/deny]
```

這樣做的好處是：

* **OpenCode 維持它最擅長的：互動 + 工具調用 + rules/skills 供給**。([OpenCode][10])
* 你的 **Orchestrator** 才是長期疊代的核心（可參考 OpenManus 的 flow/agent 觀念，但不被 Python 實作綁死）。([GitHub][8])
* tool plane 全走 MCP：你要 sandbox、公司系統、特殊工具，全部都變成 “可插拔伺服器”。([OpenCode][4])

---

## 4) 「OpenCode 能否自己開發？」以及「要不要導入 OpenManus 核心模組？」我給你三個務實選項

### 選項 A｜只用 OpenCode：你自己做 Orchestrator（我覺得最合你口味）

你用 OpenCode 的：

* Rules（md）([OpenCode][1])
* Skills（`.claude/skills`）([OpenCode][3])
* Agents/Subagents + permission.task ([OpenCode][2])
* MCP servers（local/remote/OAuth）([OpenCode][4])
* Permissions（allow/ask/deny）([OpenCode][5])

去拼出「可控、可擴、md 驅動」的通用代理系統。

**你失去的**：OpenManus 已經幫你寫好的 flow/規劃迴圈原型。
**你得到的**：語言/結構一致、長期維護成本更低、比較像你說的 “context manager + 可客製化專用 agent”。

---

### 選項 B｜OpenManus 只當參考設計，不直接導入程式碼（最 Linus）

你把 OpenManus 當「規格書」：

* 參考它怎麼分 planning / execution / memory
* 參考它怎麼做 flow（雖然它標 unstable）([GitHub][8])
  然後把這些概念，用 **OpenCode 的 agent/subagent + MCP tool plane** 重寫成一套「你自己的 orchestrator」。

---

### 選項 C｜把 OpenManus 服務化，當一個 MCP tool（只在你真的想省時間時）

如果你真的想吃現成 flow：

* 讓 OpenManus 跑成一個獨立服務（它 repo 已經有 `run_mcp.py`/`run_mcp_server.py` 的線索）([GitHub][8])
* OpenCode 端把它註冊成 remote/local MCP server（`type/command/url` 那套）([OpenCode][4])
* OpenCode → 呼叫「orchestrate(task)」這個 MCP tool → 回傳 plan/結果

**代價**：你會同時背兩套世界觀（Python prompt/tool 與 md rules 驅動），而且 multi-agent 在那個版本自己都寫 unstable。([GitHub][8])

---

## 5) 你下一步該怎麼選（不繞圈，直接給判斷準則）

把問題縮成一句很殘酷的話：

> 你要的是「可長期疊代的開源平台底座」，還是「先跑起來的代理原型」？

* **要底座（你描述更像這個）** → 選 A 或 B
* **要快、先有 flow demo** → 選 C（但要把 unstable/雙栈維護算清楚）([GitHub][8])

---

## 文末心法（五歲也懂版本）

把 OpenCode 想成「一台很會溝通、很會記規則、也很會叫工具的小助理」。
OpenManus 比較像「教科書裡的做事流程」。
你要做通用型系統，其實是：**讓小助理照你的流程做事**——流程你寫（Orchestrator），工具用插的（MCP），規則用貼的（md）。

---

## 口訣（三個重點）

1. **殼用 OpenCode**（rules/skills/agents/permission 都有）([OpenCode][1])
2. **腦你自己養**（orchestrator 才是長期價值）
3. **工具全 MCP**（可插拔、可 sandbox、可企業整合）([OpenCode][4])

如果你要我更「落地」：我可以直接幫你把 Orchestrator 拆成 **Planner / Executor / Critic / ToolRouter** 四個 subagents 的配置策略（對應哪些 permission、哪些 MCP server 要啟用、rules/skills 放哪），讓工程師照著 repo 結構就能開工。

[1]: https://opencode.ai/docs/rules/?utm_source=chatgpt.com "Rules"
[2]: https://opencode.ai/docs/agents/ "Agents | OpenCode"
[3]: https://opencode.ai/docs/skills/?utm_source=chatgpt.com "Agent Skills"
[4]: https://opencode.ai/docs/mcp-servers/ "MCP servers | OpenCode"
[5]: https://opencode.ai/docs/permissions/?utm_source=chatgpt.com "Permissions"
[6]: https://opencode.ai/docs/plugins/?utm_source=chatgpt.com "Plugins"
[7]: https://github.com/anomalyco/opencode/issues/7006?utm_source=chatgpt.com "`permission.ask` plugin hook is defined but not triggered"
[8]: https://github.com/mannaandpoem/OpenManus_Archive "GitHub - mannaandpoem/OpenManus_Archive"
[9]: https://developer.aliyun.com/article/1659823?utm_source=chatgpt.com "手撕“开源版Manus” - 阿里云开发者社区"
[10]: https://opencode.ai/docs/?utm_source=chatgpt.com "Intro"
