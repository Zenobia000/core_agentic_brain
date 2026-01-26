#!/bin/bash
# 開發環境啟動腳本

set -e

echo "🚀 Starting OpenCode Platform Development Environment..."

# 檢查環境變數
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set"
    echo "   Please set it: export OPENAI_API_KEY='your-key'"
fi

# 檢查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# 啟動依賴服務
echo "📦 Starting dependencies (Redis, Qdrant)..."
docker compose -f docker/docker-compose.yml up -d redis qdrant

# 等待服務就緒
echo "⏳ Waiting for services to be ready..."
sleep 5

# 檢查 Qdrant
if curl -s http://localhost:6333/health > /dev/null; then
    echo "✅ Qdrant is ready"
else
    echo "⚠️  Qdrant may not be ready yet"
fi

# 檢查 Redis
if docker exec $(docker ps -qf "name=redis") redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis may not be ready yet"
fi

echo ""
echo "🎉 Development environment is ready!"
echo ""
echo "Available commands:"
echo "  opencode chat -i          # Interactive chat"
echo "  opencode tui              # Terminal UI"
echo "  python -m api.main        # Start API server"
echo ""
echo "To stop services:"
echo "  docker compose -f docker/docker-compose.yml down"
