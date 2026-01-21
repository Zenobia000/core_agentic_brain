# 📋 Phase 1: 基礎設施遷移指南

## 🎯 目標
建立標準化的開發環境和基礎架構，為後續重構打好基礎。

---

## 📅 時程規劃 (Week 1)

### Day 1-2: 環境建置
### Day 3-4: 資料庫設計
### Day 5-7: CI/CD 設置

---

## 🗂️ 目錄重組作業

### Step 1: 備份現有程式碼
```bash
# 1. 創建備份分支
git checkout -b backup/legacy-architecture
git push origin backup/legacy-architecture

# 2. 創建重構分支
git checkout main
git checkout -b feature/architecture-refactor
```

### Step 2: 建立新目錄結構
```bash
#!/bin/bash
# scripts/setup-new-structure.sh

# 建立前端目錄
mkdir -p frontend/{public,src/{components,hooks,services,stores,types,utils}}

# 建立後端目錄
mkdir -p backend/app/{api/{v1,v2},core,services,repositories,models,schemas,events,websocket}

# 建立核心邏輯目錄
mkdir -p manus_core/{agents,tools/{browser,python},flows,memory,llm}

# 建立基礎設施目錄
mkdir -p database/{migrations,seeds}
mkdir -p deployment/{docker,kubernetes/{manifests,helm},nginx}
mkdir -p scripts
mkdir -p docs/{api,architecture,deployment}
mkdir -p shared/{types,utils,constants}

echo "📁 新目錄結構建立完成！"
```

### Step 3: 遷移核心模組
```python
# scripts/migrate-core-modules.py
import shutil
import os
from pathlib import Path

def migrate_manus_core():
    """遷移 OpenManus 核心模組"""

    # 遷移 Agent 相關
    shutil.move("OpenManus/app/agent/", "manus_core/agents/")

    # 遷移工具層
    shutil.move("OpenManus/app/tool/", "manus_core/tools/")

    # 遷移記憶管理
    if os.path.exists("app/memory_optimizer.py"):
        shutil.move("app/memory_optimizer.py", "manus_core/memory/optimizer.py")

    # 遷移 LLM 層
    shutil.move("OpenManus/app/llm.py", "manus_core/llm/")

    print("✅ 核心模組遷移完成")

def migrate_web_app():
    """遷移 Web 應用到後端 API"""

    # 建立後端主檔案
    backend_main = """
from fastapi import FastAPI
from app.api.v1 import router as v1_router
from app.api.v2 import router as v2_router

app = FastAPI(title="OpenManus API", version="2.0.0")

# API 路由
app.include_router(v1_router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    """

    with open("backend/app/main.py", "w") as f:
        f.write(backend_main)

    print("✅ Web 應用結構建立完成")

if __name__ == "__main__":
    migrate_manus_core()
    migrate_web_app()
```

---

## 🐳 Docker 環境設置

### docker-compose.yml
```yaml
version: '3.8'

services:
  # 前端開發服務
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - CHOKIDAR_USEPOLLING=true
    depends_on:
      - backend

  # 後端 API 服務
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./manus_core:/app/manus_core
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/openmanus
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  # PostgreSQL 資料庫
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=openmanus
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql

  # Redis 快取
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # pgAdmin (資料庫管理)
  pgadmin:
    image: dpage/pgadmin4
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@openmanus.dev
      - PGADMIN_DEFAULT_PASSWORD=admin
    ports:
      - "5050:80"
    depends_on:
      - postgres

volumes:
  postgres_data:
  redis_data:
```

### 前端 Dockerfile.dev
```dockerfile
# frontend/Dockerfile.dev
FROM node:18-alpine

WORKDIR /app

# 安裝依賴
COPY package*.json ./
RUN npm ci

# 複製源碼
COPY . .

# 開發模式啟動
CMD ["npm", "run", "dev"]
```

### 後端 Dockerfile.dev
```dockerfile
# backend/Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製源碼
COPY . .

# 開發模式啟動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

## 🗄️ 資料庫設計

### schema.sql
```sql
-- 建立擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 列舉類型
CREATE TYPE session_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'stopped');
CREATE TYPE task_type AS ENUM ('simple_query', 'web_search', 'code_generation', 'analysis', 'general');
CREATE TYPE execution_status AS ENUM ('success', 'error', 'timeout', 'cancelled');

-- 用戶表 (未來擴展)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 會話表
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    status session_status NOT NULL DEFAULT 'pending',
    task_type task_type NOT NULL DEFAULT 'general',
    prompt TEXT NOT NULL,
    result TEXT,
    workspace_path VARCHAR(255),
    token_budget INTEGER DEFAULT 4000,
    token_used INTEGER DEFAULT 0,
    optimization_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Agent 執行記錄
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL,
    step_number INTEGER NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    execution_time_ms INTEGER,
    status execution_status NOT NULL,
    error_message TEXT,
    thinking_step TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 工具調用記錄
