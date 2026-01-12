# 📁 Agent Context Directory

此目錄用於儲存各 Agent 的工作上下文和輸出報告。

## 📂 目錄結構

```
context/
├── decisions/      # 架構決策記錄 (ADR)
├── deployment/     # 部署配置和紀錄
├── docs/           # 文檔產出
├── e2e/            # E2E 測試相關
├── general/        # 通用 Agent 報告
├── quality/        # 程式碼品質報告
├── security/       # 安全審計報告
├── testing/        # 測試策略和報告
└── workflow/       # 工作流程相關
```

## 📝 使用說明

### Agent 產出位置

| Agent | 輸出目錄 |
|-------|---------|
| general-purpose | `general/` |
| code-quality-specialist | `quality/` |
| test-automation-engineer | `testing/` |
| security-auditor | `security/` |
| documentation-specialist | `docs/` |
| pdf-analyzer | `docs/` |
| report-generator | `docs/` |
| web-researcher | `docs/` |

### 命名規範

```
{type}_{date}_{description}.md

範例:
- quality_20240101_api-module-review.md
- security_20240101_auth-audit.md
- testing_20240101_user-service-tests.md
```

### 內容格式

所有報告應包含：
- 標題和日期
- Agent 識別
- 摘要
- 詳細內容
- 建議行動

## 🔄 維護

- 定期清理過時報告
- 重要決策歸檔至 `decisions/`
- 保持目錄結構一致

---

**此目錄由 TaskMaster Hub 系統自動管理**
