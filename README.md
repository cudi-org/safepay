# 🌥️ Bulut Backend

**AI-powered payment processing backend for the Bulut payment platform**

Built with FastAPI, optimized for Cloudflare Workers, featuring natural language payment processing.

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/bulut-backend.git
cd bulut-backend

# Run complete setup
make setup

# Start development server
make dev
```

Visit **http://localhost:8000/docs** for interactive API documentation.

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
- [Contributing](#-contributing)

---

## ✨ Features

### Core Capabilities
- 🧠 **AI-Powered NLP**: Natural language payment processing using Claude Sonnet 4
- ⚡ **Edge Computing**: Optimized for Cloudflare Workers (<50ms global latency)
- 🔗 **Blockchain Integration**: Arc Protocol smart contract integration
- 👥 **Alias System**: Human-readable @username → wallet address mapping
- 💳 **Multiple Payment Types**: Single, recurring subscriptions, and split payments
- 📊 **Transaction History**: Complete audit trail with real-time updates
- 🎤 **Voice Confirmations**: Optional ElevenLabs voice synthesis
- 🔒 **Enterprise Security**: Rate limiting, signature verification, input validation

### Technical Features
- Async/await throughout for maximum performance
- SQLAlchemy ORM with async PostgreSQL/SQLite support
- Comprehensive test suite (pytest)
- Docker containerization
- OpenAPI/Swagger documentation
- Production-ready error handling
- Structured logging

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
│  │  • Rate Limiter                  │   │
│  └─────────────────────────────────┘   │
└──────┬──────────────────┬───────────────┘
       │                  │
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│  AI Agent   │    │ Arc Chain   │
│  (Claude)   │    │  (Smart     │
│             │    │  Contracts) │
└─────────────┘    └─────────────┘
       │
       ▼
┌─────────────┐
│  Database   │
│ (PostgreSQL)│
└─────────────┘
```

---

## 💻 Installation

### Prerequisites

- **Python 3.10+**
- **PostgreSQL 14+** (or SQLite for development)
- **Redis** (optional, for rate limiting)
- **Docker** (optional, for containerization)

### Method 1: Standard Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install

# Set up environment variables
make env
# Edit .env with your API keys

# Initialize database
make db-init

# Run the server
make dev
```

### Method 2: Docker Installation

```bash
# Build and start all services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...
ARC_RPC_URL=https://mainnet.arc.network
ARC_CONTRACT_ADDRESS=0x...

# Optional
ELEVENLABS_API_KEY=...
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/bulut
JWT_SECRET=your-secret-key
ALLOWED_ORIGINS=http://localhost:3000,https://bulut.app
```

### Configuration Options

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | - | Claude API key for NLP processing |
| `ARC_RPC_URL` | Yes | - | Arc blockchain RPC endpoint |
| `ARC_CONTRACT_ADDRESS` | Yes | - | Bulut smart contract address |
| `DATABASE_URL` | No | `sqlite:///bulut.db` | Database connection string |
| `ELEVENLABS_API_KEY` | No | - | Voice synthesis API key |
| `JWT_SECRET` | No | (generated) | Secret for JWT signing |
| `RATE_LIMIT_ENABLED` | No | `true` | Enable rate limiting |
| `LOG_LEVEL` | No | `INFO` | Logging level |

---

## 🛠️ Development

### Running Locally

```bash
# Start development server with auto-reload
make dev

# With debug logging
make dev-debug

# Run tests
make test

# Run tests with coverage
make test-cov

# Format code
make format

# Run linters
make lint

# Run all checks
make check
```

### Project Structure

```
bulut-backend/
├── main.py                 # FastAPI application
├── database.py             # Database models & setup
├── test_backend.py         # Test suite
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker services
├── Makefile               # Development commands
├── .env.example           # Environment template
├── wrangler.toml          # Cloudflare Workers config
└── README.md              # This file
```

### API Development

```python
# Add new endpoint in main.py
@app.post("/your-endpoint")
async def your_endpoint(data: YourModel):
    # Your logic here
    return {"success": True}

# Add tests in test_backend.py
def test_your_endpoint(client):
    response = client.post("/your-endpoint", json={...})
    assert response.status_code == 200
```

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run specific test file
pytest test_backend.py -v

# Run specific test
pytest test_backend.py::test_register_alias_success -v

# Run tests in watch mode
make test-watch
```

### Test Coverage

Current test coverage: **85%+**

```bash
# Generate coverage report
make test-cov