CREATE TABLE tool_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID NOT NULL REFERENCES agent_executions(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    tool_input JSONB,
    tool_output TEXT,
    execution_time_ms INTEGER,
    status execution_status NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 熔斷器狀態
CREATE TABLE circuit_breaker_states (
    tool_name VARCHAR(100) PRIMARY KEY,
    state VARCHAR(20) NOT NULL DEFAULT 'closed', -- closed, open, half_open
    failure_count INTEGER DEFAULT 0,
    last_failure_time TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 系統指標
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL,
    labels JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_created_at ON sessions(created_at);
CREATE INDEX idx_agent_executions_session_id ON agent_executions(session_id);
CREATE INDEX idx_tool_calls_execution_id ON tool_calls(execution_id);
CREATE INDEX idx_system_metrics_name_time ON system_metrics(metric_name, recorded_at);

-- 觸發器：更新時間戳
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_circuit_breaker_updated_at
    BEFORE UPDATE ON circuit_breaker_states
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 資料庫遷移腳本
```python
# scripts/migrate_database.py
import asyncio
import asyncpg
import json
from pathlib import Path

async def migrate_legacy_data():
    """從舊系統遷移資料到新資料庫"""

    # 連接資料庫
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/openmanus")

    try:
        # 創建預設用戶
        user_id = await conn.fetchval("""
            INSERT INTO users (username, email)
            VALUES ('system', 'system@openmanus.dev')
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        """)

        if not user_id:
            user_id = await conn.fetchval(
                "SELECT id FROM users WHERE email = 'system@openmanus.dev'"
            )

        # 遷移會話資料 (如果有的話)
        # 這裡可以讀取舊的 active_sessions 資料並轉換

        print("✅ 資料庫遷移完成")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate_legacy_data())
```

---

## 🔧 開發工具配置

### 前端工具配置

#### package.json
```json
{
  "name": "openmanus-frontend",
  "version": "2.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tanstack/react-query": "^4.36.1",
    "zustand": "^4.4.4",
    "socket.io-client": "^4.7.4",
    "@radix-ui/react-progress": "^1.0.3",
    "lucide-react": "^0.291.0",
    "tailwindcss": "^3.3.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0",
    "@vitejs/plugin-react": "^4.2.1",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "typescript": "^5.2.2",
    "vite": "^5.0.8"
  }
}
```

#### tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/hooks/*": ["./src/hooks/*"],
      "@/services/*": ["./src/services/*"],
      "@/stores/*": ["./src/stores/*"],
      "@/types/*": ["./src/types/*"],
      "@/utils/*": ["./src/utils/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 後端工具配置

#### requirements.txt
```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
asyncpg==0.29.0
sqlalchemy[asyncio]==2.0.23
alembic==1.13.1

# Cache
redis==5.0.1
aioredis==2.0.1

# WebSocket
python-socketio==5.10.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2

# Development
black==23.11.0
isort==5.12.0
mypy==1.7.1

# Monitoring
prometheus-client==0.19.0
```

#### pyproject.toml
```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
asyncio_mode = "auto"
```

---

## 🚀 CI/CD 設置

### .github/workflows/ci.yml
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-backend:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: password
          POSTGRES_DB: test_openmanus
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt

    - name: Run tests
      run: |
        cd backend
        pytest
      env:
        DATABASE_URL: postgresql://postgres:password@localhost:5432/test_openmanus

  test-frontend:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Install dependencies
      run: |
        cd frontend
        npm ci

    - name: Run type check
      run: |
        cd frontend
        npm run type-check

    - name: Run linting
      run: |
        cd frontend
        npm run lint

    - name: Run tests
      run: |
        cd frontend
        npm test

  build-and-deploy:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Build and push Docker images
      run: |
        docker build -t openmanus/backend:latest ./backend
        docker build -t openmanus/frontend:latest ./frontend

        # Push to registry (configure as needed)
        # docker push openmanus/backend:latest
        # docker push openmanus/frontend:latest
```

---

## ✅ Phase 1 檢查清單

### 🏗️ 基礎設施
- [ ] 新目錄結構建立
- [ ] Docker 開發環境配置
- [ ] PostgreSQL 資料庫設置
- [ ] Redis 快取配置
- [ ] 環境變數管理

### 🛠️ 開發工具
- [ ] 前端工具鏈 (Vite + TypeScript)
- [ ] 後端工具鏈 (FastAPI + SQLAlchemy)
- [ ] 程式碼格式化工具
- [ ] 型別檢查設置
- [ ] Git Hooks 配置

### 🔄 CI/CD
- [ ] GitHub Actions 設置
- [ ] 自動化測試
- [ ] 程式碼品質檢查
- [ ] Docker 映像建構
- [ ] 部署流程配置

### 📊 監控基礎
- [ ] 日誌結構化
- [ ] 效能指標收集
- [ ] 健康檢查端點
- [ ] 錯誤追蹤設置

---

## 📝 下一步

Phase 1 完成後，進入 [Phase 2: 後端重構](./phase2-backend-refactor.md)

**預期完成時間**: 7 天
**關鍵里程碑**: Docker 環境可正常啟動，基礎 API 可訪問