 🌥️ Bulut Backend

**AI-powered payment processing backend for the Bulut payment platform**

Built with FastAPI, optimized for Cloudflare Workers, featuring natural language payment processing.

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install fastapi uvicorn pydantic httpx web3 openai

# Set up environment variables
export AIMLAPI_KEY="your_api_key_from_aimlapi.com"
export ARC_RPC_URL="https://mainnet.arc.network"
export GAS_PAYER_KEY="your_private_key_here"

# Run the server
python main.py
```

Visit **http://localhost:8000/docs** for interactive API documentation.

**That's it!** The backend is now running with:
- ✅ AI-powered natural language processing (GPT-4o)
- ✅ Real blockchain transactions (Arc Protocol)
- ✅ Web3 signature verification
- ✅ Demo aliases pre-loaded (@alice, @bob, @charlie, @demo)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [API Documentation](#-api-documentation)

---

## ✨ Features

### Core Capabilities
- 🧠 **AI-Powered NLP**: Natural language payment processing using AI/ML API (GPT-4o)
- 🔗 **Arc Blockchain**: Real on-chain transactions via Web3.py
- 👥 **Alias System**: Human-readable @username → wallet address mapping
- 🔒 **Cryptographic Security**: Web3 signature verification for all operations
- 💳 **Multiple Payment Types**: Single, recurring subscriptions, and split payments
- 📊 **Transaction History**: Complete audit trail with blockchain explorer links
- ⚡ **Fast Performance**: In-memory caching, async/await throughout

### Technical Features
- Async/await throughout for maximum performance
- Web3.py integration for blockchain interactions
- Comprehensive test suite (pytest)
- Docker containerization
- OpenAPI/Swagger documentation
- Production-ready error handling
- Mock AI parser fallback (works without API key)

---

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │
│  (React/TS) │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         Bulut Backend API                │
│  ┌─────────────────────────────────┐   │
│  │     FastAPI Application          │   │
│  ├─────────────────────────────────┤   │
│  │  • Alias Service                 │   │
│  │  • Payment Processor             │   │
│  │  • Transaction Manager           │   │
│  │  • Web3 Integration              │   │
│  └─────────────────────────────────┘   │
└──────┬──────────────────┬───────────────┘
       │                  │
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│  AI/ML API  │    │ Arc Chain   │
│  (GPT-4o)   │    │  (Web3.py)  │
│             │    │             │
└─────────────┘    └─────────────┘
       │
       ▼
┌─────────────┐
│  Database   │
│ (In-Memory/ │
│  SQLite)    │
└─────────────┘
```

---

## 💻 Installation

### Prerequisites

- **Python 3.10+**
- **AI/ML API Key** (from aimlapi.com)
- **Arc Network Access** (RPC URL and gas payer private key)
- **Docker** (optional, for containerization)

### Method 1: Standard Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# - AIMLAPI_KEY=your_key_here
# - ARC_RPC_URL=https://mainnet.arc.network
# - GAS_PAYER_KEY=your_private_key

# Run the server
python main.py
```

### Method 2: Docker Installation

```bash
# Build and start
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required - AI Processing
AIMLAPI_KEY=your_api_key_here

# Required - Blockchain
ARC_RPC_URL=https://mainnet.arc.network
ARC_CHAIN_ID=4224
GAS_PAYER_KEY=your_private_key_here

# Optional - Smart Contracts
ARC_USDC_ADDRESS=0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
ARC_EXPLORER_URL=https://explorer.arc.network

# Optional - Server Configuration
HOST=0.0.0.0
PORT=8000
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# Optional - Storage
DATABASE_URL=sqlite:///./bulut.db

