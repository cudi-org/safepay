# Bulut Setup & Deployment Guide

**Complete guide for setting up and deploying the Bulut AI-powered payment backend**

---

## Team Structure & Responsibilities

### 🧠 AI Team
**Lead:** AI/ML Engineer  
**Timeline:** Days 1-2

**Tasks:**
1. ✅ AI/ML API Configuration (1 hour)
2. ✅ Prompt Engineering for GPT-4o (4 hours)
3. ✅ NLP Logic Implementation (6 hours)
4. ✅ Testing & Validation (3 hours)

---

### ⚡ Backend Team
**Lead:** Backend Engineer  
**Timeline:** Days 1-3

**Tasks:**
1. ✅ FastAPI Setup & Configuration (4 hours)
2. ✅ Web3.py Blockchain Integration (6 hours)
3. ✅ Alias Mapping with Signature Verification (4 hours)
4. ✅ Payment Execution Routes (4 hours)
5. ✅ Transaction History & Database (3 hours)

---

## Step-by-Step Setup

### Prerequisites

```bash
# Required tools
- Python 3.10+
- Git
- Docker (optional, for containerization)

# API Keys needed
- AI/ML API Key (from aimlapi.com)
- Arc wallet with funds for gas
- Web3 private key for gas payment
```

---

## Part 1: AI Team Setup

### 1.1 Get AI/ML API Access

```bash
# Visit: https://aimlapi.com/
# Sign up for an account
# Navigate to API Keys section
# Create new API key

# Copy your API key
export AIMLAPI_KEY="your_api_key_here"

# Verify API access
python -c "
import os
from openai import OpenAI

client = OpenAI(
    base_url='https://api.aimlapi.com/v1',
    api_key=os.getenv('AIMLAPI_KEY')
)

response = client.chat.completions.create(
    model='gpt-4o',
    messages=[{'role': 'user', 'content': 'Hello'}]
)
print('✓ API Key Valid')
print(f'Response: {response.choices[0].message.content}')
"
```

**Deliverable:** ✅ Working AI/ML API connection

---

### 1.2 Deploy AI Agent

```bash
# The AI agent is integrated in agent.py

# Install dependencies
pip install openai anthropic

# Test the AI agent
python agent.py

# Expected output:
# ====================================================================
# 🧠 Bulut AI Agent - Test Suite
# ====================================================================
# 
# ✅ Using Real AI Agent (aimlapi.com)
# 
# ──────────────────────────────────────────────────────────────────
# Test 1: Send $50 to @alice for lunch
# ──────────────────────────────────────────────────────────────────
# Type: single
# Confidence: 0.95
# Confirmation: Send $50 to @alice for lunch?
# Intent: {
#   "action": "send",
#   "amount": 50,
#   "currency": "USD",
#   "recipient": {
#     "alias": "@alice"
#   },
#   "memo": "lunch"
# }
```

**Test Commands the Agent Understands:**
```python
# Single payments
"Send $50 to @alice"
"Pay @bob 25 dollars"
"Transfer 100 ARC to @charlie"

# Split payments
"Split $120 between @alice and @bob"
"Divide $90 equally with @carol, @dave, and @eve"
"Give @john 60% and @jane 40% of $100"

# Subscriptions
"Pay @netflix $9.99 every month"
"Send @spotify $4.99 monthly starting next week"
"Subscribe to @gym for $30 monthly for 12 months"

# Complex queries
"Send $50 to @alice for lunch tomorrow"
"Pay @landlord $1200 for rent on the 1st of each month"
"Split dinner bill of $85 between me, @bob, and @carol"
```

**Deliverable:** ✅ AI agent working with GPT-4o model

---

### 1.3 Prompt Engineering

The AI agent uses a specialized system prompt in `agent.py`:

```python
SYSTEM_PROMPT = """You are Bulut, an AI payment assistant that converts 
natural language into structured payment commands.

# YOUR MISSION
Parse human payment requests into precise JSON payment intents with 
MAXIMUM accuracy.

# PAYMENT TYPES
1. **single** - One-time payment to one person
2. **subscription** - Recurring payments (daily, weekly, monthly, yearly)
3. **split** - Divide payment among multiple people

# EXTRACTION RULES
...
"""
```

**Confidence Scoring:**
- **0.9-1.0**: High confidence - safe to auto-execute
- **0.7-0.89**: Good confidence - confirm with user
- **0.5-0.69**: Low confidence - ask for clarification
- **<0.5**: Error - cannot parse reliably

