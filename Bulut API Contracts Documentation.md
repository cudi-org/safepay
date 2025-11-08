# Bulut API Contracts Documentation

**Version:** 1.0.0  
**Base URL:** `https://api.bulut.app/v1`  
**Last Updated:** November 09, 2025

---

## Table of Contents

1. [Authentication](#authentication)
2. [Core Endpoints](#core-endpoints)
3. [Alias Management](#alias-management)
4. [Payment Processing](#payment-processing)
5. [Transaction History](#transaction-history)
6. [Error Codes](#error-codes)
7. [Rate Limits](#rate-limits)

---

## Authentication

All authenticated endpoints require a signed request:

```http
Authorization: Bearer {JWT_TOKEN}
X-Wallet-Address: {USER_WALLET_ADDRESS}
X-Signature: {SIGNED_PAYLOAD}
```

**Signature Format:**
```javascript
// Using Web3.py
from eth_account.messages import encode_defunct
from eth_account import Account

message = f"Register alias {alias} for address {address}"
message_hash = encode_defunct(text=message)
signature = Account.sign_message(message_hash, private_key=private_key)
```

---

## Core Endpoints

### Health Check

```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-09T12:00:00Z",
  "version": "v1",
  "environment": "production",
  "services": {
    "api": "operational",
    "blockchain": "ok"
  },
  "stats": {
    "aliases": 1542,
    "transactions": 8934
  }
}
```

---

## Alias Management

### Register Alias

Register a new `@username` → wallet address mapping with cryptographic signature verification.

```http
POST /alias/register
Content-Type: application/json
```

**Request Body:**
```json
{
  "alias": "@alice",
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "signature": "0x1b8c9d..."
}
```

**Signature Requirements:**
- Message format: `"Estoy registrando el alias {alias} para la dirección {address}"`
- Must be signed with the private key corresponding to the address
- Signature verification using Web3 `Account.recover_message()`

**Response (201 Created):**
```json
{
  "success": true,
  "alias": "@alice",
  "address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "message": "Alias registered successfully"
}
```

**Error Responses:**
- `409 Conflict` - Alias already registered
- `400 Bad Request` - Invalid alias format
- `403 Forbidden` - Invalid signature (signature doesn't match address)
- `422 Unprocessable Entity` - Invalid request format

---

### Resolve Alias to Address

```http
GET /alias/{alias}
```

**Example:**
```http
GET /alias/@alice
```

**Response (200 OK):**
```json
{
  "alias": "@alice",
  "address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb"
}
```

**Error Response:**
- `404 Not Found` - Alias does not exist

---

### Get Alias by Address

```http
GET /address/{address}/alias
```

**Response (200 OK):**
```json
{
  "address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "alias": "@alice"
}
```

If no alias registered, returns:
```json
{
  "address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "alias": null
}
```

---

### Search Aliases

```http
GET /alias/search?query={search_term}&limit={limit}
```

**Query Parameters:**
- `query` (required): Search term (minimum 2 characters)
- `limit` (optional): Maximum results (default: 10, max: 50)

**Response (200 OK):**
```json
[
  {
    "alias": "@alice",
    "address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb"
  },
  {
    "alias": "@alice_smith",
    "address": "0x8626f6940e2eb28930efb4cef49b2d1f2c9c1199"
  }
]
```

---

## Payment Processing

### Process Natural Language Command

Convert human language to structured payment intent using AI/ML API (GPT-4o).

```http
POST /process_command
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "Send $50 to @alice for lunch",
  "user_id": "user_12345",
  "timezone": "America/New_York"
}
```

**Response (200 OK):**
```json
{
  "payment_type": "single",
  "intent": {
    "action": "send",
    "amount": 50,
    "currency": "USD",
    "recipient": {
      "alias": "@alice"
    },
    "memo": "Lunch payment"
  },
  "confidence": 0.95,
  "requires_confirmation": true,
  "confirmation_text": "Send $50 to @alice for lunch payment?",
  "_metadata": {
    "raw_input": "Send $50 to @alice for lunch",
    "parsed_at": "2025-11-09T12:00:00Z",
    "model": "gpt-4o",
    "parser": "real"
  }
}
```

**Mock Mode Response (No AI API Key):**
```json
{
  "payment_type": "single",
  "intent": {
    "action": "send",
    "amount": 50,
    "currency": "USD",
    "recipient": {
      "alias": "@alice"
    },
    "memo": "Mocked payment"
  },
  "confidence": 0.85,
  "requires_confirmation": true,
  "confirmation_text": "Send USD 50 to @alice?",
  "_metadata": {
    "parser": "mock"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "payment_type": null,
  "intent": {},
  "confidence": 0.0,
  "requires_confirmation": false,
  "error": {
    "code": "missing_amount",
    "message": "Could not determine payment amount",
    "suggestions": [
      "Try specifying an amount like '$50'",
      "Use format: 'send [amount] to [recipient]'"
    ]
  }
}
```

**Status Codes:**
- `200 OK` - Successfully parsed (confidence ≥ 0.5)
- `400 Bad Request` - Low confidence or parsing error
- `503 Service Unavailable` - AI agent not configured

---

### Execute Payment

Execute a confirmed payment intent on the Arc blockchain.

```http
POST /execute_payment
Content-Type: application/json
X-Wallet-Address: {USER_ADDRESS}
X-Signature: {SIGNATURE}
```

**Request Body:**
```json
{
  "intent_id": "intent_abc123",
  "payment_intent": {
    "payment_type": "single",
    "intent": {
      "action": "send",
      "amount": 50,
      "currency": "ARC",
      "recipient": {
        "alias": "@alice",
        "address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb"
      },
      "memo": "Lunch payment"
    },
    "confidence": 0.95,
    "requires_confirmation": true
  },
  "user_signature": "0x1b8c9d...",
  "user_address": "0x123abc..."
}
```

**Response (200 OK - Success):**
```json
{
  "success": true,
  "transaction_hash": "0xabc123def456...",
  "blockchain": "arc",
  "timestamp": "2025-11-09T12:00:05Z",
  "amount": 50.0,
  "from_address": "0x123abc...",
  "to_address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "explorer_url": "https://explorer.arc.network/tx/0xabc123def456...",
  "error": null
}
```

**Response (200 OK - Failure):**
```json
{
  "success": false,
  "transaction_hash": null,
  "blockchain": "arc",
  "timestamp": "2025-11-09T12:00:05Z",
  "error": "Insufficient funds"
}
```

**Status Codes:**
- `200 OK` - Transaction processed (check `success` field)
- `404 Not Found` - Recipient alias not found
- `403 Forbidden` - Header address doesn't match request body
- `503 Service Unavailable` - Blockchain service not initialized

---

### Execute Subscription Payment

```http
POST /execute_payment
```

**Request Body (Subscription Example):**
```json
{
  "intent_id": "sub_xyz789",
  "payment_intent": {
    "payment_type": "subscription",
    "intent": {
      "action": "send",
      "amount": 9.99,
      "currency": "ARC",
      "recipient": {
        "alias": "@netflix"
      },
      "subscription": {
        "frequency": "monthly",
        "start_date": "2025-11-01T00:00:00Z",
        "total_payments": 12
      }
    },
    "confidence": 0.92,
    "requires_confirmation": true
  },
  "user_signature": "0x...",
  "user_address": "0x..."
}
```

**Response:** Same format as single payment, includes `subscription_id`

**Note:** Subscription execution is currently simulated (not on-chain smart contract).

---

### Execute Split Payment

```http
POST /execute_payment
```

**Request Body (Split Example):**
```json
{
  "intent_id": "split_456",
  "payment_intent": {
    "payment_type": "split",
    "intent": {
      "action": "split",
      "amount": 120,
      "currency": "ARC",
      "recipients": [
        {
          "alias": "@bob",
          "percentage": 40,
          "amount": 48
        },
        {
          "alias": "@carol",
          "percentage": 60,
          "amount": 72
        }
      ],
      "memo": "Dinner split"
    },
    "confidence": 0.89,
    "requires_confirmation": true
  },
  "user_signature": "0x...",
  "user_address": "0x..."
}
```

**Note:** Split payment execution is currently simulated (not on-chain smart contract).

---

## Transaction History

### Get User Transaction History

```http
GET /history/{address}?limit=50&offset=0
```

**Example:**
```http
GET /history/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb?limit=20
```

**Response (200 OK):**
```json
{
  "address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "total_count": 45,
  "count": 15,
  "transactions": [
    {
      "id": "tx_abc123",
      "timestamp": "2025-11-09T11:45:00Z",
      "from_address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
      "to_address": "0x123abc...",
      "amount": 50,
      "currency": "ARC",
      "type": "single",
      "transaction_hash": "0xabc123def456...",
      "status": "success",
      "memo": "Lunch payment"
    }
  ]
}
```

**Query Parameters:**
- `limit` (optional): Maximum number of transactions (default: 50, max: 100)
- `offset` (optional): Pagination offset (default: 0)

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `alias_exists` | 409 | Alias already registered |
| `address_has_alias` | 409 | Address already has an alias |
| `alias_not_found` | 404 | Alias does not exist |
| `invalid_alias_format` | 422 | Alias format invalid (must be @username, 3-20 chars) |
| `invalid_signature` | 403 | Cryptographic signature verification failed |
| `signature_error` | 400 | Error processing signature |
| `recipient_not_found` | 404 | Payment recipient alias not found |
| `insufficient_funds` | 400 | User wallet has insufficient balance |
| `missing_amount` | 400 | Payment amount not specified |
| `missing_recipient` | 400 | Payment recipient not specified |
| `ambiguous_intent` | 400 | AI could not parse payment intent clearly |
| `unexpected_error` | 500 | Unexpected error occurred |
| `blockchain_error` | 500 | Blockchain RPC error |
| `service_unavailable` | 503 | Required service not initialized |

**Standard Error Response:**
```json
{
  "error": {
    "code": "insufficient_funds",
    "message": "Wallet balance too low for transaction",
    "details": {
      "required": 50,
      "available": 25,
      "currency": "ARC"
    }
  },
  "timestamp": "2025-11-09T12:00:00Z"
}
```

---

## Rate Limits

Rate limiting is configurable via `RATE_LIMIT_ENABLED` environment variable.

| Endpoint | Rate Limit | Window |
|----------|------------|--------|
| `/process_command` | 100 requests | 1 minute |
| `/execute_payment` | 10 requests | 1 minute |
| `/alias/register` | 5 requests | 1 hour |
| `/alias/{alias}` | 1000 requests | 1 minute |
| `/history/{address}` | 50 requests | 1 minute |

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699545600
```

**Rate Limit Exceeded Response (429):**
```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Too many requests. Please wait before retrying.",
    "retry_after": 45
  }
}
```

---

## Technology Stack

### AI/NLP Processing
- **AI/ML API** with GPT-4o model
- Fallback to pattern-matching mock parser when API key not configured
- Structured JSON output with confidence scoring

### Blockchain
- **Arc Protocol** blockchain (Chain ID: 4224)
- **Web3.py** for blockchain interactions
- **eth-account** for signature verification
- Native ARC token transactions (real on-chain)
- USDC contract address: `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`

### Backend
- **FastAPI** - Modern async Python web framework
- **Pydantic** - Data validation and serialization
- **Uvicorn** - ASGI server
- **HTTPX** - Async HTTP client

### Storage
- In-memory storage for development
- PostgreSQL/SQLite support via SQLAlchemy (production-ready)
- Redis support for rate limiting

---

## SDK Examples

### Python
```python
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
import requests

# Initialize
API_URL = "https://api.bulut.app/v1"
w3 = Web3(Web3.HTTPProvider("https://mainnet.arc.network"))

# Register alias with signature
def register_alias(alias: str, address: str, private_key: str):
    message = f"Estoy registrando el alias {alias} para la dirección {address}"
    message_hash = encode_defunct(text=message)
    signed = Account.sign_message(message_hash, private_key=private_key)
    
    response = requests.post(f"{API_URL}/alias/register", json={
        "alias": alias,
        "address": address,
        "signature": signed.signature.hex()
    })
    return response.json()

# Process payment command
def process_command(text: str):
    response = requests.post(f"{API_URL}/process_command", json={
        "text": text,
        "user_id": "user_123",
        "timezone": "UTC"
    })
    return response.json()

# Execute payment
def execute_payment(intent, user_address: str, private_key: str):
    # Sign payment
    message = f"Execute payment: {intent['intent_id']}"
    message_hash = encode_defunct(text=message)
    signed = Account.sign_message(message_hash, private_key=private_key)
    
    response = requests.post(
        f"{API_URL}/execute_payment",
        json={
            "intent_id": intent["intent_id"],
            "payment_intent": intent,
            "user_signature": signed.signature.hex(),
            "user_address": user_address
        },
        headers={
            "X-Wallet-Address": user_address,
            "X-Signature": signed.signature.hex()
        }
    )
    return response.json()
```

### JavaScript/TypeScript
```typescript
import { ethers } from 'ethers';

const API_URL = 'https://api.bulut.app/v1';

// Register alias
async function registerAlias(alias: string, address: string, signer: ethers.Signer) {
  const message = `Estoy registrando el alias ${alias} para la dirección ${address}`;
  const signature = await signer.signMessage(message);
  
  const response = await fetch(`${API_URL}/alias/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ alias, address, signature })
  });
  
  return response.json();
}

// Process command
async function processCommand(text: string) {
  const response = await fetch(`${API_URL}/process_command`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, user_id: 'user_123', timezone: 'UTC' })
  });
  
  return response.json();
}
```

---

## Testing

**Sandbox Environment:**
- Base URL: `http://localhost:8000`
- Demo aliases: `@alice`, `@bob`, `@charlie`, `@demo`
- No real funds required

**Environment Variables:**
```bash
# Required
AIMLAPI_KEY=your_api_key_here
ARC_RPC_URL=https://mainnet.arc.network
GAS_PAYER_KEY=your_private_key_here

# Optional
ARC_USDC_ADDRESS=0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
ARC_CHAIN_ID=4224
```

---

## Support

- **Documentation:** https://docs.bulut.app
- **API Status:** https://status.bulut.app
- **Discord:** https://discord.gg/bulut
- **Email:** dev@bulut.app
- **GitHub:** https://github.com/bulut-app
