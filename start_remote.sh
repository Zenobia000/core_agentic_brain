#!/bin/bash

# Script specifically for running on remote servers

echo "🚀 Starting Manus System for Remote Access..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')
echo -e "${BLUE}Server IP: ${SERVER_IP}${NC}"

# Function to kill process on port
kill_port() {
    local port=$1
    echo "Killing processes on port $port..."
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"

    # Kill processes
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi

    # Kill any remaining processes on ports
    kill_port 8000
    kill_port 5173

    echo -e "${GREEN}Services stopped${NC}"
    exit 0
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Clear ports
kill_port 8000
kill_port 5173

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 is required but not installed${NC}"
    exit 1
fi

# Check for Node
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is required but not installed${NC}"
    exit 1
fi

# ============= BACKEND SETUP =============
echo -e "\n${GREEN}Setting up Backend...${NC}"
cd OpenManus

# Create virtual environment if needed
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate and install dependencies
source .venv/bin/activate

# Check for required packages
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing backend dependencies..."
    pip install fastapi uvicorn websockets python-dotenv pydantic
fi

# Update CORS in web_server.py to allow remote access
echo "Configuring backend for remote access..."

# Start backend with host 0.0.0.0
echo -e "${YELLOW}Starting backend on 0.0.0.0:8000...${NC}"
nohup python -c "
import uvicorn
from web_server import app

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000, reload=False)
" > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend
echo "Waiting for backend..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/status > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend started${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Backend failed to start${NC}"
        cat backend.log
        exit 1
    fi
    sleep 1
done

# ============= FRONTEND SETUP =============
echo -e "\n${GREEN}Setting up Frontend...${NC}"
cd ../Hacker_UI_Design

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Configure for remote access
echo "VITE_API_URL=http://${SERVER_IP}:8000" > .env
echo -e "${BLUE}Frontend configured to use API at: http://${SERVER_IP}:8000${NC}"

# Start frontend with host 0.0.0.0
echo -e "${YELLOW}Starting frontend on 0.0.0.0:5173...${NC}"
nohup npm run dev -- --host 0.0.0.0 --port 5173 > ../OpenManus/frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend
echo "Waiting for frontend..."
for i in {1..30}; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend started${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Frontend failed to start${NC}"
        cat ../OpenManus/frontend.log
        exit 1
    fi
    sleep 1
done

# ============= SUCCESS MESSAGE =============
echo -e "\n${GREEN}✨ System Successfully Started for Remote Access!${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${BLUE}Access from browser:${NC}"
echo -e "  Frontend: ${GREEN}http://${SERVER_IP}:5173${NC}"
echo -e "  Backend:  ${GREEN}http://${SERVER_IP}:8000${NC}"
echo -e "  API Docs: ${GREEN}http://${SERVER_IP}:8000/docs${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "\n${YELLOW}Firewall Configuration:${NC}"
echo -e "Make sure these ports are open in your firewall:"
echo -e "  sudo ufw allow 5173/tcp"
echo -e "  sudo ufw allow 8000/tcp"
echo -e ""
echo -e "Or for iptables:"
echo -e "  sudo iptables -A INPUT -p tcp --dport 5173 -j ACCEPT"
echo -e "  sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT"
echo -e ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Backend:  tail -f OpenManus/backend.log"
echo -e "  Frontend: tail -f OpenManus/frontend.log"
echo -e ""
echo -e "Press ${YELLOW}Ctrl+C${NC} to stop all services"

# Keep script running and tail logs
tail -f OpenManus/backend.log OpenManus/frontend.log