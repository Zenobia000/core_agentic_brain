# 行為驅動開發指南 - OpenManus Linus 式重構

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2025-01-21`
**主要作者 (Lead Author):** `QA Lead & Tech Lead`
**審核者 (Reviewers):** `產品經理, 開發團隊`
**狀態 (Status):** `已批准 (Approved)`

---

## 目錄 (Table of Contents)

1. [BDD 方法論 (BDD Methodology)](#第-1-部分bdd-方法論-bdd-methodology)
2. [功能場景定義 (Feature Scenarios)](#第-2-部分功能場景定義-feature-scenarios)
3. [驗收測試標準 (Acceptance Criteria)](#第-3-部分驗收測試標準-acceptance-criteria)
4. [測試實施策略 (Testing Implementation)](#第-4-部分測試實施策略-testing-implementation)

---

**目的**: 本文件定義基於行為的測試方法，確保 OpenManus 重構專案符合 Linus 式簡潔哲學，同時滿足所有用戶需求和品質標準。

---

## 第 1 部分：BDD 方法論 (BDD Methodology)

### 1.1 Linus 式 BDD 原則

#### 核心理念
> **"代碼要做的事情應該顯而易見。測試要驗證的行為也應該顯而易見。"** - Linus 哲學應用於測試

| BDD 原則 | Linus 式解釋 | 實際應用 |
| :--- | :--- | :--- |
| **Given-When-Then** | 明確的前置條件、行為、結果 | 避免複雜的測試設置 |
| **用戶語言** | 技術人員和用戶都能理解 | 簡單直白的場景描述 |
| **行為優先** | 關注做什麼，而非怎麼做 | 測試用戶體驗，不測試實現細節 |
| **實例驅動** | 具體的例子而非抽象描述 | 真實的使用場景 |

#### BDD 品質閘門
```python
BDD_QUALITY_GATES = {
    "scenario_clarity": "場景描述無需額外解釋",
    "user_perspective": "從用戶角度描述行為",
    "testable_outcomes": "結果可觀察和驗證",
    "minimal_setup": "最少的前置條件",
    "realistic_data": "使用真實的測試數據"
}
```

### 1.2 測試金字塔 (Linus 簡化版)

#### 測試優先級分配
```
    🔺 單元測試 (10%)
   ▂▂▂ 只測試核心邏輯函數
  ▃▃▃▃▃ 集成測試 (20%)
 ▄▄▄▄▄▄▄ 關鍵路徑端到端測試
████████████ 手動探索測試 (70%)
           真實用戶場景驗證
```

#### 反模式避免
```python
# ❌ 避免的測試反模式
TESTING_ANTIPATTERNS = {
    "test_implementation": "不要測試實現細節",
    "fragile_tests": "避免因小改動就失敗的測試",
    "slow_tests": "測試執行時間應 < 5 秒",
    "complex_setup": "測試準備不應比實際邏輯複雜",
    "unclear_assertions": "斷言應該清楚表達預期"
}
```

---

## 第 2 部分：功能場景定義 (Feature Scenarios)

### 2.1 核心功能場景

#### Feature 1: 系統啟動與初始化
```gherkin
Feature: 系統快速啟動
  作為終端用戶
  我希望系統能快速啟動
  以便立即開始使用 AI 助手

  Background:
    Given 系統已安裝所有依賴
    And 配置檔案存在並正確設置

  Scenario: 命令行模式快速啟動
    Given 用戶在 OpenManus 目錄
    When 用戶執行 "python main.py"
    Then 系統應在 2 秒內啟動
    And 顯示 "manus>" 提示符
    And 系統狀態為 "準備就緒"

  Scenario: Web 模式啟動
    Given 用戶在 OpenManus 目錄
    When 用戶執行 "python main.py --web"
    Then 系統應在 2 秒內啟動 Web 服務
    And 在瀏覽器中打開 http://localhost:8000
    And 顯示聊天界面
    And 連接狀態顯示 "🟢 已連線"

  Scenario: 直接提示執行
    Given 用戶在 OpenManus 目錄
    When 用戶執行 "python main.py --prompt 'hello world'"
    Then 系統應在 2 秒內回應
    And 輸出包含 AI 回應
    And 系統正常退出

  Scenario: 配置錯誤處理
    Given 配置檔案不存在或格式錯誤
    When 用戶嘗試啟動系統
    Then 系統應顯示清楚的錯誤訊息
    And 提供解決問題的建議
    And 系統優雅退出
