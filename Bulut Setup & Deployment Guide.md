# Bulut Setup & Deployment Guide

## Team Structure & Responsibilities

### 🧠 AI Team
**Lead:** AI/ML Engineer  
**Timeline:** Days 1-2

**Tasks:**
1. ✅ API Configuration (1 hour)
2. ✅ Prompt Engineering (4 hours)
3. ✅ NLP Logic Implementation (6 hours)
4. ✅ Voice Integration (3 hours) - **BONUS**

---

### ⚡ Backend Team
**Lead:** Backend Engineer  
**Timeline:** Days 1-3

**Tasks:**
1. ✅ Edge Infrastructure Setup (4 hours)
2. ✅ Alias Mapping System (3 hours)
3. ✅ Critical Routes (6 hours)
4. ✅ History/Database (4 hours)

---

## Step-by-Step Setup

### Prerequisites

```bash
# Required tools
- Python 3.10+
- Node.js 18+ (for Cloudflare Workers)
- Git
- Docker (optional, for local testing)

# API Keys needed
- Anthropic API Key (with ARCHACK20 credits)
- ElevenLabs API Key (optional, for voice)
- Arc Wallet credentials
- Cloudflare account
```

---

## Part 1: AI Team Setup

### 1.1 Activate Anthropic API

```bash
# Install Claude SDK
pip install anthropic

# Set up API key
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Verify credits with ARCHACK20 code
python -c "
import anthropic
client = anthropic.Anthropic()
print('✓ API Key Valid')
"
```

**Deliverable:** ✅ Working API connection

---

### 1.2 Deploy AI Agent

```bash
# Clone repository
git clone https://github.com/your-org/bulut-ai.git
cd bulut-ai

# Install dependencies
pip install -r requirements.txt

# Requirements.txt content:
# anthropic==0.39.0
# fastapi==0.115.0
# uvicorn==0.30.0
# pydantic==2.9.0
# httpx==0.27.0

# Test the AI agent
python ai_agent.py

# Run FastAPI server
uvicorn ai_agent:app --host 0.0.0.0 --port 8001 --reload
```

**Test Commands:**
```bash
curl -X POST http://localhost:8001/parse_payment \
  -H "Content-Type: application/json" \
  -d '{"text": "Send $50 to @alice", "user_id": "test_user"}'
```

**Expected Output:**
```json
{
  "payment_type": "single",
  "intent": {
    "action": "send",
    "amount": 50,
    "currency": "USD",
    "recipient": {"alias": "@alice"}
  },
  "confidence": 0.95,
  "requires_confirmation": true,
  "confirmation_text": "Send $50 to @alice?"
}
```

**Deliverable:** ✅ `bulut_json_schema.json` ✅ `get_payment_intent()` function

---

### 1.3 Voice Integration (BONUS)

```bash
# Get ElevenLabs API key from: https://elevenlabs.io
export ELEVENLABS_API_KEY="your_key_here"

# Test voice generation
python bulut_voice.py

# Generate demo audio
curl -X POST http://localhost:8002/voice/confirmation \
  -H "Content-Type: application/json" \
  -d @demo_intent.json > confirmation.mp3

# Play audio
open confirmation.mp3  # macOS
# or
mpv confirmation.mp3   # Linux
```

**Deliverable:** ✅ Test audio file for pitch demo

---

## Part 2: Backend Team Setup

### 2.1 Set Up Cloudflare Workers

```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Create new Worker project
wrangler init bulut-api
cd bulut-api

# Configure wrangler.toml
cat > wrangler.toml << EOF
name = "bulut-api"
main = "src/index.py"
compatibility_date = "2025-10-31"
workers_dev = true

[env.production]
name = "bulut-api-production"
route = { pattern = "api.bulut.app/*", zone_name = "bulut.app" }

[[kv_namespaces]]
binding = "ALIAS_DB"
id = "YOUR_KV_NAMESPACE_ID"

[[d1_databases]]
binding = "TX_HISTORY"
database_name = "bulut_transactions"
database_id = "YOUR_D1_DATABASE_ID"
EOF
```

**Deliverable:** ✅ Functional endpoint URL

---

### 2.2 Create KV Namespace (for Alias Storage)

```bash
# Create KV namespace
wrangler kv:namespace create "ALIAS_DB"
# Output: Created namespace with ID: abc123...

# Create KV namespace for production
wrangler kv:namespace create "ALIAS_DB" --env production

# Update wrangler.toml with namespace IDs
```

**Deliverable:** ✅ `get_address_by_alias()` ready

