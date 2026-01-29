# 日誌系統說明

## 設計原則
基於 Linus Torvalds 的哲學：
- **簡單直接**：77行代碼實現完整日誌系統
- **零配置**：合理預設值，開箱即用
- **環境變數**：簡單的開關控制

## 配置方式

日誌系統**只使用環境變數**配置（不使用 config.yaml）：

### 環境變數設定

在 `.env` 檔案中設定：

```bash
# === 日誌設定 ===
LOG_DEBUG=true     # 啟用詳細除錯（預設 false）
LOG_HUMAN=true     # 人類可讀（預設 true）
LOG_DIR=logs/      # 日誌目錄（預設 workspace/logs）
```

### 預設值

- `LOG_HUMAN=true` - 預設啟用人類可讀格式
- `LOG_DEBUG=false` - 預設關閉除錯模式
- `LOG_DIR=workspace/logs` - 預設日誌目錄

## 使用方式

### 1. 簡潔模式（預設）
```bash
python3 main.py "你的任務"
```
只顯示關鍵事件和結果。

### 2. 除錯模式
```bash
# 方法一：設定環境變數
export LOG_DEBUG=true
python3 main.py "你的任務"

# 方法二：使用除錯腳本
./debug.sh "你的任務"

# 方法三：在 .env 設定
# 編輯 .env，設定 LOG_DEBUG=true
```
顯示詳細的執行過程，包括：
- LLM 分析策略
- 任務複雜度
- 選擇的代理
- 執行時間
- 參數細節

### 3. 臨時關閉人類可讀
```bash
export LOG_HUMAN=false
python3 main.py "你的任務"
```
完全關閉控制台輸出（通常不需要）。

## 日誌格式

### 簡潔模式輸出
```
18:01:36 info            LLM analyzing task
18:01:38 info            LLM analysis complete
18:01:39 agent.complete  Executor completed in 936ms
```

### 除錯模式輸出
```
18:01:36 info            LLM analyzing task
            └─ prompt=分析系統架構
            └─ strategy=sequential
            └─ complexity=moderate
18:01:39 agent.complete  Executor completed in 936ms
            └─ agent=Executor
            └─ result=系統架構分析完成...
```

## 事件類型

- `info` - 一般資訊
- `debug` - 除錯資訊（需要 LOG_DEBUG=true）
- `agent.*` - 代理相關事件
- `error` - 錯誤訊息

## 為什麼不用 config.yaml？

遵循 Linus 的原則：
1. **消除重複**：避免多處配置同一功能
2. **簡單直接**：環境變數是最簡單的配置方式
3. **合理預設**：大部分情況不需要配置

## 檔案說明

- `core/simple_logger.py` - 日誌系統實作（77行）
- `.env` - 環境變數設定
- `debug.sh` - 快速除錯腳本

## 注意事項

1. config.yaml 中的 logging 設定**已被移除**（未使用）
2. 所有日誌配置統一使用環境變數
3. 除錯日誌會寫入 `workspace/logs/debug_YYYYMMDD.log`