# 配置系統升級說明

**日期**: 2026-01-29
**版本**: v2.0

## 📋 升級內容

借鑒 OpenManus 配置設計，實現多 LLM Provider 支援，同時保持 Linus 原則：簡單、直接、好預設值。

### 新增功能

1. **多 Provider 支援**
   - OpenAI (預設)
   - Anthropic Claude
   - Google Gemini
   - Azure OpenAI
   - Ollama (本地模型)

2. **統一配置架構**
   - `config.yaml` - 極簡主配置
   - `config.example.yaml` - 完整配置範例
   - `.env.example` - 環境變數範例

3. **自動 API Key 載入**
   - 根據 provider 自動載入對應環境變數
   - 支援 .env 檔案（需安裝 python-dotenv）

## 🔄 更新的檔案

| 檔案 | 說明 |
|------|------|
| `config.yaml` | 簡化為最小配置 |
| `config.example.yaml` | 新增 - 完整配置範例 |
| `.env.example` | 更新 - 多 provider API key 範例 |
| `core/config.py` | 支援多 provider API key 載入 |
| `core/llm.py` | 完全重寫 - 統一 LLM Provider 介面 |
| `test_config.py` | 新增 - 配置系統測試 |

## 🚀 使用方法

### 1. 基本使用（OpenAI）

```bash
# 設定環境變數
export OPENAI_API_KEY="sk-..."

# 使用預設配置
python3 main.py
```

### 2. 切換到 Anthropic

編輯 `config.yaml`:
```yaml
llm:
  provider: anthropic
  model: claude-3-haiku-20240307
```

設定環境變數:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. 使用 Ollama（本地模型）

編輯 `config.yaml`:
```yaml
llm:
  provider: ollama
  model: llama3.2
```

確保 Ollama 運行:
```bash
ollama serve  # 預設 http://localhost:11434
```

## 🔧 向後相容性

✅ **完全向後相容**:
- 舊式 `core.llm` 配置格式仍支援
- `LLMWrapper` 和 `LLMClient` 別名保留
- 預設使用 OpenAI，行為不變

## 📊 測試結果

```bash
python3 test_config.py
```

- ✅ 配置載入測試通過
- ✅ Ollama Provider 初始化成功
- ✅ 向後相容性測試通過
- ✅ API key 環境變數檢測正常

## 🎯 設計原則

遵循 Linus Torvalds 原則：

1. **好預設值勝過選項**
   - 預設 OpenAI + GPT-3.5，開箱即用
   - 大多數用戶不需要修改配置

2. **消除特殊情況**
   - 統一 LLMProvider 介面
   - 所有 provider 使用相同的 `generate()` 方法

3. **簡單是前提**
   - 主配置檔案只有 24 行
   - 核心功能程式碼保持精簡

## 📝 注意事項

1. API keys 優先從環境變數讀取，不要寫在配置檔案中
2. `.env` 檔案不要提交到版本控制
3. Ollama 需要本地安裝並運行服務
4. Anthropic 需要額外安裝：`pip install anthropic`

---

**Linus 會說**：
> "Talk is cheap. Show me the code."

代碼已完成，測試通過，系統運作正常。