---

### 2.3 Deploy Backend API

```bash
# Copy backend code
cp ../backend_api.py src/index.py

# Set environment secrets
wrangler secret put ANTHROPIC_API_KEY
wrangler secret put ARC_RPC_URL
wrangler secret put ARC_CONTRACT_ADDRESS
wrangler secret put ELEVENLABS_API_KEY

# Deploy to Cloudflare Workers
wrangler deploy

# Output: 
# ✓ Built successfully
# ✓ Deployed to https://bulut-api.your-subdomain.workers.dev
```

**Test Deployment:**
```bash
# Health check
curl https://bulut-api.your-subdomain.workers.dev/health

# Register test alias
curl -X POST https://bulut-api.your-subdomain.workers.dev/alias/register \
  -H "Content-Type: application/json" \
  -d '{
    "alias": "@testuser",
    "address": "0xTEST123...",
    "signature": "0xSIGNATURE..."
  }'

# Process command
curl -X POST https://bulut-api.your-subdomain.workers.dev/process_command \
  -H "Content-Type: application/json" \
  -d '{"text": "Send $50 to @testuser"}'
```

**Deliverable:** ✅ `API_CONTRACTS.md` finalized

---

### 2.4 Set Up Database

```bash
# Create D1 database for transaction history
wrangler d1 create bulut_transactions

# Run migrations
wrangler d1 execute bulut_transactions --file=schema.sql

# schema.sql content:
CREATE TABLE transactions (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    from_address TEXT NOT NULL,
    to_address TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT NOT NULL,
    type TEXT NOT NULL,
    tx_hash TEXT,
    status TEXT NOT NULL,
    memo TEXT
);

CREATE INDEX idx_from ON transactions(from_address);
CREATE INDEX idx_to ON transactions(to_address);
CREATE INDEX idx_timestamp ON transactions(timestamp DESC);
```

**Deliverable:** ✅ Database connection ready

---

## Part 3: Arc Blockchain Integration

### 3.1 Connect to Arc Network

```bash
# Install Arc SDK (example - adjust for actual SDK)
pip install arc-blockchain-sdk

# Configure connection
export ARC_RPC_URL="https://mainnet.arc.network"
export ARC_CHAIN_ID="4224"
export ARC_CONTRACT_ADDRESS="0x..."
```

### 3.2 Test Smart Contract Calls

```python
# test_arc_integration.py
from arc_sdk import ArcClient

client = ArcClient(rpc_url=os.environ['ARC_RPC_URL'])

# Test connection
balance = client.get_balance('0xYOUR_ADDRESS')
print(f"Balance: {balance} ARC")

# Test payment function
tx = client.send_payment(
    from_address='0xSENDER',
    to_address='0xRECIPIENT',
    amount=1.0,
    signature='0xSIGNATURE'
)
print(f"Transaction: {tx.hash}")
```

---

## Part 4: Integration Testing

### 4.1 End-to-End Test Flow

```bash
# 1. Register aliases
curl -X POST $API_URL/alias/register \
  -d '{"alias": "@alice", "address": "0xALICE...", "signature": "0x..."}'

curl -X POST $API_URL/alias/register \
  -d '{"alias": "@bob", "address": "0xBOB...", "signature": "0x..."}'

# 2. Process payment command
INTENT=$(curl -X POST $API_URL/process_command \
  -H "Content-Type: application/json" \
  -d '{"text": "Send 10 ARC to @alice"}')

echo $INTENT | jq .

# 3. Execute payment
curl -X POST $API_URL/execute_payment \
  -H "Content-Type: application/json" \
  -H "X-Wallet-Address: 0xBOB..." \
  -H "X-Signature: 0x..." \
  -d "{
    \"intent_id\": \"test_001\",
    \"payment_intent\": $INTENT,
    \"user_signature\": \"0x...\",
    \"user_address\": \"0xBOB...\"
  }"

# 4. Verify transaction history
curl $API_URL/history/0xBOB...
```

### 4.2 Performance Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test API latency
ab -n 1000 -c 10 https://api.bulut.app/health

# Target: < 100ms p95 latency
# Cloudflare Workers should achieve ~50ms globally
```

---

## Part 5: Frontend Integration

### 5.1 React/Next.js Integration

```typescript
// lib/bulut-client.ts
export class BulutClient {
  private apiUrl = 'https://api.bulut.app';
  
