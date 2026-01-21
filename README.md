# 🧠 Core Agentic Brain

智能助手系統 - 整合 OpenManus 後端和現代化 Web 前端

## 🚀 快速開始

### 1️⃣ 系統檢查
```bash
python check_system.py
```

### 2️⃣ 配置 API 密鑰
編輯 `.env` 檔案（如果不存在，運行系統檢查會自動創建）：
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 3️⃣ 安裝依賴
```bash
cd OpenManus
pip install -r requirements.txt
cd ..
```

### 4️⃣ 啟動系統
```bash
python web_run.py
```

### 5️⃣ 開始使用
打開瀏覽器訪問：http://localhost:8000

## ✨ 主要功能

- 🧠 **智能對話**: 基於 OpenManus 的 AI 助手
- 📊 **Token 監控**: 實時 Token 使用量監控和優化
- 🌐 **現代界面**: 響應式 Web 界面
- 🔧 **工具整合**: Browser、Search、Code 等工具
- 💾 **工作區管理**: 自動文件管理和工作區隔離

## 📚 完整文檔

查看 [啟動說明書.md](./啟動說明書.md) 獲取詳細的安裝、配置和使用指南。

## 🛠️ 故障排除

1. **依賴問題**: 運行 `python check_system.py` 檢查
2. **API 配置**: 檢查 `.env` 檔案中的 API 密鑰
3. **端口占用**: 嘗試更改端口 `uvicorn web_app.app:app --port 8001`

## 📊 系統監控

- **健康檢查**: http://localhost:8000/api/health
- **系統指標**: http://localhost:8000/api/metrics
- **API 文檔**: http://localhost:8000/docs

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 許可證

本項目使用開源許可證，詳見 LICENSE 文件。