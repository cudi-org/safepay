#!/bin/bash

# Bulut Backend - Quick Start Script
# Makes the backend fully functional with one command

set -e

echo "🌥️  Bulut Backend - Quick Start"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
python3 --version || { echo "Python 3 not found!"; exit 1; }

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q fastapi uvicorn pydantic httpx

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > .env << EOF
# Bulut Backend Configuration
APP_ENV=development
DEBUG=true

# External Services (Optional - using mocks)
AI_AGENT_URL=http://localhost:8001
ARC_RPC_URL=https://mainnet.arc.network
ARC_CONTRACT_ADDRESS=0xBulutContract123

# Security
JWT_SECRET=dev-secret-change-in-production
ALLOWED_ORIGINS=*
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
fi

# Start the server
echo ""
echo -e "${GREEN}🚀 Starting Bulut Backend...${NC}"
echo ""
echo "=========================================="
echo "📍 API Server: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo "=========================================="
echo ""
echo "Demo Aliases Available:"
echo "  @alice → 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
echo "  @bob → 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199"
echo "  @charlie → 0xdD870fA1b7C4700F2BD7f44238821C26f7392148"
echo "  @demo → 0x4E5B2ea1F6E7eA1e5e5E5e5e5e5e5e5e5e5e5e5"
echo ""
echo "Try these commands in another terminal:"
echo ""
echo "  # Get alias"
echo "  curl http://localhost:8000/alias/@alice"
echo ""
echo "  # Process payment command"
echo "  curl -X POST http://localhost:8000/process_command \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"text\": \"Send \$50 to @alice\"}'"
echo ""
echo "=========================================="
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
python3 main.py