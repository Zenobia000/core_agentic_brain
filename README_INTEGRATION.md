# Manus Hacker UI Integration Guide

## Overview

This guide explains how to run the integrated system combining:
- **Hacker UI Design**: Matrix-style web frontend with terminal aesthetics
- **OpenManus**: Core agentic brain backend with LLM capabilities

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Hacker UI Frontend                     │
│                    (React + Vite)                        │
│                   Port: 5173                             │
├─────────────────────────────────────────────────────────┤
│                  WebSocket & REST API                    │
│                        ↑↓                                │
├─────────────────────────────────────────────────────────┤
│                  OpenManus Backend                       │
│                 (FastAPI + Manus Agent)                  │
│                   Port: 8000                             │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Method 1: Using the Integrated Script (Recommended)

```bash
# Run the integrated system
./run_integrated.sh
```

This will:
1. Start the OpenManus backend on port 8000
2. Start the Hacker UI frontend on port 5173
3. Open your browser to http://localhost:5173

### Method 2: Using Docker Compose

```bash
# Build and run with Docker
docker-compose up --build

# Run in background
docker-compose up -d

# Stop services
docker-compose down
```

### Method 3: Manual Startup SOP (Standard Operating Procedure)

This is the recommended method for development and debugging. It involves running the backend and frontend in separate terminals.

#### **Prerequisites**

Before you begin, ensure you have the following installed:

*   **Python**: Version 3.10 or higher.
*   **Node.js**: Version 18 or higher.
*   **npm**: Should be included with Node.js.

#### **Step 1: Configure Environment Variables**

You need to set up API keys and other configurations for the backend to work correctly.

1.  **Navigate to the `OpenManus` directory:**
    ```bash
    cd OpenManus
    ```

2.  **Create a configuration file:**
    Copy the example configuration file to create your own.
    ```bash
    cp config/config.example.toml config/config.toml
    ```

3.  **Edit the configuration file:**
    Open `config/config.toml` in a text editor and add your API keys (e.g., `OPENAI_API_KEY`).

#### **Step 2: Start the Backend Server**

1.  **Open a new terminal.** This will be your **backend terminal**.

2.  **Navigate to the `OpenManus` directory:**
    ```bash
    cd /path/to/your/project/core_agentic_brain/OpenManus
    ```

3.  **Install Python dependencies:**
    It's recommended to use a virtual environment.
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

4.  **Start the web server:**
    ```bash
    python web_server.py
    ```

    You should see output indicating the server is running on `http://0.0.0.0:8000`. Keep this terminal open.

#### **Step 3: Start the Frontend Application**

1.  **Open a second, new terminal.** This will be your **frontend terminal**.

2.  **Navigate to the `Hacker_UI_Design` directory:**
    ```bash
    cd /path/to/your/project/core_agentic_brain/Hacker_UI_Design
    ```

3.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

4.  **Start the development server:**
    ```bash
    npm run dev
    ```

    You should see output indicating the frontend is running, usually on `http://localhost:5173`.

#### **Step 4: Access the Application**

1.  Open your web browser and navigate to the frontend URL, which is typically:
    **http://localhost:5173**

You should now see the Hacker UI, connected to your local backend.

#### **Step 5: Stopping the Services**

To stop the application, you need to stop both the frontend and backend servers.

1.  **In the frontend terminal**, press `Ctrl + C`.
2.  **In the backend terminal**, press `Ctrl + C`.

## Configuration

### Backend Configuration (.env)

Create `/OpenManus/.env`:

```env
# LLM Configuration
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key

# Search APIs
TAVILY_API_KEY=your-key
GOOGLE_API_KEY=your-key

# Workspace
WORKSPACE_DIR=./workspace
LOG_LEVEL=INFO
```

### Frontend Configuration

Create `/Hacker_UI_Design/.env`:

```env
VITE_API_URL=http://localhost:8000
```

## API Endpoints

### REST API

- `GET /api/status` - System status
- `GET /api/settings` - User settings
- `POST /api/chat` - Send chat message (SSE streaming)
- `GET /api/sessions` - List active sessions
- `DELETE /api/sessions/{id}` - Delete session

### WebSocket

- `ws://localhost:8000/ws` - Real-time bidirectional communication

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Features

### Frontend Features

- **Matrix Rain Background** - Animated digital rain effect
- **Terminal UI** - Command-line interface in browser
- **Real-time Updates** - WebSocket for instant feedback
- **Collapsible Panels** - Thinking process and tools panels
- **Command Palette** - Ctrl+P for quick commands
- **Export** - Save conversations as Markdown or JSON

### Backend Features

- **Manus Agent** - Core AI agent with tool capabilities
- **Session Management** - Multi-session support
- **Context Management** - Workspace isolation per session
- **Tool Integration** - File operations, search, code execution
- **Streaming Response** - Real-time token streaming

## Commands

Available commands in the UI:

- `/help` - Show available commands
- `/clear` - Clear conversation
- `/mode [minimal|standard|hacker]` - Change UI mode
- `/theme [matrix|minimal]` - Change theme
- `/export [md|json]` - Export conversation
- `/status` - Show system status

## Keyboard Shortcuts

- `Ctrl+P` - Open command palette
- `Ctrl+K` - Switch pane focus
- `Ctrl+J` - Toggle current section
- `Ctrl+G` - Go to last error
- `Ctrl+L` - Clear screen
- `Ctrl+/` - Toggle sidebar
- `Escape` - Cancel/Close

## Development

### Frontend Development

```bash
cd Hacker_UI_Design

# Run tests
npm test

# Build for production
npm run build

# Preview production build
npm run preview
```

### Backend Development

```bash
cd OpenManus

# Run tests
pytest

# Format code
black app/

# Type checking
mypy app/
```

## Troubleshooting

### Backend Issues

1. **Port 8000 already in use**
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

2. **Module import errors**
   ```bash
   pip install -r requirements.txt
   pip install fastapi uvicorn websockets
   ```

3. **Check backend logs**
   ```bash
   tail -f OpenManus/backend.log
   ```

### Frontend Issues

1. **Port 5173 already in use**
   ```bash
   lsof -ti:5173 | xargs kill -9
   ```

2. **Node modules issues**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Check frontend logs**
   ```bash
   tail -f OpenManus/frontend.log
   ```

### Connection Issues

1. **WebSocket connection failed**
   - Check if backend is running: `curl http://localhost:8000/api/status`
   - Check CORS settings in web_server.py
   - Verify VITE_API_URL in frontend .env

2. **API calls failing**
   - Check network tab in browser DevTools
   - Verify backend is accessible
   - Check for CORS errors

## Production Deployment

### Using Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Using PM2

```bash
# Install PM2
npm install -g pm2

# Start backend
pm2 start OpenManus/web_server.py --interpreter python3 --name manus-backend

# Start frontend
pm2 start npm --name manus-frontend -- run dev --prefix Hacker_UI_Design

# Save PM2 config
pm2 save
pm2 startup
```

## Security Considerations

1. **API Keys**: Store all sensitive keys in .env files
2. **CORS**: Configure allowed origins in production
3. **HTTPS**: Use SSL/TLS certificates in production
4. **Authentication**: Implement user authentication for production
5. **Rate Limiting**: Add rate limiting to prevent abuse

## Support

- GitHub Issues: Report bugs and feature requests
- Documentation: Check /docs folder for detailed guides
- API Docs: http://localhost:8000/docs

## License

See LICENSE file in the project root.