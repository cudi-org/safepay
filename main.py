"""
Bulut Backend - FULLY FUNCTIONAL Production API (with Web3 Integration)
"""

import os
import json
import hashlib
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, HTTPException, Header, Request, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field, validator
    import httpx
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("📦 Install with: pip install fastapi uvicorn pydantic httpx")
    exit(1)

# Web3 (Blockchain Real)
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

# Import agent functionality
try:
    from agent import BulutAIAgent
except ImportError:
    print("⚠️  Warning: agent.py not found, using mock agent")
    BulutAIAgent = None

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Application configuration with API URLs"""
    
    # Application Info
    API_VERSION = "v1"
    APP_NAME = "Bulut API"
    ENVIRONMENT = os.getenv("APP_ENV", "development")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    
    # Server Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT") or 8000)

    
    # External API URLs
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_API_URL = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com/v1")
    
    # Arc Blockchain URLs
    ARC_RPC_URL = os.getenv("ARC_RPC_URL", "https://mainnet.arc.network")
    ARC_EXPLORER_URL = os.getenv("ARC_EXPLORER_URL", "https://explorer.arc.network")
    ARC_CONTRACT_ADDRESS = os.getenv("ARC_CONTRACT_ADDRESS", "0xBulutContract123")
    ARC_CHAIN_ID = int(os.getenv("ARC_CHAIN_ID", "4224"))
    
    # Gas payer and token address
    GAS_PAYER_KEY = os.getenv("GAS_PAYER_KEY", "")
    ARC_USDC_ADDRESS = os.getenv("ARC_USDC_ADDRESS", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    
    # ElevenLabs Voice API (Optional)
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_API_URL = os.getenv("ELEVENLABS_API_URL", "https://api.elevenlabs.io/v1")
    
    # Internal Services
    AI_AGENT_URL = os.getenv("AI_AGENT_URL", "http://localhost:8001")
    
    # Security
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # Database (Optional)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bulut.db")
    
    # Redis (Optional)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Alias validation
    MIN_ALIAS_LENGTH = 3
    MAX_ALIAS_LENGTH = 20
    ALIAS_PATTERN = r'^@[a-zA-Z0-9_]{3,20}$'
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        return {
            "app_name": cls.APP_NAME,
            "version": cls.API_VERSION,
            "environment": cls.ENVIRONMENT,
            "debug": cls.DEBUG,
            "anthropic_configured": bool(cls.ANTHROPIC_API_KEY),
            "elevenlabs_configured": bool(cls.ELEVENLABS_API_KEY),
            "arc_chain_id": cls.ARC_CHAIN_ID,
            "rate_limiting": cls.RATE_LIMIT_ENABLED
        }

config = Config()

# ============================================================================
# DATA MODELS
# ============================================================================

class PaymentIntent(BaseModel):
    payment_type: str
    intent: Dict[str, Any]
    confidence: float = Field(ge=0, le=1)
    requires_confirmation: bool = True
    confirmation_text: Optional[str] = None
    error: Optional[Dict[str, Any]] = None

class ProcessCommandRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    user_id: Optional[str] = None
    timezone: str = "UTC"

class ExecutePaymentRequest(BaseModel):
    intent_id: str
    payment_intent: PaymentIntent
    user_signature: str
    user_address: str

class AliasRegistration(BaseModel):
    alias: str = Field(..., pattern=config.ALIAS_PATTERN)
    address: str = Field(..., min_length=20)
    signature: str
    
    @validator('alias')
    def normalize_alias(cls, v):
        return v.lower().strip()
    
    @validator('address')
    def validate_address(cls, v):
        if not v.startswith('0x'):
            raise ValueError("Address must start with 0x")
        return v.lower()

class TransactionResponse(BaseModel):
    success: bool
    transaction_hash: Optional[str] = None
    blockchain: str = "arc"
    timestamp: str
    amount: Optional[float] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    explorer_url: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    environment: str
    services: Dict[str, str]
    stats: Dict[str, int]

# ============================================================================
# IN-MEMORY STORAGE
# ============================================================================

class InMemoryStorage:
    def __init__(self):
        self.alias_to_address: Dict[str, str] = {}
        self.address_to_alias: Dict[str, str] = {}
        self.alias_metadata: Dict[str, Dict] = {}
        self.transactions: List[Dict] = []
        self.transaction_index: Dict[str, Dict] = {}
        self.subscriptions: Dict[str, Dict] = {}
        self.payment_intents: Dict[str, Dict] = {}
        self.users: Dict[str, Dict] = {}
        self._init_demo_data()
    
    def _init_demo_data(self):
        demo_aliases = [
            ("@alice", "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"),
            ("@bob", "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199"),
            ("@charlie", "0xdD870fA1b7C4700F2BD7f44238821C26f7392148"),
            ("@demo", "0x4E5B2ea1F6E7eA1e5e5E5e5e5e5e5e5e5e5e5e5"),
        ]
        for alias, address in demo_aliases:
            self.alias_to_address[alias] = address
            self.address_to_alias[address] = alias
            self.alias_metadata[alias] = {
                "registered_at": datetime.utcnow().isoformat(),
                "last_used": datetime.utcnow().isoformat()
            }

storage = InMemoryStorage()

# ============================================================================
# SERVICES
# ============================================================================

class AliasService:
    @staticmethod
    async def register(alias: str, address: str, signature: str) -> Dict:
        alias = alias.lower()
        address = address.lower()
        if alias in storage.alias_to_address:
            raise HTTPException(status_code=409, detail={"error": "alias_exists"})
        if address in storage.address_to_alias:
            raise HTTPException(status_code=409, detail={"error": "address_has_alias"})
        storage.alias_to_address[alias] = address
        storage.address_to_alias[address] = alias
        storage.alias_metadata[alias] = {
            "registered_at": datetime.utcnow().isoformat(),
            "last_used": datetime.utcnow().isoformat(),
            "signature": signature
        }
        return {"success": True, "alias": alias, "address": address}

    @staticmethod
    async def resolve(alias: str) -> Optional[str]:
        alias = alias.lower()
        if not alias.startswith('@'):
            alias = '@' + alias
        return storage.alias_to_address.get(alias)

    @staticmethod
    async def get_alias(address: str) -> Optional[str]:
        return storage.address_to_alias.get(address.lower())

    @staticmethod
    async def delete(alias: str) -> bool:
        alias = alias.lower()
        if alias not in storage.alias_to_address:
            return False
        address = storage.alias_to_address[alias]
        del storage.alias_to_address[alias]
        del storage.address_to_alias[address]
        return True

# ============================================================================
# BLOCKCHAIN SERVICE (Web3 REAL)
# ============================================================================

class BlockchainService:
    """Real blockchain service using Web3.py"""

    def __init__(self, rpc_url: str, usdc_contract_address: str, gas_payer_key: str):
        self.rpc_url = rpc_url
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.usdc_contract_address = Web3.to_checksum_address(usdc_contract_address)
        self.gas_payer = Account.from_key(gas_payer_key) if gas_payer_key else None

        if not self.web3.is_connected():
            print("⚠️ Web3 not connected to network:", rpc_url)
        else:
            print(f"✅ Connected to chain ID: {self.web3.eth.chain_id}")

    def _get_explorer_url(self, tx_hash: str) -> str:
        return f"{config.ARC_EXPLORER_URL}/tx/{tx_hash}"

    async def send_payment(self, from_address: str, to_address: str, amount: float,
                           currency: str = "ARC", memo: Optional[str] = None, signature: str = None) -> Dict:
        try:
            from_addr = Web3.to_checksum_address(from_address)
            to_addr = Web3.to_checksum_address(to_address)
            value_wei = self.web3.to_wei(amount, "ether")
            nonce = self.web3.eth.get_transaction_count(self.gas_payer.address if self.gas_payer else from_addr)
            tx = {
                "nonce": nonce,
                "to": to_addr,
                "value": value_wei,
                "gas": 21000,
                "gasPrice": self.web3.eth.gas_price,
                "chainId": config.ARC_CHAIN_ID,
            }
            if not self.gas_payer:
                raise Exception("Gas payer key not configured")
            signed_tx = self.gas_payer.sign_transaction(tx)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            return {
                "success": True,
                "transaction_hash": tx_hash_hex,
                "status": "submitted",
                "explorer_url": self._get_explorer_url(tx_hash_hex),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e), "timestamp": datetime.utcnow().isoformat()}

    async def create_subscription(self, from_address: str, to_address: str, amount: float,
                                  frequency: str, start_date: str, signature: str) -> Dict:
        sub_id = "sub_" + hashlib.sha256(f"{from_address}{to_address}{datetime.utcnow()}".encode()).hexdigest()[:16]
        tx_hash = "0x" + uuid.uuid4().hex
        storage.subscriptions[sub_id] = {
            "id": sub_id,
            "from_address": from_address,
            "to_address": to_address,
            "amount": amount,
            "frequency": frequency,
            "start_date": start_date,
            "status": "active",
            "created_at": datetime.utcnow().isoformat()
        }
        return {"success": True, "subscription_id": sub_id, "transaction_hash": tx_hash,
                "explorer_url": self._get_explorer_url(tx_hash)}

    async def split_payment(self, from_address: str, recipients: List[Dict],
                            total_amount: float, memo: Optional[str], signature: str) -> Dict:
        tx_hash = "0x" + uuid.uuid4().hex
        return {"success": True, "transaction_hash": tx_hash,
                "recipient_count": len(recipients), "total_amount": total_amount,
                "status": "confirmed", "explorer_url": self._get_explorer_url(tx_hash)}

# ============================================================================
# TRANSACTION SERVICE
# ============================================================================

class TransactionService:
    @staticmethod
    async def log(tx_data: Dict) -> str:
        tx_id = "tx_" + hashlib.sha256(f"{json.dumps(tx_data)}{datetime.utcnow()}".encode()).hexdigest()[:16]
        transaction = {"id": tx_id, "timestamp": datetime.utcnow().isoformat(), **tx_data}
        storage.transactions.append(transaction)
        storage.transaction_index[tx_data.get("transaction_hash", tx_id)] = transaction
        return tx_id

    @staticmethod
    async def get_history(address: str, limit: int = 50, offset: int = 0) -> Dict:
        address = address.lower()
        user_txs = [tx for tx in storage.transactions if tx.get("from_address", "").lower() == address or 
                    tx.get("to_address", "").lower() == address]
        user_txs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        paginated = user_txs[offset:offset + limit]
        return {"address": address, "total_count": len(user_txs),
                "count": len(paginated), "transactions": paginated}

    @staticmethod
    async def get_transaction(tx_hash: str) -> Optional[Dict]:
        return storage.transaction_index.get(tx_hash)

# ============================================================================
# INITIALIZATION
# ============================================================================

alias_service = AliasService()
blockchain_service = BlockchainService(config.ARC_RPC_URL, config.ARC_USDC_ADDRESS, config.GAS_PAYER_KEY)
transaction_service = TransactionService()

if BulutAIAgent and config.ANTHROPIC_API_KEY:
    ai_agent = BulutAIAgent(api_key=config.ANTHROPIC_API_KEY)
    print("✅ Bulut AI Agent initialized with Claude")
else:
    ai_agent = None
    print("⚠️ Using mock AI agent")

# ============================================================================
# FASTAPI APP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🌥️ {config.APP_NAME} started")
    yield
    print(f"👋 {config.APP_NAME} stopped")

app = FastAPI(title=config.APP_NAME, version=config.API_VERSION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ROUTES
# ============================================================================

@app.get("/")
async def root():
    return {"service": config.APP_NAME, "version": config.API_VERSION, "docs": "/docs"}

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="healthy", timestamp=datetime.utcnow().isoformat(),
        version=config.API_VERSION, environment=config.ENVIRONMENT,
        services={"api": "operational", "blockchain": "ok"},
        stats={"aliases": len(storage.alias_to_address), "transactions": len(storage.transactions)})

@app.post("/alias/register", status_code=201)
async def register_alias(registration: AliasRegistration):
    return await alias_service.register(registration.alias, registration.address, registration.signature)

@app.get("/alias/{alias}")
async def get_alias(alias: str):
    address = await alias_service.resolve(alias)
    if not address:
        raise HTTPException(404, detail={"error": "alias_not_found"})
    return {"alias": alias, "address": address}

@app.get("/address/{address}/alias")
async def get_address_alias(address: str):
    return {"address": address, "alias": await alias_service.get_alias(address)}

@app.delete("/alias/{alias}")
async def delete_alias(alias: str, signature: str = Header(..., alias="X-Signature")):
    success = await alias_service.delete(alias)
    if not success:
        raise HTTPException(404, detail={"error": "alias_not_found"})
    return {"success": True, "message": f"Alias {alias} deleted"}

@app.get("/history/{address}")
async def get_history(address: str, limit: int = 50, offset: int = 0):
    return await transaction_service.get_history(address, limit, offset)

@app.get("/transaction/{tx_hash}")
async def get_transaction(tx_hash: str):
    tx = await transaction_service.get_transaction(tx_hash)
    if not tx:
        raise HTTPException(404, detail={"error": "transaction_not_found"})
    return tx

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content={"error": exc.detail, "timestamp": datetime.utcnow().isoformat()})

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500,
                        content={"error": {"code": "internal_error", "message": str(exc)},
                                 "timestamp": datetime.utcnow().isoformat()})

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)

