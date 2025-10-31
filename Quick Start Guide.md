# 🚀 Bulut Backend - Quick Start Guide

Get the fully functional backend running in **2 minutes**!

---

## ⚡ Super Quick Start (One Command)

```bash
# Make start script executable
chmod +x start.sh

# Run it!
./start.sh
```

That's it! The API is now running at **http://localhost:8000** ✨

---

## 📦 Manual Setup (If start.sh doesn't work)

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install fastapi uvicorn pydantic httpx
```

### 2. Run the Server

```bash
python3 main.py
```

**Done!** Visit http://localhost:8000/docs

---

## 🧪 Test the API

### Option 1: Automated Tests

```bash
# Install test client
pip install requests

# Run all tests
python3 test_client.py --auto
```

### Option 2: Interactive Testing

```bash
# Run interactive test client
python3 test_client.py
```

### Option 3: Manual Testing (curl)

```bash
# Health check
curl http://localhost:8000/health

# Get demo alias
curl http://localhost:8000/alias/@alice

# Process payment command
curl -X POST http://localhost:8000/process_command \
  -H "Content-Type: application/json" \
  -d '{"text": "Send $50 to @alice"}'

# Register new alias
curl -X POST http://localhost:8000/alias/register \
  -H "Content-Type: application/json" \
  -d '{
    "alias": "@myname",
    "address": "0x1234567890abcdef1234567890abcdef12345678",
    "signature": "0xabcd..."
  }'
```

---

## 🎯 Quick API Reference

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root info + demo aliases |
| `/health` | GET | Health check + stats |
| `/docs` | GET | Interactive API docs |
| `/alias/register` | POST | Register new alias |
| `/alias/{alias}` | GET | Resolve alias to address |
| `/address/{address}/alias` | GET | Get alias for address |
| `/process_command` | POST | Parse payment command |
| `/execute_payment` | POST | Execute payment |
| `/history/{address}` | GET | Transaction history |
| `/subscriptions/{address}` | GET | Active subscriptions |

### Demo Aliases (Pre-loaded)

```
@alice   → 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
@bob     → 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199
@charlie → 0xdD870fA1b7C4700F2BD7f44238821C26f7392148
@demo    → 0x4E5B2ea1F6E7eA1e5e5E5e5e5e5e5e5e5e5e5e5
```

---

## 💡 Example Usage

### 1. Single Payment

```bash
# Parse command
curl -X POST http://localhost:8000/process_command \
  -H "Content-Type: application/json" \
  -d '{"text": "Send $50 to @alice for lunch"}'

# Response:
{
  "payment_type": "single",
  "intent": {
    "action": "send",
    "amount": 50.0,
    "currency": "USD",
    "recipient": {