# 開發環境與建置清單 (Development Environment & Build Manifest) - OpenManus

---

**文件版本 (Document Version):** `v1.0`

**最後更新 (Last Updated):** `2025-10-14`

**主要作者 (Lead Author):** `OpenManus Team`

**審核者 (Reviewers):** `Community Contributors`

**狀態 (Status):** `已批准 (Approved)`

---

## 目錄 (Table of Contents)

1.  [概述 (Overview)](#1-概述-overview)
2.  [系統依賴 (System Dependencies)](#2-系統依賴-system-dependencies)
3.  [環境變數清單 (Environment Variables)](#3-環境變數清單-environment-variables)
4.  [建置與執行指令 (Build & Run Commands)](#4-建置與執行指令-build--run-commands)
5.  [除錯指南 (Debugging Guide)](#5-除錯指南-debugging-guide)
6.  [IDE 配置建議 (IDE Setup)](#6-ide-配置建議-ide-setup)

---

## 1. 概述 (Overview)

### 1.1 文件目的 (Document Purpose)
*   本文檔旨在確保所有開發者（包括未來的自己）能在 15 分鐘內搭建出完全一致的 OpenManus 開發與建置環境。
*   解決 "It works on my machine" 問題，統一團隊開發基準。

### 1.2 適用範圍 (Scope)
*   適用於 OpenManus 專案的所有開發、測試與 CI/CD 環境配置。

---

## 2. 系統依賴 (System Dependencies)

### 2.1 基礎環境 (Base Environment)
*   **OS**: `Linux (Recommended) / macOS / Windows (via WSL2)`
*   **Runtime**: `Python >= 3.12`
*   **Package Manager**: `uv` (Recommended) or `pip`
*   **Virtual Environment**: `venv` or `conda`

### 2.2 外部依賴 (External Services)
*本專案主要依賴外部 API 服務，本地依賴較少。*

| 服務名稱 | 版本要求 | 用途 | 備註 |
| :--- | :--- | :--- | :--- |
| **LLM Provider** | `N/A` | 提供核心智能 (OpenAI/Anthropic/Ollama) | 需 API Key |
| **Docker** | `19.03+` | 運行 Sandbox 環境 | 選用 (Sandboxed execution) |

---

## 3. 環境變數清單 (Environment Variables)

主要透過 `config/config.toml` 進行配置，部分敏感資訊可透過環境變數覆蓋。

| 變數名稱 | 必填 | 預設值/範例 | 描述 |
| :--- | :---: | :--- | :--- |
| `OPENAI_API_KEY` | ❌ | `sk-...` | OpenAI API Key (若使用 OpenAI) |
| `ANTHROPIC_API_KEY` | ❌ | `sk-ant-...` | Anthropic API Key (若使用 Claude) |
| `BING_SEARCH_V7_SUBSCRIPTION_KEY` | ❌ | `...` | Bing Search Key (若使用 Bing Search) |

---

## 4. 建置與執行指令 (Build & Run Commands)

### 4.1 安裝依賴 (Install Dependencies)
```bash
# 推薦使用 uv 進行快速安裝
pip install uv
uv pip install -r requirements.txt

# 或者使用標準 pip
pip install -r requirements.txt
```

### 4.2 啟動本地環境 (Start Local Environment)
```bash
# 運行主程式 (CLI 模式)
python main.py

# 帶參數運行
python main.py --prompt "幫我查一下明天的天氣"
```

### 4.3 啟動 MCP Server (Start MCP Server)
```bash
# 啟動 MCP Server (Stdio 模式)
python run_mcp_server.py
```

### 4.4 運行測試 (Run Tests)
```bash
pytest tests/
```

### 4.5 使用 Docker 運行 (Run with Docker)
```bash
# 建置映像檔
docker build -t openmanus .

# 運行容器
docker run -it --rm openmanus
```

---

## 5. 除錯指南 (Debugging Guide)

### 5.1 日誌 (Logs)
*   **Log System**: 使用 `loguru` 進行日誌記錄。
*   **Log Level**: 預設輸出到 `stderr`，級別為 `INFO`。

### 5.2 常見問題排除 (Troubleshooting)
*   **Error: `ModuleNotFoundError`**: 
    *   **解法**: 確保已啟動虛擬環境且執行了 `pip install -r requirements.txt`。
*   **Error: API Key Missing**:
    *   **解法**: 檢查 `config/config.toml` 是否已正確填寫 API Key。

---

## 6. IDE 配置建議 (IDE Setup)

### 6.1 推薦插件 (Recommended Extensions)
*   **VSCode**:
    *   `Python` (Microsoft)
    *   `Pylance` (Microsoft)
    *   `Black Formatter` (Microsoft)
    *   `Ruff` (Astral Software)

### 6.2 格式化與 Linting (Formatter & Linter)
*   **Python**: 使用 `Ruff` 進行 Linting，`Black` 進行格式化。
*   **設定**: 建議開啟 "Format On Save"。
