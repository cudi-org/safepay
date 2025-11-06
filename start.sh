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
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo -e "${RED}❌ Python not found! Please install Python 3.10+${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo -e "${RED}❌ Failed to find activation script${NC}"
    exit 1
fi

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -q --upgrade pip

# Install core dependencies
echo "  • fastapi, uvicorn, pydantic..."
pip install -q fastapi uvicorn pydantic httpx

# Install AI dependencies
echo "  • anthropic (Claude AI)..."
pip install -q anthropic

# Install optional dependencies
echo "  • python-dotenv, requests..."
pip install -q python-dotenv requests

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > .env << 'EOF'
# Bulut Backend Configuration
APP_ENV=development
DEBUG=true
HOST=0.0.0.0
PORT=8000

# ============================================================================
# ANTHROPIC - Add your API key here
# ============================================================================
# Get your key from: https://console.anthropic.com/
# Use code: ARCHACK20 for credits
ANTHROPIC_API_KEY=

# API URL (don't change unless using proxy)
ANTHROPIC_API_URL=https://api.anthropic.com/v1

# ============================================================================
# ARC BLOCKCHAIN
# ============================================================================
ARC_RPC_URL=https://mainnet.arc.network
ARC_EXPLORER_URL=https://explorer.arc.network
ARC_CONTRACT_ADDRESS=0xBulutContract123
ARC_CHAIN_ID=4224

# ============================================================================
# ELEVENLABS (VOICE) - Optional
# ============================================================================
ELEVENLABS_API_KEY=
ELEVENLABS_API_URL=https://api.elevenlabs.io/v1

# ============================================================================
# SECURITY
# ============================================================================
JWT_SECRET=dev-secret-change-in-production
ALLOWED_ORIGINS=*

# ============================================================================
# FEATURES
# ============================================================================
ENABLE_VOICE=false
ENABLE_AI_AGENT=true
RATE_LIMIT_ENABLED=false
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}📝 Note: Add your ANTHROPIC_API_KEY to .env for AI features${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Check if agent.py exists
if [ ! -f "agent.py" ]; then
    echo -e "${RED}⚠️  Warning: agent.py not found${NC}"
    echo -e "${YELLOW}   The API will use mock AI parser instead of Claude${NC}"
fi

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: main.py not found${NC}"
    echo -e "${YELLOW}   Make sure you're in the correct directory${NC}"
    exit 1
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
echo "  @alice   → 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
echo "  @bob     → 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199"
echo "  @charlie → 0xdD870fA1b7C4700F2BD7f44238821C26f7392148"
echo "  @demo    → 0x4E5B2ea1F6E7eA1e5e5E5e5e5e5e5e5e5e5e5e5"
echo ""
echo "Try these commands in another terminal:"
echo ""
echo "  # Health check"
echo "  curl http://localhost:8000/health"
echo ""
echo "  # Get alias"
echo "  curl http://localhost:8000/alias/@alice"
echo ""
echo "  # Process payment command"
echo "  curl -X POST http://localhost:8000/process_command \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"text\": \"Send \$50 to @alice\"}'"
echo ""
echo "  # Or run interactive tests"
echo "  python3 test_client.py"
echo ""
echo "=========================================="
echo ""
echo -e "${YELLOW}💡 Tip: Set ANTHROPIC_API_KEY in .env for real AI features${NC}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
$PYTHON_CMD main.py