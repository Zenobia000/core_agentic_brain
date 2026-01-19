@echo off
REM OpenManus++ Setup Script for Windows
REM 設置虛擬環境並安裝依賴

echo 🚀 OpenManus++ Setup
echo ====================

REM 檢查 Python
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Error: Python not found
    exit /b 1
)

REM 建立虛擬環境
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo 📦 Virtual environment already exists
)

REM 啟動虛擬環境
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM 升級 pip
echo ⬆️  Upgrading pip...
pip install --upgrade pip

REM 安裝依賴
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM 安裝 playwright browsers
echo 🌐 Installing Playwright browsers...
playwright install chromium

REM 複製配置檔案
if not exist "config\config.toml" (
    echo 📝 Creating config file from template...
    copy config\config.example.toml config\config.toml
    echo ⚠️  Please edit config\config.toml with your API keys!
)

echo.
echo ✅ Setup Complete!
echo.
echo Next steps:
echo   1. Activate venv:  venv\Scripts\activate
echo   2. Edit config:    notepad config\config.toml
echo   3. Run:            python main.py
echo.