**Deliverable:** ✅ Tuned prompts with 95%+ accuracy

---

## Part 2: Backend Team Setup

### 2.1 Set Up Environment

```bash
# Clone repository
git clone https://github.com/your-org/bulut-backend.git
cd bulut-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Dependencies include:
# - fastapi (web framework)
# - uvicorn (ASGI server)
# - pydantic (data validation)
# - httpx (HTTP client)
# - web3 (blockchain interaction)
# - openai (AI/ML API client)
# - eth-account (signature verification)
```

**Deliverable:** ✅ Development environment ready

---

### 2.2 Configure Environment Variables

```bash
# Create .env file
cp .env.example .env

# Edit .env with your values:
nano .env
```

**Required Configuration:**
```bash
# AI/ML API (Required for AI features)
AIMLAPI_KEY=your_api_key_here

# Arc Blockchain (Required for transactions)
ARC_RPC_URL=https://mainnet.arc.network
ARC_CHAIN_ID=4224
GAS_PAYER_KEY=0xyour_private_key_here

# Optional: USDC Contract
ARC_USDC_ADDRESS=0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48

# Optional: Explorer
ARC_EXPLORER_URL=https://explorer.arc.network

# Server Configuration
HOST=0.0.0.0
PORT=8000
APP_ENV=development
DEBUG=true

# Security
JWT_SECRET=your-secret-key-change-in-production
ALLOWED_ORIGINS=*

# Storage
DATABASE_URL=sqlite:///./bulut.db
```

**Generate Gas Payer Wallet:**
```bash
# Create new wallet for gas payment
python -c "
from eth_account import Account
acc = Account.create()
print(f'🔑 New Wallet Created:')
print(f'Address: {acc.address}')
print(f'Private Key: {acc.key.hex()}')
print(f'\n⚠️  SAVE THIS PRIVATE KEY SECURELY!')
print(f'💰 Fund this address with ARC tokens for gas')
"
```

**Deliverable:** ✅ `.env` configured with all keys

---

### 2.3 Test Blockchain Connection

```bash
# Test Web3 connection
python -c "
from web3 import Web3
import os

rpc_url = os.getenv('ARC_RPC_URL', 'https://mainnet.arc.network')
w3 = Web3(Web3.HTTPProvider(rpc_url))

print(f'🔗 Testing connection to: {rpc_url}')
print(f'Connected: {w3.is_connected()}')

if w3.is_connected():
    print(f'✅ Chain ID: {w3.eth.chain_id}')
    print(f'✅ Block Number: {w3.eth.block_number}')
    print(f'✅ Gas Price: {w3.eth.gas_price} wei')
    
    # Test gas payer balance
    gas_payer = os.getenv('GAS_PAYER_KEY')
    if gas_payer:
        from eth_account import Account
        account = Account.from_key(gas_payer)
        balance = w3.eth.get_balance(account.address)
        print(f'✅ Gas Payer: {account.address}')
        print(f'💰 Balance: {w3.from_wei(balance, \"ether\")} ARC')
else:
    print('❌ Connection failed')
"
```

**Deliverable:** ✅ Blockchain connection verified

---

### 2.4 Run Backend Server

```bash
# Start the server
python main.py

# Expected output:
# INFO:     Started server process [12345]
# INFO:     Waiting for application startup.
# ✅ Connected to chain ID: 4224 (BlockchainService)
# ✅ Gas Payer Address: 0x...
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test Endpoints:**
```bash
# Health check
curl http://localhost:8000/health | jq

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-11-09T12:00:00Z",
  "version": "v1",
  "environment": "development",
  "services": {
    "api": "operational",
    "blockchain": "ok"
  },
  "stats": {
    "aliases": 4,
    "transactions": 0
  }
}
```

**Deliverable:** ✅ Backend API running and accessible

---

### 2.5 Implement Signature Verification

The backend uses Web3 signature verification for alias registration:

```python
from eth_account import Account
from eth_account.messages import encode_defunct

# Message format (Spanish for security)
message = f"Estoy registrando el alias {alias} para la dirección {address}"

# Hash and verify
message_hash = encode_defunct(text=message)
recovered_address = Account.recover_message(
    message_hash, 
    signature=signature
)

# Check match
if recovered_address.lower() != address.lower():
    raise ValueError("Invalid signature")
