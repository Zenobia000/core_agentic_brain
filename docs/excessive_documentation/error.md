**一句話結論：這段 log 其實很乾淨地告訴你一件事——「工具層（browser_use）初始化壞掉 + 網路對外不穩」，所以整個 agent 一直在做 fallback，最後靠 `wttr.in` 的簡化 endpoint 才勉強成功。**

---

## 1) 逐段拆解：這個 request 的實際執行劇本

### 1.1 Session / 分類階段

* `Session initialized: 20260121_114941_0b6093f6`

  * Session ID 正常，這個 ID 之後應該當你的 trace id（UI timeline 也靠它串起來）。

* `LLM classification failed: RetryError[...] raised TypeError, using fallback`

  * 你的 **task classifier**（可能是一個小 prompt 或小模型判斷）在重試後直接 TypeError。
  * 結果：系統啟用 fallback → `Task classified as 'general' with confidence 0.40`
  * 影響：

    1. 分類失準 → 後續工具選擇策略可能不夠精準（例如應該直接走 weather tool 或 web search provider）。
    2. Token 會更浪費，因為 agent 會在 general 模式下走比較「大而全」的推理迴圈。

**你現在缺的不是分類本身，而是：分類失敗要留下 stack trace + 版本資訊**，不然你永遠只能猜是哪個 TypeError。

---

### 1.2 Step 1：瀏覽器搜尋（失敗）

* tool args：`{"action":"web_search","query":"今天天气"}`
* 回來的錯誤：

  * `Browser.__init__() got an unexpected keyword argument 'headless'`

這句話的意思非常直接：

> 你的 OpenManus adaptor 在建立 Browser 物件時，丟了一個 `headless=` 參數，但你目前安裝的 browser library（或 wrapper）那個版本 **不接受這個參數**。

所以不是「web_search 不行」，而是「Browser 連起都起不來」。

---

### 1.3 Step 2：改用 go_to_url（仍失敗）

* tool args：`{"action":"go_to_url","url":"https://www.weather.com.cn"}`
* 一樣死在：

  * `Browser.__init__() got an unexpected keyword argument 'headless'`

這非常關鍵：
**你可以把任何 browser action 都關掉了，因為根本不是 action 問題，是 Browser 初始化就爆。**

---

### 1.4 Step 3：python_execute 打 wttr.in（失敗，Connection reset）

* 嘗試：`requests.get("https://wttr.in/?format=j1", timeout=10)`
* 錯誤：`ConnectionResetError(104, 'Connection reset by peer')`

意思是：TCP 建連後被對方或中間設備強制切斷。常見原因（從工程角度）：

1. 公司網路/防火牆/Proxy 對 `wttr.in` 這類服務不友善
2. `wttr.in` 對某些來源 IP 有 rate limit / block
3. TLS/中間人設備導致連線被 reset
4. requests 沒走你的企業 proxy 設定（環境變數沒帶進去）

---

### 1.5 Step 4：python_execute 改用 wttr.in 的「更短回應格式」（成功）

* 改成：

  * `https://wttr.in/?format=%l:+%c+%t+%h+%w`
* 成功回來：

  * `Taichung, Taiwan: ⛅️ +16°C 68% ↓19km/h`

這裡很有趣：同一個服務，`j1`（JSON）被 reset，但「純文字 format」成功了。工程上代表：

* 不是 DNS 全掛
* 不是 HTTPS 全掛
* 比較像是：

  * JSON 回應比較大、被某個中間設備判定異常而切斷
  * 或 `j1` endpoint 被特別限流/阻擋
  * 或第一次連線不穩、第二次剛好成功（你的 retry/backoff 還不夠系統化）

---

## 2) 你現在系統的 3 個「真問題」（按優先順序）

### 問題 A：browser_use adaptor / 依賴版本不一致（最致命）

**症狀：** `Browser.__init__` 不吃 `headless`
**結論：** 你的 browser_use 這條工具鏈目前「不可用」，而 agent 還一直選它。

你要做兩件事：

1. **把 browser_use 標記成 unhealthy**（短期）

   * 一旦出現 `Browser.__init__` 類錯誤，就直接熔斷（circuit breaker），後面 steps 不要再選它。
