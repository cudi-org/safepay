@echo off
REM Bulut Backend - Windows Quick Start Script

echo.
echo ============================================
echo    Bulut Backend - Quick Start (Windows)
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

echo [INFO] Python found
echo.

REM Create virtual environment
if not exist venv (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo [INFO] Installing dependencies...
pip install -q --upgrade pip
pip install -q fastapi uvicorn pydantic httpx requests

echo.
echo [SUCCESS] Dependencies installed
echo.

REM Create .env if it doesn't exist
if not exist .env (
    echo [INFO] Creating .env file...
    (
        echo # Bulut Backend Configuration
        echo APP_ENV=development
        echo DEBUG=true
        echo.
        echo # External Services
        echo AI_AGENT_URL=http://localhost:8001
        echo ARC_RPC_URL=https://mainnet.arc.network
        echo ARC_CONTRACT_ADDRESS=0xBulutContract123
        echo.
        echo # Security
        echo JWT_SECRET=dev-secret-change-in-production
        echo ALLOWED_ORIGINS=*
    ) > .env
    echo [SUCCESS] .env file created
)

REM Start the server
echo.
echo ============================================
echo    Starting Bulut Backend...
echo ============================================
echo.
echo [INFO] API Server: http://localhost:8000
echo [INFO] API Docs: http://localhost:8000/docs
echo [INFO] Health Check: http://localhost:8000/health
echo.
echo ============================================
echo Demo Aliases Available:
echo   @alice   -^> 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
echo   @bob     -^> 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199
echo   @charlie -^> 0xdD870fA1b7C4700F2BD7f44238821C26f7392148
echo   @demo    -^> 0x4E5B2ea1F6E7eA1e5e5E5e5e5e5e5e5e5e5e5e5
echo ============================================
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the server
python main.py

pause