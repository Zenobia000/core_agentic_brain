#!/bin/bash

# Script to run both OpenManus backend and Hacker UI frontend

echo "🚀 Starting Manus Integrated System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to kill process on port
kill_port() {
    local port=$1
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

# Check prerequisites
echo "Checking prerequisites..."

if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}Error: npm is not installed${NC}"
    exit 1
fi

# Kill any existing processes on required ports
echo "Clearing ports..."
kill_port 8000
kill_port 5173

# Start Backend
echo -e "\n${GREEN}Starting OpenManus Backend...${NC}"
cd OpenManus

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment and install dependencies
source .venv/bin/activate

# Install backend dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing backend dependencies..."
    pip install fastapi uvicorn websockets pydantic python-dotenv
fi

# Start backend server in background
echo "Starting backend server on port 8000..."
python web_server.py > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/status > /dev/null 2>&1; then
        echo -e "${GREEN}Backend started successfully${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Backend failed to start. Check backend.log for details${NC}"
        exit 1
    fi
    sleep 1
done

# Start Frontend
echo -e "\n${GREEN}Starting Hacker UI Frontend...${NC}"
cd ../Hacker_UI_Design

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Detect if running on remote server
if [[ -n "${SSH_CONNECTION}" ]] || [[ -n "${SSH_CLIENT}" ]]; then
    # Get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    echo -e "${YELLOW}Detected remote server. Using IP: ${SERVER_IP}${NC}"
    echo "VITE_API_URL=http://${SERVER_IP}:8000" > .env
else
    # Local development
    echo "VITE_API_URL=http://localhost:8000" > .env
fi

# Start frontend server in background with host binding
echo "Starting frontend server on port 5173..."
npm run dev -- --host 0.0.0.0 > ../OpenManus/frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
echo "Waiting for frontend to start..."
for i in {1..30}; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}Frontend started successfully${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Frontend failed to start. Check frontend.log for details${NC}"
        exit 1
    fi
    sleep 1
done

# Display success message
echo -e "\n${GREEN}✨ Manus Integrated System is running!${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Show appropriate URLs based on environment
if [[ -n "${SSH_CONNECTION}" ]] || [[ -n "${SSH_CLIENT}" ]]; then
    SERVER_IP=$(hostname -I | awk '{print $1}')
    echo -e "  Frontend: ${GREEN}http://${SERVER_IP}:5173${NC}"
    echo -e "  Backend:  ${GREEN}http://${SERVER_IP}:8000${NC}"
    echo -e "  API Docs: ${GREEN}http://${SERVER_IP}:8000/docs${NC}"
else
    echo -e "  Frontend: ${GREEN}http://localhost:5173${NC}"
    echo -e "  Backend:  ${GREEN}http://localhost:8000${NC}"
    echo -e "  API Docs: ${GREEN}http://localhost:8000/docs${NC}"
fi

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "\nPress ${YELLOW}Ctrl+C${NC} to stop all services"
echo -e "\nLogs:"
echo -e "  Backend:  ${YELLOW}OpenManus/backend.log${NC}"
echo -e "  Frontend: ${YELLOW}OpenManus/frontend.log${NC}"

# Keep script running and show logs
tail -f OpenManus/backend.log OpenManus/frontend.log