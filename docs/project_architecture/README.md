# Core Agentic Brain - 專案架構文檔

## 📚 文檔目錄

本目錄包含 Core Agentic Brain 專案的完整系統架構與設計文檔。

### 文檔清單

1. **[系統架構 (System Architecture)](./01_System_Architecture.md)**
   - 整體架構設計
   - 分層架構說明
   - 系統組件描述
   - 非功能性需求

2. **[系統設計 (System Design)](./02_System_Design.md)**
   - 詳細模組設計
   - 資料模型定義
   - 演算法設計
   - 實作規格

3. **[技術實作指南 (Technical Implementation Guide)](./03_Technical_Implementation_Guide.md)**
   - 開發環境設置
   - 核心實作步驟
   - 工具開發指南
   - 部署與維護

4. **[API 規格 (API Specification)](./04_API_Specification.md)**
   - REST API 端點
   - WebSocket API
   - SDK 使用範例
   - 錯誤處理規範

---

## 🎯 架構理念

### 核心原則

**「簡單的事情應該簡單，複雜的事情應該可能」**

本專案採用 **漸進式分層架構**，結合：
- Linus Torvalds 的極簡主義哲學
- 企業級功能的可擴展性
- Claude Code 的相容性

### 三層設計

```
Layer 0: 極簡核心 (<500 行)
  ├── 基本 AI 對話
  ├── 簡單工具調用
  └── 零配置啟動

Layer 1: 智慧路由 (可選)
  ├── 任務複雜度分析
  ├── 快速/代理路徑
  └── 簡單代理協作

Layer 2: 企業擴展 (可選)
  ├── 權限控制系統
  ├── 審計日誌追蹤
  └── MCP 協議支援
```

---

## 🚀 快速導航

### 開發者

- 新手入門 → 閱讀 [技術實作指南](./03_Technical_Implementation_Guide.md) 第 1-2 節
- 了解架構 → 閱讀 [系統架構](./01_System_Architecture.md) 第 1-2 節
- API 開發 → 參考 [API 規格](./04_API_Specification.md)

### 架構師

- 整體設計 → [系統架構](./01_System_Architecture.md) 完整文檔
- 詳細設計 → [系統設計](./02_System_Design.md) 完整文檔
- 技術決策 → 參考各文檔的 ADR 章節

### 產品經理

- 功能規格 → [系統架構](./01_System_Architecture.md) 第 3 節
- API 功能 → [API 規格](./04_API_Specification.md) 概覽部分
- 部署選項 → [技術實作指南](./03_Technical_Implementation_Guide.md) 第 6 節

---

## 📊 架構決策摘要

| 決策項目 | 選擇 | 理由 |
|---------|------|------|
| **程式語言** | Python 3.10+ | 生態豐富、開發效率高 |
| **架構模式** | 漸進式分層 | 平衡簡單性與擴展性 |
| **預設模式** | 極簡模式 | 降低入門門檻 |
| **工具協議** | MCP | 標準化工具介面 |
| **前端框架** | 原生 JS | 零依賴、完全控制 |

---

## 🔄 文檔版本

| 文檔 | 版本 | 最後更新 | 狀態 |
|-----|------|---------|------|
| System Architecture | 1.0 | 2026-01-27 | ✅ 已批准 |
| System Design | 1.0 | 2026-01-27 | ✅ 已批准 |
| Implementation Guide | 1.0 | 2026-01-27 | ✅ 已發布 |
| API Specification | 1.0 | 2026-01-27 | ✅ 已發布 |

---

## 📈 專案狀態

### 實作進度

- [x] Layer 0: 極簡核心
- [x] 基礎工具 (Python, Files)
- [ ] Layer 1: 智慧路由
- [ ] Layer 2: 企業功能
- [ ] 完整測試覆蓋
- [ ] 生產部署準備

### 關鍵指標

| 指標 | 目標 | 當前 |
|-----|------|------|
| 核心代碼行數 | < 500 | 設計中 |
| 冷啟動時間 | < 2s | 設計中 |
| 響應時間 P95 | < 1s | 設計中 |
| 測試覆蓋率 | > 80% | 設計中 |

---

## 🛠 開發資源

### 相關連結

- [專案根目錄](../../)
- [原始碼](../../core/)
- [配置範例](../../config.yaml)
- [測試套件](../../tests/)

### 開發指令

```bash
# 快速啟動
python main.py

# 運行測試
pytest

# 檢查程式碼品質
black . && ruff check .

# 建立 Docker 映像
docker build -t core-brain .
```

---

## 📝 貢獻指南

歡迎貢獻！請確保：

1. 遵循現有的程式碼風格
2. 保持極簡設計原則
3. 更新相關文檔
4. 添加適當的測試

---

## 📞 聯繫方式

- GitHub Issues: [問題回報](https://github.com/org/core-agentic-brain/issues)
- Email: team@core-brain.dev
- 文檔問題: 請在對應文檔中提出

---

**維護團隊:** Core Agentic Brain 架構組
**最後更新:** 2026-01-27