# Optional - Security
JWT_SECRET=your-secret-key
ALLOWED_ORIGINS=*
```

### Configuration Options

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AIMLAPI_KEY` | Yes | - | AI/ML API key for NLP processing (GPT-4o) |
| `ARC_RPC_URL` | Yes | - | Arc blockchain RPC endpoint |
| `GAS_PAYER_KEY` | Yes | - | Private key for gas payment on transactions |
| `ARC_CHAIN_ID` | No | `4224` | Arc network chain ID |
| `ARC_USDC_ADDRESS` | No | `0xA0b...` | USDC contract address on Arc |
| `ARC_EXPLORER_URL` | No | `https://...` | Blockchain explorer base URL |
| `DATABASE_URL` | No | `sqlite:///bulut.db` | Database connection string |
| `JWT_SECRET` | No | (generated) | Secret for JWT signing |
| `RATE_LIMIT_ENABLED` | No | `false` | Enable rate limiting |
| `LOG_LEVEL` | No | `INFO` | Logging level |

---

## 🛠️ Development

### Running Locally

```bash
# Start development server with auto-reload
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest test-backend.py -v

# Run interactive test client
python test-client.py
```

### Project Structure

```
bulut-backend/
├── main.py                 # FastAPI application (core API)
├── agent.py                # AI payment parsing (Real + Mock)
├── blockchain_service.py   # Web3 blockchain integration
├── test-backend.py         # Comprehensive test suite
├── test-client.py          # Interactive test client
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── docker-compose.yml      # Docker services
├── Dockerfile              # Docker configuration
└── README.md               # This file
```

### API Development

```python
# Add new endpoint in main.py
@app.post("/your-endpoint")
async def your_endpoint(data: YourModel):
    # Your logic here
    return {"success": True}

# Add tests in test-backend.py
def test_your_endpoint(client):
    response = client.post("/your-endpoint", json={...})
    assert response.status_code == 200
```

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest test-backend.py -v

# Run specific test
pytest test-backend.py::test_register_alias_success -v

# Run with coverage
pytest test-backend.py --cov=. --cov-report=html

# Run interactive test client
python test-client.py --auto  # Automated
python test-client.py         # Interactive mode
```

### Test Coverage

Current test coverage: **85%+**

Tests include:
- ✅ Alias registration with signature verification
- ✅ Alias resolution and reverse lookup
- ✅ Payment command processing (AI + Mock)
- ✅ Payment execution (single, split, subscription)
- ✅ Transaction history and retrieval
- ✅ Error handling and edge cases
- ✅ Security (SQL injection, XSS prevention)
- ✅ Blockchain integration

---

## 🚀 Deployment

### Docker Deployment

```bash
# Build production image
docker build -t bulut-backend:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name bulut-backend \
  bulut-backend:latest

# With Docker Compose
docker-compose up -d
```

### Traditional Server Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AIMLAPI_KEY=...
export ARC_RPC_URL=...
export GAS_PAYER_KEY=...

# Run with Gunicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Production Checklist

- [ ] Set `AIMLAPI_KEY` for production AI processing
- [ ] Configure `GAS_PAYER_KEY` with funded account
- [ ] Set secure `JWT_SECRET`
- [ ] Configure `ALLOWED_ORIGINS` properly
- [ ] Enable HTTPS/TLS
- [ ] Set up monitoring (Sentry)
- [ ] Configure database backups
- [ ] Enable rate limiting (set `RATE_LIMIT_ENABLED=true`)

---

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Key Endpoints

#### Health Check
```bash
GET /health
```

#### Register Alias (with Web3 Signature)
```bash
POST /alias/register
Content-Type: application/json

{
  "alias": "@alice",
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "signature": "0x..."
}
```

#### Process Command (AI/ML API)
```bash
POST /process_command
Content-Type: application/json

{
  "text": "Send $50 to @alice",
  "user_id": "user_123",
  "timezone": "UTC"
}
```

#### Execute Payment (Web3 Transaction)
```bash
POST /execute_payment
Content-Type: application/json
X-Wallet-Address: 0x...
X-Signature: 0x...