```

#### Feature 2: AI 對話交互
```gherkin
Feature: 自然語言對話
  作為終端用戶
  我希望能與 AI 進行自然對話
  以便完成各種任務

  Background:
    Given 系統已啟動並準備就緒
    And LLM API 可正常訪問

  Scenario: 簡單問答
    Given 用戶在命令行模式
    When 用戶輸入 "什麼是 Python?"
    Then AI 應在 3 秒內回應
    And 回應內容相關且有幫助
    And 系統繼續等待下一個輸入

  Scenario: 多輪對話
    Given 用戶在命令行模式
    When 用戶輸入 "請介紹一下你自己"
    Then AI 回應自我介紹
    When 用戶續問 "你能做什麼?"
    Then AI 回應能力清單
    And 保持對話上下文

  Scenario: Web 界面對話
    Given 用戶在 Web 界面
    When 用戶在輸入框輸入 "hello"
    And 點擊發送按鈕
    Then 訊息出現在聊天區域
    And 顯示 "思考中..." 狀態
    And AI 回應出現在聊天區域
    And 思考狀態消失

  Scenario: 長文本處理
    Given 用戶提供長篇文本 (>1000 字)
    When AI 處理該文本
    Then 系統應正常處理而不崩潰
    And 回應時間不超過 10 秒
    And 回應內容完整且相關
```

#### Feature 3: 工具調用與執行
```gherkin
Feature: Python 代碼執行
  作為終端用戶
  我希望 AI 能執行 Python 代碼
  以便完成編程任務

  Background:
    Given 系統已啟動
    And Python 工具已載入

  Scenario: 簡單代碼執行
    Given 用戶請求 "計算 2+2"
    When AI 生成並執行 Python 代碼 "print(2+2)"
    Then 執行結果應為 "4"
    And AI 回應包含計算結果
    And 執行時間少於 3 秒

  Scenario: 錯誤代碼處理
    Given 用戶請求執行有語法錯誤的代碼
    When AI 執行該代碼
    Then 系統捕獲錯誤訊息
    And 返回清楚的錯誤說明
    And 系統保持穩定運行

  Scenario: 文件操作
    Given 用戶請求 "創建一個 hello.txt 文件"
    When AI 使用文件工具創建文件
    Then 文件應成功創建在工作目錄
    And 文件內容符合要求
    And 返回操作成功確認

Feature: 瀏覽器操作
  作為終端用戶
  我希望 AI 能獲取網頁內容
  以便處理網路資訊

  Background:
    Given 系統已啟動
    And 瀏覽器工具已載入
    And 網路連接正常

  Scenario: 網頁內容獲取
    Given 用戶請求 "獲取 example.com 的內容"
    When AI 使用瀏覽器工具訪問網站
    Then 應成功獲取網頁內容
    And 內容長度合理 (<2000 字符)
    And 響應時間少於 10 秒

  Scenario: 網路錯誤處理
    Given 用戶請求訪問不存在的網站
    When AI 嘗試訪問該網站
    Then 系統應捕獲網路錯誤
    And 返回友好的錯誤訊息
    And 系統繼續正常運行
