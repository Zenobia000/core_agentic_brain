#!/bin/bash

# Diagnostic script for remote access issues

echo "🔍 Checking Remote Access Configuration..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get server info
SERVER_IP=$(hostname -I | awk '{print $1}')
echo -e "${BLUE}Server IP: ${SERVER_IP}${NC}"
echo ""

# Check if services are running
echo "📋 Checking Services:"

# Check backend
if lsof -i:8000 > /dev/null 2>&1; then
    echo -e "  Backend:  ${GREEN}✓ Running on port 8000${NC}"
else
    echo -e "  Backend:  ${RED}✗ Not running${NC}"
fi

# Check frontend
if lsof -i:5173 > /dev/null 2>&1; then
    echo -e "  Frontend: ${GREEN}✓ Running on port 5173${NC}"
else
    echo -e "  Frontend: ${RED}✗ Not running${NC}"
fi

echo ""
echo "🔥 Checking Firewall:"

# Check ufw status
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(sudo ufw status 2>/dev/null | grep -E "5173|8000" | head -2)
    if [ ! -z "$UFW_STATUS" ]; then
        echo -e "  UFW: ${GREEN}Ports seem to be configured${NC}"
        echo "$UFW_STATUS"
    else
        echo -e "  UFW: ${YELLOW}Ports may need to be opened${NC}"
        echo "  Run: sudo ufw allow 5173/tcp"
        echo "       sudo ufw allow 8000/tcp"
    fi
else
    echo "  UFW: Not installed"
fi

# Check iptables
if command -v iptables &> /dev/null; then
    IPTABLES_5173=$(sudo iptables -L -n 2>/dev/null | grep 5173)
    IPTABLES_8000=$(sudo iptables -L -n 2>/dev/null | grep 8000)

    if [ ! -z "$IPTABLES_5173" ] || [ ! -z "$IPTABLES_8000" ]; then
        echo -e "  iptables: ${GREEN}Some rules found${NC}"
    else
        echo -e "  iptables: ${YELLOW}May need configuration${NC}"
    fi
fi

echo ""
echo "🌐 Testing Connectivity:"

# Test local connectivity
echo -n "  Local Backend (8000):  "
if curl -s http://localhost:8000/api/status > /dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
fi

echo -n "  Local Frontend (5173): "
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
fi

# Test remote connectivity
echo -n "  Remote Backend:  "
if curl -s http://${SERVER_IP}:8000/api/status > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Accessible${NC}"
else
    echo -e "${RED}✗ Not accessible from this machine${NC}"
fi

echo -n "  Remote Frontend: "
if curl -s http://${SERVER_IP}:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Accessible${NC}"
else
    echo -e "${RED}✗ Not accessible from this machine${NC}"
fi

echo ""
echo "📁 Checking Configuration:"

# Check Vite config
if [ -f "Hacker_UI_Design/vite.config.ts" ]; then
    HOST_CONFIG=$(grep "host:" Hacker_UI_Design/vite.config.ts | grep "0.0.0.0")
    if [ ! -z "$HOST_CONFIG" ]; then
        echo -e "  Vite host: ${GREEN}✓ Configured for 0.0.0.0${NC}"
    else
        echo -e "  Vite host: ${RED}✗ Not configured for external access${NC}"
    fi
fi

# Check .env
if [ -f "Hacker_UI_Design/.env" ]; then
    API_URL=$(grep "VITE_API_URL" Hacker_UI_Design/.env)
    echo -e "  Frontend .env: ${BLUE}${API_URL}${NC}"
fi

echo ""
echo "💡 Troubleshooting Tips:"
echo ""
echo "1. If services are not running, start them with:"
echo "   ./start_remote.sh"
echo ""
echo "2. If firewall is blocking, open ports:"
echo "   sudo ufw allow 5173/tcp"
echo "   sudo ufw allow 8000/tcp"
echo "   sudo ufw reload"
echo ""
echo "3. Check if ports are listening on all interfaces:"
echo "   netstat -tlnp | grep -E '5173|8000'"
echo ""
echo "4. Test from another machine:"
echo "   curl http://${SERVER_IP}:5173"
echo "   curl http://${SERVER_IP}:8000/api/status"
echo ""
echo "5. Check logs:"
echo "   tail -f OpenManus/backend.log"
echo "   tail -f OpenManus/frontend.log"

# Show netstat info
echo ""
echo "📊 Current Port Bindings:"
netstat -tlnp 2>/dev/null | grep -E '5173|8000' || ss -tlnp | grep -E '5173|8000'