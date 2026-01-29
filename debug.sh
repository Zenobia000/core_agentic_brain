#!/bin/bash
# 除錯模式啟動腳本

echo "🔍 啟動除錯模式..."
echo ""

# 設置環境變數
export LOG_HUMAN=true
export LOG_DEBUG=true

# 顯示當前設定
echo "📊 日誌設定："
echo "  • LOG_HUMAN=$LOG_HUMAN (人類可讀)"
echo "  • LOG_DEBUG=$LOG_DEBUG (詳細模式)"
echo ""

# 執行命令
if [ $# -eq 0 ]; then
    echo "🧠 進入互動模式 (輸入 'exit' 退出)"
    echo "================================================"
    python3 main.py
else
    echo "🔄 執行任務: $@"
    echo "================================================"
    python3 main.py "$@"
fi