```

### 2.2 邊界條件場景

#### Feature 4: 系統限制與錯誤處理
```gherkin
Feature: 系統穩定性
  作為系統管理員
  我希望系統在異常情況下保持穩定
  以便提供可靠的服務

  Scenario: 超長輸入處理
    Given 用戶輸入超過 10000 字符的文本
    When 系統處理該輸入
    Then 系統應優雅處理或拒絕
    And 給出清楚的限制說明
    And 系統保持響應

  Scenario: API 限制處理
    Given LLM API 達到使用限制
    When 用戶嘗試發送請求
    Then 系統應捕獲 API 錯誤
    And 顯示友好的錯誤訊息
    And 建議稍後再試

  Scenario: 記憶體壓力測試
    Given 系統運行多個並發對話
    When 記憶體使用接近限制
    Then 系統應優雅降級
    And 保持核心功能可用
    And 記憶體使用不超過 100MB

  Scenario: 網路中斷處理
    Given 系統正在運行
    When 網路連接中斷
    Then 本地功能繼續工作
    And 清楚標示網路狀態
    And 網路恢復後自動重連
```

---

## 第 3 部分：驗收測試標準 (Acceptance Criteria)

### 3.1 功能驗收標準

#### 系統啟動 (System Startup)
```python
STARTUP_ACCEPTANCE_CRITERIA = {
    "cold_start_time": {
        "target": "< 1 秒",
        "maximum": "< 2 秒",
        "measurement": "從執行 main.py 到顯示提示符"
    },
    "memory_usage": {
        "target": "< 50MB",
        "maximum": "< 100MB",
        "measurement": "RSS 記憶體使用量"
    },
    "error_handling": {
        "requirement": "所有錯誤都有清楚說明",
        "test_cases": ["缺少配置", "API Key 錯誤", "網路不通"]
    }
}
```

#### 對話品質 (Conversation Quality)
```python
CONVERSATION_ACCEPTANCE_CRITERIA = {
    "response_time": {
        "simple_query": "< 3 秒",
        "complex_task": "< 10 秒",
        "tool_execution": "< 5 秒"
    },
    "response_quality": {
        "relevance": "回應與問題相關",
        "completeness": "回答完整解決問題",
        "clarity": "語言清晰易懂"
    },
    "context_maintenance": {
        "short_term": "保持 3-5 輪對話上下文",
        "coherence": "回應邏輯一致"
    }
}
```

#### 工具功能 (Tool Functionality)
```python
TOOL_ACCEPTANCE_CRITERIA = {
    "python_execution": {
        "success_rate": "> 95%",
        "timeout": "< 30 秒",
        "safety": "安全沙盒執行"
    },
    "browser_access": {
        "success_rate": "> 90%",
        "timeout": "< 10 秒",
        "content_length": "< 2000 字符"
    },
    "file_operations": {
        "read_success": "> 99%",
        "write_success": "> 99%",
        "error_handling": "清楚的錯誤訊息"
    }
}
```

### 3.2 非功能性驗收標準

#### 性能標準 (Performance Standards)
```python
PERFORMANCE_ACCEPTANCE_CRITERIA = {
    "scalability": {
        "concurrent_users": "支持 5 個並發 WebSocket 連接",
        "memory_per_session": "< 20MB",
        "response_degradation": "< 10% 在負載下"
    },
    "reliability": {
        "uptime": "> 99% 在 24 小時測試中",
        "error_recovery": "自動從暫時性錯誤中恢復",
        "data_integrity": "不丟失用戶輸入或對話"
    },
    "resource_usage": {
        "cpu_idle": "< 5% 待機時",
        "cpu_active": "< 50% 處理時",
        "disk_space": "< 50MB 總占用"
    }
}
```

#### 可用性標準 (Usability Standards)
```python
USABILITY_ACCEPTANCE_CRITERIA = {
    "learning_curve": {
        "first_time_user": "10 分鐘內能成功對話",
        "developer_onboarding": "5 分鐘理解架構",
        "tool_extension": "30 分鐘添加新工具"
    },
    "error_messages": {
        "clarity": "用戶能理解錯誤原因",
        "actionability": "包含解決問題的建議",
        "consistency": "相似錯誤使用一致的訊息格式"
    },
    "interface_design": {
        "command_line": "直觀的命令行界面",
        "web_interface": "簡潔的 Web 聊天界面",
        "accessibility": "基本的鍵盤導航支持"
    }
}
```

---

## 第 4 部分：測試實施策略 (Testing Implementation)

### 4.1 測試環境設置

#### 環境配置
```bash
# 測試環境設置腳本
#!/bin/bash
# test_setup.sh