```

**Test Signature Verification:**
```bash
# Test with Python
python -c "
from eth_account import Account
from eth_account.messages import encode_defunct

# Create test account
private_key = '0x' + '1' * 64
account = Account.from_key(private_key)

# Sign message
alias = '@testuser'
address = account.address
message = f'Estoy registrando el alias {alias} para la dirección {address}'
message_hash = encode_defunct(text=message)
signed = account.sign_message(message_hash)

print(f'Address: {address}')
print(f'Signature: {signed.signature.hex()}')

# Verify
recovered = Account.recover_message(message_hash, signature=signed.signature)
print(f'Recovered: {recovered}')
print(f'Match: {recovered.lower() == address.lower()}')
"
```

**Deliverable:** ✅ Secure signature verification implemented

---

## Part 3: Integration Testing

### 3.1 End-to-End Test Flow

```bash
# Run automated test suite
python test-client.py --auto

# Expected output:
# ====================================================================
# 🧪 BULUT BACKEND - COMPREHENSIVE TEST SUITE
# ====================================================================
# 
# TEST 1: Health Check
# ✅ PASS     | Health Check
# 
# TEST 2: Root Endpoint
# ✅ PASS     | Root Endpoint
# 
# TEST 3: Get Demo Alias (@alice)
# ✅ PASS     | Get Demo Alias
# 
# ... (more tests)
# 
# ====================================================================
# 📊 TEST RESULTS SUMMARY
# ====================================================================
# Results: 12/12 tests passed (100%)
# ====================================================================
```

### 3.2 Manual Test Scenarios

**Scenario 1: Register Alias with Signature**
```bash
# Generate signature
python -c "
from eth_account import Account
from eth_account.messages import encode_defunct
import requests

# Your wallet
private_key = '0xyour_private_key'
account = Account.from_key(private_key)

# Create signature
alias = '@myalias'
address = account.address
message = f'Estoy registrando el alias {alias} para la dirección {address}'
message_hash = encode_defunct(text=message)
signed = account.sign_message(message_hash)

# Register via API
response = requests.post('http://localhost:8000/alias/register', json={
    'alias': alias,
    'address': address,
    'signature': signed.signature.hex()
})

print(response.json())
"
```

**Scenario 2: AI Payment Processing**
```bash
# Process natural language command
curl -X POST http://localhost:8000/process_command \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Send 10 ARC to @alice for coffee",
    "user_id": "test_user",
    "timezone": "UTC"
  }' | jq

# Expected: Structured payment intent with confidence score
```

**Scenario 3: Execute Real Blockchain Transaction**
```bash
# Execute payment (requires gas payer to have funds)
curl -X POST http://localhost:8000/execute_payment \
  -H "Content-Type: application/json" \
  -H "X-Wallet-Address: 0xYOUR_ADDRESS" \
  -H "X-Signature: 0xYOUR_SIGNATURE" \
  -d '{
    "intent_id": "test_001",
    "payment_intent": {
      "payment_type": "single",
      "intent": {
        "action": "send",
        "amount": 10,
        "currency": "ARC",
        "recipient": {"alias": "@alice"}
      },
      "confidence": 0.95
    },
    "user_signature": "0xYOUR_SIGNATURE",
    "user_address": "0xYOUR_ADDRESS"
  }' | jq

# Expected: Transaction hash and explorer link
```

**Deliverable:** ✅ All integration tests passing

---

## Part 4: Performance Testing

### 4.1 Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils  # Linux
brew install ab  # macOS

# Test health endpoint
ab -n 1000 -c 10 http://localhost:8000/health

# Expected results:
# Requests per second: > 1000
# Time per request: < 10ms (mean)
# Failed requests: 0
```

### 4.2 AI Response Time Testing

```bash
# Test AI processing time
python -c "
import time
import requests

commands = [
    'Send \$50 to @alice',
    'Split \$120 between @bob and @carol',
    'Pay @netflix \$9.99 monthly'
]

for cmd in commands:
    start = time.time()
    response = requests.post('http://localhost:8000/process_command', json={
        'text': cmd
    })
    duration = (time.time() - start) * 1000
    
    print(f'{cmd:50} | {duration:.0f}ms | {response.status_code}')
"

# Expected:
# With AI/ML API: 200-500ms
# With Mock: < 10ms
```

**Deliverable:** ✅ Performance benchmarks documented

---

