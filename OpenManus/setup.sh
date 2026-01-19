#!/bin/bash
# OpenManus++ Setup Script
# 設置虛擬環境並安裝依賴

set -e

echo "🚀 OpenManus++ Setup"
echo "===================="

# 檢查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "📍 Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.10" ]]; then
    echo "❌ Error: Python 3.10+ required"
    exit 1
fi

# 建立虛擬環境
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv $VENV_DIR
    echo "✅ Virtual environment created"
else
    echo "📦 Virtual environment already exists"
fi

# 啟動虛擬環境
echo "🔄 Activating virtual environment..."
source $VENV_DIR/bin/activate

# 升級 pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# 安裝依賴
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# 安裝 playwright browsers (如果需要)
echo "🌐 Installing Playwright browsers..."
playwright install chromium || echo "⚠️  Playwright install skipped (optional)"

# 複製配置檔案
if [ ! -f "config/config.toml" ]; then
    echo "📝 Creating config file from template..."
    cp config/config.example.toml config/config.toml
    echo "⚠️  Please edit config/config.toml with your API keys!"
fi

echo ""
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "  1. Activate venv:  source venv/bin/activate"
echo "  2. Edit config:    nano config/config.toml"
echo "  3. Run:            python main.py"
echo ""