echo "設置 OpenManus 測試環境..."

# 1. 創建測試目錄
mkdir -p test_workspace
cd test_workspace

# 2. 複製核心文件
cp -r ../openmanus .
cd openmanus

# 3. 創建測試配置
cat > config.test.yaml << EOF
agent:
  llm_model: "gpt-3.5-turbo"  # 使用較便宜的模型進行測試
  api_key: "${OPENAI_API_KEY_TEST}"
  max_tokens: 1000
  max_steps: 5
  tools:
    - python
    - files

workspace:
  path: "./test_workspace"
  auto_cleanup: true

web:
  host: "127.0.0.1"
  port: 8001  # 使用不同端口避免衝突
EOF

# 4. 安裝測試依賴
pip install pytest httpx

echo "✅ 測試環境設置完成"
```

### 4.2 自動化測試腳本

#### 核心功能測試
```python
# tests/test_core_functionality.py
import pytest
import subprocess
import time
import json
import websocket

class TestSystemStartup:
    """系統啟動測試"""

    def test_command_line_startup_time(self):
        """測試命令行啟動時間"""
        start_time = time.time()
        result = subprocess.run(
            ["python", "main.py", "--prompt", "hello"],
            capture_output=True,
            text=True,
            timeout=5
        )
        end_time = time.time()

        # 驗收標準: 啟動時間 < 2 秒
        assert (end_time - start_time) < 2.0
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_web_mode_startup(self):
        """測試 Web 模式啟動"""
        # 在背景啟動 Web 服務器
        process = subprocess.Popen(
            ["python", "main.py", "--web"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # 等待服務啟動
        time.sleep(3)

        try:
            # 測試 HTTP 連接
            import requests
            response = requests.get("http://localhost:8001", timeout=5)
            assert response.status_code == 200
            assert "OpenManus" in response.text

            # 測試 WebSocket 連接
            ws = websocket.create_connection("ws://localhost:8001/ws")
            ws.send(json.dumps({"type": "prompt", "content": "test"}))
            result = ws.recv()
            assert len(result) > 0
            ws.close()

        finally:
            process.terminate()
            process.wait()

class TestAIConversation:
    """AI 對話測試"""

    def test_simple_conversation(self):
        """測試簡單對話"""
        result = subprocess.run(
            ["python", "main.py", "--prompt", "什麼是 2+2?"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0
        assert "4" in result.stdout
        assert len(result.stdout.strip()) > 10  # 回應有實質內容

    def test_python_tool_execution(self):
        """測試 Python 工具執行"""
        prompt = "請用 Python 計算 3 * 7 的結果"
        result = subprocess.run(
            ["python", "main.py", "--prompt", prompt],
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode == 0
        assert "21" in result.stdout

class TestErrorHandling:
    """錯誤處理測試"""

    def test_invalid_config(self):
        """測試無效配置處理"""
        # 暫時重命名配置檔案
        import os
        os.rename("config.yaml", "config.yaml.bak")

        try:
            result = subprocess.run(
                ["python", "main.py", "--prompt", "test"],
                capture_output=True,
                text=True,
                timeout=5
            )

            # 應該優雅失敗並提供有用訊息
            assert result.returncode != 0
            assert "配置" in result.stderr or "config" in result.stderr.lower()

        finally:
            os.rename("config.yaml.bak", "config.yaml")

    def test_network_error_handling(self):
        """測試網路錯誤處理"""
        # 創建無效 API Key 的配置
        invalid_config = """
agent:
  llm_model: "gpt-4"
  api_key: "invalid_key"
  max_tokens: 100
  max_steps: 1
  tools: []
"""
        with open("config.invalid.yaml", "w") as f:
            f.write(invalid_config)

        try:
            result = subprocess.run(
                ["python", "main.py", "--config", "config.invalid.yaml",
                 "--prompt", "test"],
                capture_output=True,
                text=True,
                timeout=10
            )

            # 應該有清楚的錯誤訊息
            assert "API" in result.stdout or "錯誤" in result.stdout

        finally:
            import os
            os.remove("config.invalid.yaml")
```

### 4.3 手動測試檢查清單

#### 用戶體驗測試
```markdown
# 手動測試檢查清單

## 基本功能測試 (30 分鐘)

### 系統啟動測試
- [ ] `python main.py` 快速啟動 (< 2 秒)
- [ ] 顯示清楚的提示符
- [ ] `help` 命令顯示使用說明
- [ ] `exit` 命令正常退出

### 命令行對話測試
- [ ] 簡單問答: "你好" → 有意義的回應
- [ ] 計算任務: "計算 15 * 23" → 正確結果
- [ ] 編程任務: "寫一個 hello world" → 生成代碼並執行
- [ ] 文件操作: "創建一個測試文件" → 成功創建

### Web 界面測試
- [ ] `python main.py --web` 啟動 Web 服務
- [ ] 瀏覽器自動打開或手動訪問 localhost:8000
- [ ] 聊天界面顯示正常
- [ ] 連接狀態顯示 "🟢 已連線"
- [ ] 發送消息正常工作
- [ ] 思考狀態正確顯示

## 高級功能測試 (15 分鐘)

### 工具集成測試
- [ ] Python 代碼執行正常
- [ ] 瀏覽器獲取網頁內容
- [ ] 文件讀寫操作正常
- [ ] 錯誤情況優雅處理

### 性能測試
- [ ] 冷啟動時間 < 2 秒
- [ ] 簡單查詢響應 < 3 秒
- [ ] 記憶體使用 < 100MB
- [ ] 長時間運行穩定

### 錯誤處理測試
- [ ] 無配置檔案 → 清楚錯誤訊息
- [ ] 無效 API Key → 友好提示
- [ ] 網路中斷 → 優雅降級
- [ ] 無效輸入 → 正確處理

## 代碼品質檢查 (15 分鐘)

### Linus 式品味檢查
- [ ] 沒有特殊情況 if/elif 分支
- [ ] 所有函數職責單一
- [ ] 代碼自我解釋，無需註釋
- [ ] 統一的工具介面
- [ ] 配置集中在一個檔案

### 架構檢查
- [ ] 總代碼行數 < 900 行
- [ ] 單函數 < 20 行
- [ ] 嵌套深度 < 3 層
- [ ] 外部依賴 < 10 個
```

### 4.4 持續測試策略

#### 開發階段測試
```python
DEVELOPMENT_TESTING_SCHEDULE = {
    "daily": [
        "核心功能回歸測試 (10 分鐘)",
        "新功能手動驗證 (15 分鐘)",
        "性能基準檢查 (5 分鐘)"
    ],
    "weekly": [
        "完整功能測試套件 (60 分鐘)",
        "邊界條件測試 (30 分鐘)",
        "用戶體驗測試 (45 分鐘)"
    ],
    "release": [
        "全面驗收測試 (120 分鐘)",
        "性能壓力測試 (60 分鐘)",
        "部署驗證測試 (30 分鐘)"
    ]
}
```

#### 品質閘門
```python
QUALITY_GATES = {
    "commit": {
        "基本功能測試通過",
        "代碼符合 Linus 式規範",
        "無語法錯誤或明顯 bug"
    },
    "merge": {
        "所有自動化測試通過",
        "手動測試檢查清單完成",
        "性能指標符合要求"
    },
    "release": {
        "完整驗收測試通過",
        "用戶體驗測試滿意",
        "文檔與代碼同步"
    }
}
```

---

**批准簽字**:
- QA Lead: ✅ 已批准 (2025-01-21)
- Tech Lead: ✅ 已批准 (2025-01-21)
- 產品經理: ✅ 已批准 (2025-01-21)

**下一步**: 開始按照測試場景進行開發驗證