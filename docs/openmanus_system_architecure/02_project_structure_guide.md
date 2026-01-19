# 專案結構指南 (Project Structure Guide) - OpenManus

---

**文件版本 (Document Version):** `v1.0`

**最後更新 (Last Updated):** `2025-10-14`

**主要作者 (Lead Author):** `OpenManus Team`

**審核者 (Reviewers):** `Community Contributors`

**狀態 (Status):** `已批准 (Approved)`

---

## 目錄 (Table of Contents)

1.  [概述 (Overview)](#1-概述-overview)
2.  [目錄結構總覽 (Directory Structure Overview)](#2-目錄結構總覽-directory-structure-overview)
3.  [核心目錄說明 (Core Directory Description)](#3-核心目錄說明-core-directory-description)
4.  [非標準/特殊目錄 (Non-Standard/Special Directories)](#4-非標準特殊目錄-non-standardspecial-directories)

---

## 1. 概述 (Overview)

### 1.1 文件目的 (Document Purpose)
*   本文檔旨在標準化 OpenManus 的專案結構，幫助開發者快速定位程式碼與資源。
*   定義了各目錄的職責與命名規範。

---

## 2. 目錄結構總覽 (Directory Structure Overview)

```text
OpenManus/
├── app/                    # 應用程式核心源碼
│   ├── agent/              # Agent 實作 (Base, Manus, ToolCall)
│   ├── flow/               # 流程控制 (Planning)
│   ├── mcp/                # Model Context Protocol 相關
│   ├── prompt/             # 提示詞模板 (Prompts)
│   ├── sandbox/            # 沙箱環境 (Execution Sandbox)
│   ├── tool/               # 工具集 (Browser, File, Python, Search)
│   ├── utils/              # 通用工具函式
│   ├── config.py           # 配置加載邏輯
│   ├── llm.py              # LLM 介面封裝
│   ├── logger.py           # 日誌配置
│   └── schema.py           # 數據模型定義 (Pydantic)
├── assets/                 # 靜態資源 (Logo, Images)
├── config/                 # 配置文件 (config.toml, mcp.json)
├── examples/               # 範例與 Benchmark
├── protocol/               # 通訊協議實作
├── tests/                  # 測試代碼
├── workspace/              # 運行時工作目錄 (Sandbox Mount)
├── main.py                 # CLI 入口點
├── run_mcp_server.py       # MCP Server 入口點
├── requirements.txt        # Python 依賴清單
├── setup.py                # 套件安裝腳本
└── Dockerfile              # Docker 建置檔
```

---

## 3. 核心目錄說明 (Core Directory Description)

### 3.1 `app/` (核心應用層)
*   **職責**: 包含所有業務邏輯與核心功能。
*   **關鍵子目錄**:
    *   `agent/`: 定義 Agent 的行為與生命週期 (`Manus` 是主 Agent)。
    *   `tool/`: 存放所有可用工具 (`BrowserUseTool`, `PythonExecute` 等)。
    *   `sandbox/`: 負責安全執行代碼的環境管理。

### 3.2 `config/` (配置層)
*   **職責**: 存放應用程式配置。
*   **關鍵檔案**:
    *   `config.toml`: 主配置文件 (API Key, Model 設定)。
    *   `mcp.json`: MCP Server 的連接配置。

### 3.3 `workspace/` (數據層)
*   **職責**: Agent 運行時的「工作台」。
*   **說明**: 這是 Sandbox 環境掛載的目錄，Agent 生成的文件、讀取的數據都在這裡。此目錄內容通常不應提交到 Git (除了 `.gitkeep` 或範例)。

---

## 4. 非標準/特殊目錄 (Non-Standard/Special Directories)

### 4.1 `protocol/`
*   **說明**: 包含特定通訊協議的實作，目前主要是 `a2a` (Agent-to-Agent)。
*   **注意**: 這部分可能隨架構演進而變動。

### 4.2 `examples/`
*   **說明**: 包含使用案例 (`use_case`) 和基準測試 (`benchmarks`)。
*   **用途**: 供使用者參考如何使用 OpenManus 解決特定問題。
