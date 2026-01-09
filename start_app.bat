@echo off
chcp 65001
title 企業知識庫助手啟動器

echo ========================================================
echo 🚀 正在啟動 企業知識庫助手 (RAG智能回答系統)...
echo ========================================================
echo.

:: 1. 檢查 Python 環境
if not exist ".venv\Scripts\python.exe" (
    echo ❌ 找不到 .venv 虛擬環境，請確認安裝步驟！
    pause
    exit
)

:: 2. 啟動後端 (開一個新視窗)
echo [1/3] 正在啟動後端 API (Port 8001)...
start "RAG Backend API" cmd /k "call .venv\Scripts\activate && python -m src.main"

:: 等待 3 秒讓後端先跑起來
timeout /t 3 /nobreak >nul

:: 3. 啟動前端 (開一個新視窗)
echo [2/3] 正在啟動前端介面 (Port 3000)...
cd frontend
if not exist "node_modules" (
    echo ⚠️ 初次執行，正在安裝前端依賴 (npm install)...
    call npm install
)
start "RAG Frontend UI" cmd /k "npm run dev"

:: 4. 自動打開瀏覽器
echo [3/3] 系統啟動完成！正在開啟瀏覽器...
timeout /t 2 /nobreak >nul
start http://localhost:3000

echo.
echo ✅ 服務已在背景執行。
echo 💡 後端 API: http://localhost:8001/docs
echo 💡 前端 UI:  http://localhost:3000
echo.
pause