# View HTML report
open htmlcov/index.html
```

### Writing Tests

```python
# Example test
def test_new_feature(client):
    """Test description"""
    response = client.post("/endpoint", json={"data": "value"})
    assert response.status_code == 200
    assert response.json()["success"] == True
```

---

## 🚀 Deployment

### Cloudflare Workers (Recommended)

```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Configure wrangler.toml with your account details

# Deploy to production
make deploy-cloudflare

# Deploy to staging
make deploy-staging
```

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
docker-compose -f docker-compose.prod.yml up -d
```

### Traditional Server Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY=...
export ARC_RPC_URL=...

# Run with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

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

#### Process Command
```bash
POST /process_command
Content-Type: application/json

{
  "text": "Send $50 to @alice",
  "user_id": "user_123",
  "timezone": "UTC"
}
```

#### Register Alias
```bash
POST /alias/register
Content-Type: application/json

{
  "alias": "@alice",
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "signature": "0x..."
}
```

#### Execute Payment
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

#### Get Transaction History
```bash
GET /history/{address}?limit=50&offset=0
```

See [API_CONTRACTS.md](API_CONTRACTS.md) for complete documentation.

---

## 🔒 Security

### Best Practices Implemented

✅ **Input Validation**: Pydantic models for all inputs  
✅ **SQL Injection Protection**: Parameterized queries  
✅ **XSS Prevention**: Sanitized outputs  
✅ **Rate Limiting**: Configurable limits per endpoint  
✅ **Signature Verification**: Cryptographic validation  
✅ **CORS Configuration**: Whitelist-based origins  
✅ **HTTPS Only**: Enforced in production  
✅ **Secrets Management**: Environment-based configuration  

### Security Checklist

Before deploying to production:

- [ ] Change default `JWT_SECRET`
- [ ] Configure `ALLOWED_ORIGINS` properly
- [ ] Enable HTTPS/TLS
- [ ] Set up rate limiting backend (Redis)
- [ ] Configure Sentry for error monitoring
- [ ] Review and update firewall rules
- [ ] Enable database backups
- [ ] Set up log aggregation

---

## 📊 Monitoring & Logging

### Health Monitoring

```bash
# Check application health
make health-check

# View logs
make logs

# Docker logs
make docker-logs
```

### Sentry Integration

```bash
# Set Sentry DSN in .env
SENTRY_DSN=https://...@sentry.io/...

# Errors will be automatically reported
```

### Performance Monitoring

```bash
# Run benchmark
make benchmark

# Run load test
make load-test
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'main'`  
**Solution**: Make sure you're in the project directory and virtual environment is activated.

**Issue**: `Database connection failed`  
**Solution**: Check `DATABASE_URL` in `.env` and ensure PostgreSQL is running.

**Issue**: `AI agent timeout`  
**Solution**: Verify `ANTHROPIC_API_KEY` is valid and AI agent service is running.

**Issue**: `Rate limit exceeded`  
**Solution**: Check Redis connection or disable rate limiting in development.

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=DEBUG make dev

# Check configuration
python -c "from main import config; print(vars(config))"
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Format code (`make format`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines

- Write tests for new features
- Follow PEP 8 style guide (enforced by `black` and `flake8`)
- Update documentation
- Add type hints
- Keep functions focused and small

---

## 📄 License

This project is proprietary and confidential.

---

## 👥 Team

**Backend Team**
- Lead Backend Engineer
- DevOps Engineer
- Database Administrator

**AI Team**
- AI/ML Engineer
- NLP Specialist

---

## 📞 Support

- **Documentation**: https://docs.bulut.app
- **API Status**: https://status.bulut.app
- **Email**: dev@bulut.app
- **Discord**: https://discord.gg/bulut

---

## 🙏 Acknowledgments

- **Anthropic** for Claude AI API
- **Arc Protocol** for blockchain infrastructure
- **FastAPI** for the amazing framework
- **Cloudflare** for edge computing platform

---

## 📈 Roadmap

- [x] Core payment processing
- [x] Alias system
- [x] Transaction history
- [ ] WebSocket support for real-time updates
- [ ] Multi-currency support
- [ ] Advanced analytics dashboard
- [ ] Mobile SDK
- [ ] Recurring payment optimization
- [ ] Multi-signature wallet support

---

**Built with ❤️ by the Bulut Team**