2. **鎖版本 or 改 adaptor**（根治）

   * 不是「修 action」，是「修 Browser 初始化參數傳遞」。

---

### 問題 B：對外網路連線不穩（或被企業環境干擾）

**症狀：** `Connection reset by peer`
**建議：**

* requests 要統一走企業 proxy（若你在公司內網）
* 對外 API 要做：

  * retry（含 jitter）
  * fallback provider（至少 2 個來源）
  * timeout 分級（connect/read）

---

### 問題 C：Token 使用對「查天氣」來說太肥

你這個 query 才一句話，但 Input tokens 已經到：

* Step1 前：Input=2454
* Step2：Input=2842
* Step3：Input=3244
* Step4：Input=4212

這代表你每一步都在把大量上下文餵回去（可能包含：

* 全量 system prompt
* 工具 schema 很長
* 前面 step 的 observation 全部回灌）

**這會讓「簡單任務」變得又慢又貴，也更容易撞 rate limit。**

---

## 3) 具體可落地的修正清單（你可以直接開 ticket）

### 3.1 Tool 熔斷（避免 Step 1/2 這種重複撞牆）

* 規則：若觀測到以下字串之一，就把 `browser_use` 標記 unhealthy（30 分鐘或直到重啟）

  * `Browser.__init__() got an unexpected keyword argument`
  * `Playwright not installed`
  * `BrowserType.launch` 類初始化錯

效果：
agent 不會再浪費 step 嘗試 browser，會直接走 python / api fallback。

---

### 3.2 修 browser_use 初始化參數（版本一致化）

你要在 repo 做一個「工具版本契約」：

* `requirements.lock / poetry.lock` 嚴格鎖住 browser_use + 相關 browser backend（playwright/selenium…）
* adaptor 層不要硬塞 `headless=`，改用該版本正確的 config 方式

（你前面那個錯誤就是典型「套件升級後參數簽名改了」。）

---

### 3.3 weather provider 改成「多來源 + 明確地點」

你這次回來 Taichung，原因很可能是：

* `wttr.in` 用你的 IP 推測位置（或環境預設）

建議做法：

* prompt 只要沒城市，就：

  1. 問使用者城市（如果是 chat app）
  2. 或用系統配置預設城市（如果是內部系統，像「台北廠」）

並且 provider 至少兩個：

* Provider1：wttr 純文字（快、容易成功）
* Provider2：你可信任的正式 weather API（公司可控、穩定、可簽 SLA）

---

### 3.4 Token slimming：把「觀測」改成摘要回灌

你現在每 step 都把完整觀測塞回 LLM。改成：

* tool observation 先做一層「摘要/結構化」再回灌
* 原始全文只存到 artifact store（UI timeline 展開才看）

這會直接讓：

* 成本下降
* latency 下降
* LLM 判斷更穩（不會被一堆雜訊淹沒）

---

## 4) 五歲小孩也懂的版本

你現在像是：

* 叫外送（查天氣）
* 你先派了機車外送員（browser_use）
  結果機車根本發不動（init 就爆）
* 你改叫走路送（python requests）
  路上又被警衛擋了一次（connection reset）
* 最後換小路走（wttr 純文字 format）才送到

所以要做的就是：

1. 機車修好（browser 版本一致）
2. 被擋要有備案（多 provider + retry）
3. 不要每走一步就把整本日記塞給大腦看（token slimming）

---

## 5) 口訣（三個重點）

1. **先修初始化**：Browser 起不來，任何 action 都沒用
2. **加熔斷與備援**：撞牆一次就換路，不要連撞兩次
3. **瘦身回灌**：Observation 存檔，回灌只給摘要

---

如果你想我「直接定位」那個 `headless` 到底是哪段程式塞進去的：
把你專案裡 `browser_use` 的 wrapper / adaptor 檔案（通常在 `app/tools/` 或 `app/agent/tools/` 附近）貼 30~80 行（包含 Browser 初始化那段），我就能精準指出要改哪一行、以及「鎖哪個版本」最不容易踩雷。