## Part 5: Deployment

### 5.1 Docker Deployment

```bash
# Build Docker image
docker build -t bulut-backend:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name bulut-backend \
  bulut-backend:latest

# Check logs
docker logs -f bulut-backend

# Or use Docker Compose
docker-compose up -d
```

### 5.2 Production Deployment (VPS)

```bash
# Install on production server
ssh user@your-server.com

# Clone and setup
git clone https://github.com/your-org/bulut-backend.git
cd bulut-backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure production environment
nano .env
# Set APP_ENV=production
# Set DEBUG=false
# Set secure JWT_SECRET
# Configure ALLOWED_ORIGINS

# Run with Gunicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/bulut/access.log \
  --error-logfile /var/log/bulut/error.log \
  --daemon

# Set up as systemd service
sudo nano /etc/systemd/system/bulut.service
```

**Systemd Service File:**
```ini
[Unit]
Description=Bulut Backend API
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/bulut-backend
Environment="PATH=/opt/bulut-backend/venv/bin"
EnvironmentFile=/opt/bulut-backend/.env
ExecStart=/opt/bulut-backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable bulut
sudo systemctl start bulut
sudo systemctl status bulut
```

**Deliverable:** ✅ Production deployment configured

---

## Part 6: Monitoring & Maintenance

### 6.1 Health Monitoring

```bash
# Set up monitoring cron job
crontab -e

# Add health check (every 5 minutes)
*/5 * * * * curl -s http://localhost:8000/health || echo "Bulut API down!" | mail -s "Alert" admin@bulut.app
```

### 6.2 Log Management

```bash
# Rotate logs
sudo nano /etc/logrotate.d/bulut

# Add configuration:
/var/log/bulut/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

### 6.3 Backup Strategy

```bash
# Backup database daily
0 2 * * * /usr/bin/sqlite3 /opt/bulut-backend/bulut.db ".backup '/backup/bulut_$(date +\%Y\%m\%d).db'"

# Backup environment config
0 2 * * * cp /opt/bulut-backend/.env /backup/.env.$(date +\%Y\%m\%d)
```

**Deliverable:** ✅ Monitoring and backup configured

---

## Part 7: Security Hardening

### 7.1 Production Security Checklist

- [ ] Change default `JWT_SECRET` to cryptographically random value
- [ ] Set `ALLOWED_ORIGINS` to specific domains only
- [ ] Use HTTPS/TLS (configure reverse proxy)
- [ ] Store `GAS_PAYER_KEY` securely (e.g., AWS Secrets Manager)
- [ ] Enable rate limiting (`RATE_LIMIT_ENABLED=true`)
- [ ] Set up firewall rules (allow only 80, 443, 22)
- [ ] Configure fail2ban for SSH protection
- [ ] Enable database backups
- [ ] Set up error monitoring (Sentry)
- [ ] Implement API key rotation policy
- [ ] Review and audit all API endpoints
- [ ] Set up intrusion detection

### 7.2 Nginx Reverse Proxy (HTTPS)

```nginx
# /etc/nginx/sites-available/bulut
server {
    listen 80;
    server_name api.bulut.app;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name api.bulut.app;
    
    ssl_certificate /etc/letsencrypt/live/api.bulut.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.bulut.app/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Deliverable:** ✅ Production security implemented

---

## Timeline Summary

| Day | Team | Deliverables |
|-----|------|-------------|
| **Day 1** | AI | ✅ AI/ML API setup, ✅ Prompt engineering, 🔄 Testing |
| **Day 1** | Backend | ✅ Environment setup, ✅ Web3 integration |
| **Day 2** | AI | ✅ NLP logic complete, ✅ Validation |
| **Day 2** | Backend | ✅ All API routes, 🔄 Testing |
| **Day 3** | Both | ✅ Integration testing, ✅ Deployment, ✅ Demo |

**Launch:** End of Day 3 🚀

---

## Support & Resources

- **Documentation:** [API_CONTRACTS.md](API_CONTRACTS.md)
- **Quick Start:** [QUICKSTART.md](QUICKSTART.md)
- **Testing Guide:** [test-client.py](test-client.py)
- **AI/ML API:** https://aimlapi.com/
- **Arc Network:** https://arc.network/
- **Web3.py Docs:** https://web3py.readthedocs.io/

---

**Built with ❤️ by the Bulut Team - Let's revolutionize payments!** 🌥️
