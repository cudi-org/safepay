# Bulut API Contracts Documentation

**Version:** 1.0.0  
**Base URL:** `https://api.bulut.app/v1`  
**Last Updated:** October 31, 2025

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
signature = sign(sha256(payload + timestamp + wallet_address), private_key)
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
  "timestamp": "2025-10-31T12:00:00Z",
  "services": {
    "api": "operational",
    "database": "operational",
    "blockchain": "operational"
  }
}
```

---

## Alias Management

### Register Alias

Register a new `@username` → wallet address mapping.

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

**Response (201 Created):**
```json
{
  "success": true,
  "alias": "@alice",
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "message": "Alias registered successfully"
}
```

**Error Responses:**
- `409 Conflict` - Alias already registered
- `400 Bad Request` - Invalid alias format
- `401 Unauthorized` - Invalid signature

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
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
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
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "alias": "@alice"
}
```

If no alias registered, returns:
```json
{
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "alias": null
}
```

---

## Payment Processing

### Process Natural Language Command

Convert human language to structured payment intent.

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
    "parsed_at": "2025-10-31T12:00:00Z",
    "model_version": "claude-sonnet-4-20250514"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": {
    "code": "ambiguous_intent",
    "message": "Could not determine payment amount",
    "suggestions": [
      "Try specifying an amount like '$50'",
      "Use format: 'send [amount] to [recipient]'"
    ]
  },
  "confidence": 0.3
}
```

**Status Codes:**
- `200 OK` - Successfully parsed (confidence ≥ 0.5)
- `400 Bad Request` - Low confidence or parsing error
- `422 Unprocessable Entity` - Invalid input format

---

### Execute Payment

Execute a confirmed payment intent on the blockchain.

```http
POST /execute_payment
Content-Type: application/json
Authorization: Bearer {JWT_TOKEN}
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
      "currency": "USD",
      "recipient": {
        "alias": "@alice",
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
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

**Response (200 OK):**
```json
{
  "success": true,
  "transaction_hash": "0xabc123def456...",
  "blockchain": "arc",
  "timestamp": "2025-10-31T12:00:05Z",
  "error": null
}
```

**Response (500 Internal Server Error):**
```json
{
  "success": false,
  "transaction_hash": null,
  "blockchain": "arc",
  "timestamp": "2025-10-31T12:00:05Z",
  "error": "Insufficient funds"
}
```

**Status Codes:**
- `200 OK` - Transaction executed (check `success` field)
- `404 Not Found` - Recipient alias not found
- `401 Unauthorized` - Invalid signature
- `400 Bad Request` - Invalid payment intent

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
      "currency": "USD",
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

**Response:** Same format as single payment

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
      "currency": "USD",
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

---

## Transaction History

### Get User Transaction History

```http
GET /history/{address}?limit=50
```

**Example:**
```http
GET /history/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb?limit=20
```

**Response (200 OK):**
```json
{
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "count": 15,
  "transactions": [
    {
      "id": "tx_abc123",
      "timestamp": "2025-10-31T11:45:00Z",
      "from": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
      "to": "0x123abc...",
      "amount": 50,
      "type": "single",
      "tx_hash": "0xabc123def456...",
      "status": "success",
      "memo": "Lunch payment"
    },
    {
      "id": "tx_def456",
      "timestamp": "2025-10-30T15:30:00Z",
      "from": "0x456def...",
      "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
      "amount": 200,
      "type": "single",
      "tx_hash": "0xdef456...",
      "status": "success",
      "memo": "Freelance work"
    }
  ]
}
```

**Query Parameters:**
- `limit` (optional): Maximum number of transactions (default: 50, max: 100)

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `alias_exists` | 409 | Alias already registered |
| `alias_not_found` | 404 | Alias does not exist |
| `invalid_alias_format` | 400 | Alias format invalid (must be @username) |
| `invalid_signature` | 401 | Cryptographic signature verification failed |
| `insufficient_funds` | 400 | User wallet has insufficient balance |
| `ambiguous_intent` | 400 | AI could not parse payment intent clearly |
| `missing_amount` | 400 | Payment amount not specified |
| `missing_recipient` | 400 | Payment recipient not specified |
| `blockchain_error` | 500 | Blockchain RPC error |
| `rate_limit_exceeded` | 429 | Too many requests |

**Standard Error Response:**
```json
{
  "error": {
    "code": "insufficient_funds",
    "message": "Wallet balance too low for transaction",
    "details": {
      "required": 50,
      "available": 25,
      "currency": "USD"
    }
  },
  "timestamp": "2025-10-31T12:00:00Z"
}
```

---

## Rate Limits

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
X-RateLimit-Reset: 1698757200
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

## WebSocket Support (Future)

**Coming Soon:** Real-time payment notifications

```javascript
// Future WebSocket endpoint
ws://api.bulut.app/ws/payments?address={USER_ADDRESS}

// Event types:
{
  "event": "payment_received",
  "data": { ... }
}
```

---

## SDK Examples

### JavaScript/TypeScript
```typescript
import { BulutClient } from '@bulut/sdk';

const client = new BulutClient({
  apiKey: process.env.BULUT_API_KEY,
  network: 'mainnet'
});

// Process command
const intent = await client.processCommand('Send $50 to @alice');

// Execute payment
const tx = await client.executePayment(intent, {
  signature: userSignature
});
```

### Python
```python
from bulut_sdk import BulutClient

client = BulutClient(
    api_key=os.environ['BULUT_API_KEY'],
    network='mainnet'
)

# Process command
intent = client.process_command('Send $50 to @alice')

# Execute payment
tx = client.execute_payment(intent, signature=user_signature)
```

---

## Testing

**Sandbox Environment:**
- Base URL: `https://api-sandbox.bulut.app/v1`
- Test alias: `@testuser` → `0xTEST...`
- No real funds required

**Test API Key:**
```
BULUT_TEST_API_KEY=blt_test_abc123xyz789
```

---

## Support

- **Documentation:** https://docs.bulut.app
- **API Status:** https://status.bulut.app
- **Discord:** https://discord.gg/bulut
- **Email:** dev@bulut.app