  async processCommand(text: string): Promise<PaymentIntent> {
    const response = await fetch(`${this.apiUrl}/process_command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    
    return response.json();
  }
  
  async executePayment(intent: PaymentIntent, signature: string): Promise<Transaction> {
    const response = await fetch(`${this.apiUrl}/execute_payment`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Wallet-Address': await this.getWalletAddress(),
        'X-Signature': signature
      },
      body: JSON.stringify({
        intent_id: crypto.randomUUID(),
        payment_intent: intent,
        user_signature: signature,
        user_address: await this.getWalletAddress()
      })
    });
    
    return response.json();
  }
}
```

---

## Part 6: Deployment Checklist

### Pre-Launch Checklist

- [ ] **AI Team**
  - [ ] Claude API configured with ARCHACK20 credits
  - [ ] Prompt tested with 100+ sample commands
  - [ ] Confidence scoring calibrated (target: 95%+ accuracy)
  - [ ] Error handling for edge cases implemented
  - [ ] Voice integration tested (optional)

- [ ] **Backend Team**
  - [ ] Cloudflare Workers deployed to production
  - [ ] All environment secrets configured
  - [ ] KV namespace created and tested
  - [ ] D1 database schema deployed
  - [ ] API rate limits configured
  - [ ] CORS headers configured for frontend
  - [ ] Health check endpoint returns 200 OK

- [ ] **Blockchain Integration**
  - [ ] Arc RPC connection verified
  - [ ] Smart contract addresses configured
  - [ ] Test transactions successful on testnet
  - [ ] Gas fee estimation implemented
  - [ ] Transaction retry logic implemented

- [ ] **Security**
  - [ ] Signature verification working
  - [ ] Rate limiting active
  - [ ] Input validation on all endpoints
  - [ ] SQL injection prevention (parameterized queries)
  - [ ] HTTPS enforced

- [ ] **Monitoring**
  - [ ] Error logging configured (Sentry/Datadog)
  - [ ] Performance monitoring (Cloudflare Analytics)
  - [ ] Alerting for API failures
  - [ ] Transaction success rate tracking

---

## Part 7: Demo Preparation

### Pitch Demo Script

```markdown
## 2-Minute Pitch Demo

**[Slide 1: Problem]**
"Traditional payment apps require 7+ taps to send money. What if you could just... talk?"

**[Slide 2: Solution - Live Demo]**
[Open Bulut app]

User: "Send 50 dollars to Alice for lunch"
Bulut: 🎤 "Ready to send $50 to @alice for lunch. Confirm?"
[User confirms]
Bulut: ✅ "Payment sent successfully"

**[Slide 3: Advanced Features]**
User: "Split 120 between Bob, Carol, and Dave"
Bulut: 🎤 "Splitting $120 equally. Confirm?"
[Instant split payment to 3 people]

**[Slide 4: Subscriptions]**
User: "Pay Netflix 9.99 every month"
Bulut: 🎤 "Monthly payment to @netflix set up. Confirm?"
[Automatic recurring payment]

**[Slide 5: Technology]**
- Claude 4 AI for natural language understanding
- Arc blockchain for instant, low-fee transactions
- Cloudflare Workers for global sub-50ms latency

**[Slide 6: Market]**
- $1.9T mobile payment market
- 290M crypto users globally
- First AI-native payment interface

**[Closing]**
"Bulut: The future of payments is conversational."
```

---

## Troubleshooting

### Common Issues

**AI Agent returns low confidence:**
```python
# Adjust prompt to be more specific
# Add more examples to system prompt
# Check for ambiguous user input
```

**Cloudflare Worker timeout:**
```bash
# Increase timeout in wrangler.toml
# Optimize database queries
# Add caching layer
```

**Blockchain transaction fails:**
```python
# Check gas estimation
# Verify wallet has sufficient balance
# Check RPC endpoint health
```

---

## Support & Resources

- **Documentation:** Internal wiki
- **API Playground:** https://api.bulut.app/docs
- **Slack Channel:** #bulut-dev
- **On-call:** +1-XXX-XXX-XXXX

---

## Timeline Summary

| Day | Team | Deliverables |
|-----|------|-------------|
| **Day 1** | AI | ✅ API setup, ✅ Prompt design, 🔄 NLP logic |
| **Day 1** | Backend | ✅ Cloudflare setup, 🔄 Alias DB |
| **Day 2** | AI | ✅ NLP complete, ✅ Voice (bonus) |
| **Day 2** | Backend | ✅ Critical routes, 🔄 History DB |
| **Day 3** | Both | ✅ Integration testing, ✅ Demo prep |

**Launch:** End of Day 3 🚀