{
  "intent_id": "intent_123",
  "payment_intent": {...},
  "user_signature": "0x...",
  "user_address": "0x..."
}
```

See [API_CONTRACTS.md](API_CONTRACTS.md) for complete documentation.

---

## 🔒 Security

### Implemented Security Features

✅ **Web3 Signature Verification**: All alias registrations verified cryptographically  
✅ **Input Validation**: Pydantic models for all inputs  
✅ **SQL Injection Protection**: Parameterized queries  
✅ **XSS Prevention**: Sanitized outputs  
✅ **CORS Configuration**: Whitelist-based origins  
✅ **HTTPS Only**: Enforced in production  
✅ **Rate Limiting**: Configurable limits per endpoint  

### Signature Verification

```python
from eth_account import Account
from eth_account.messages import encode_defunct

# Create message
message = f"Estoy registrando el alias {alias} para la dirección {address}"
message_hash = encode_defunct(text=message)

# Verify signature
recovered_address = Account.recover_message(message_hash, signature=signature)

if recovered_address.lower() != address.lower():
    raise ValueError("Invalid signature")
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'web3'`  
**Solution**: Install dependencies: `pip install -r requirements.txt`

**Issue**: `AIMLAPI_KEY not found`  
**Solution**: Create `.env` file and add `AIMLAPI_KEY=your_key_here`

**Issue**: `Web3 not connected to network`  
**Solution**: Check `ARC_RPC_URL` in `.env` and network connectivity

**Issue**: `GAS_PAYER_KEY not set. Real transactions will fail`  
**Solution**: Add funded private key to `.env` as `GAS_PAYER_KEY`

**Issue**: AI agent returns low confidence  
**Solution**: Make command more specific or check if AIMLAPI_KEY is valid

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest test-backend.py`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📄 License

This project is proprietary and confidential.

---

## 👥 Team

**Backend Team**
- Lead Backend Engineer
- Blockchain Integration Specialist
- DevOps Engineer

**AI Team**
- AI/ML Engineer
- NLP Specialist

---

## 📞 Support

- **Documentation**: https://docs.bulut.app
- **API Status**: https://status.bulut.app
- **Email**: dev@bulut.app
- **Discord**: https://discord.gg/bulut
- **GitHub**: https://github.com/bulut-app

---

## 🙏 Acknowledgments

- **AI/ML API** for GPT-4o access
- **Arc Protocol** for blockchain infrastructure
- **Web3.py** for Ethereum-compatible interactions
- **FastAPI** for the amazing framework
- **OpenAI** for GPT-4o model

---

## 📈 Technology Stack

### Backend Framework
- **FastAPI** - Modern async Python web framework
- **Uvicorn** - Lightning-fast ASGI server
- **Pydantic** - Data validation and serialization

### AI/NLP
- **AI/ML API** - GPT-4o model access
- **Pattern matching** - Fallback mock parser

### Blockchain
- **Web3.py** - Ethereum/Arc blockchain interactions
- **eth-account** - Signature creation and verification
- **Arc Protocol** - Layer 2 blockchain (Chain ID: 4224)

### Storage
- **In-memory** - Development and demo
- **SQLite** - Local persistence
- **PostgreSQL** - Production (via SQLAlchemy)

### Additional
- **HTTPX** - Async HTTP client
- **pytest** - Testing framework
- **Docker** - Containerization

---

## 📈 Roadmap

- [x] Core payment processing with AI
- [x] Alias system with Web3 signatures
- [x] Real blockchain transactions
- [x] Transaction history
- [ ] WebSocket support for real-time updates
- [ ] Smart contract for subscriptions
- [ ] Smart contract for split payments
- [ ] Multi-currency support (ETH, BTC, USDC)
- [ ] Advanced analytics dashboard
- [ ] Mobile SDK
- [ ] Multi-signature wallet support

---

**Built with ❤️ by the Bulut Team**
