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

from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

# --- ARQUITECTURA LIMPIA ---
try:
    from agent import parse_payment_command
except ImportError:
    print(" CRITICAL: agent.py not found. AI endpoints will fail.")
    parse_payment_command = None

try:
    from blockchain_service import BlockchainService
except ImportError:
    print(" CRITICAL: blockchain_service.py not found. Blockchain endpoints will fail.")
    BlockchainService = None 

try:
    from circle_service import CircleService
except ImportError:
    print(" CRITICAL: circle_service.py not found. Circle functionality will fail.")
    CircleService = None

try:
    from utils import normalize_address
except ImportError:
    def normalize_address(address: str, is_alias: bool = False) -> str:
        if not isinstance(address, str): return ""
        if is_alias: return address.lower().lstrip('@')
        return address.lower().lstrip('0x')


# ============================================================================
# CONFIGURATION
# ============================================================================
class Config:
    API_VERSION = "v1"
    APP_NAME = "Bulut API"
    ENVIRONMENT = os.getenv("APP_ENV", "development")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT") or 8000)
    
    # AI CONFIG
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_API_URL = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com/v1")
    AI_AGENT_API_KEY = os.getenv("AIMLAPI_KEY", "")
    
    # BLOCKCHAIN CONFIG
    ARC_RPC_URL = os.getenv("ARC_RPC_URL", "https://mainnet.arc.network")
    ARC_EXPLORER_URL = os.getenv("ARC_EXPLORER_URL", "https://explorer.arc.network")
    ARC_CONTRACT_ADDRESS = os.getenv("ARC_CONTRACT_ADDRESS", "0xBulutContract123")
    ARC_CHAIN_ID = int(os.getenv("ARC_CHAIN_ID", "4224"))
    
    ARC_USDC_ADDRESS = os.getenv("ARC_USDC_ADDRESS", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    
    # CIRCLE CONFIGURATION
    CIRCLE_API_KEY = os.getenv("CIRCLE_API_KEY", "")
    CIRCLE_BASE_URL = os.getenv("CIRCLE_BASE_URL", "https://api.circle.com/v1/w3s")
    CIRCLE_ENTITY_ID = os.getenv("CIRCLE_ENTITY_ID", "")
    
    
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_API_URL = os.getenv("ELEVENLABS_API_URL", "https://api.elevenlabs.io/v1")
    
    AI_AGENT_URL = os.getenv("AI_AGENT_URL", "http://localhost:8001")
    
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bulut.db")
    
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    MIN_ALIAS_LENGTH = 3
    MAX_ALIAS_LENGTH = 20
    ALIAS_PATTERN = r'^@[a-zA-Z0-9_]{3,20}$'
    
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
    
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        return {
            "app_name": cls.APP_NAME,
            "version": cls.API_VERSION,
            "environment": cls.ENVIRONMENT,
            "debug": cls.DEBUG,
            "anthropic_configured": bool(cls.ANTHROPIC_API_KEY),
            "ai_agent_configured": bool(cls.AI_AGENT_API_KEY),
            "circle_configured": bool(cls.CIRCLE_API_KEY and cls.CIRCLE_ENTITY_ID),
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
        return normalize_address(v, is_alias=True)
    
    @validator('address')
    def validate_address(cls, v):
        if not v.startswith('0x'):
            raise ValueError("Address must start with 0x")
        return normalize_address(v) # Normalización

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
            # Normalización al guardar data demo
            normalized_alias = normalize_address(alias, is_alias=True)
            normalized_address = normalize_address(address)
            self.alias_to_address[normalized_alias] = normalized_address
            self.address_to_alias[normalized_address] = normalized_alias
            self.alias_metadata[normalized_alias] = {
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
        
        try:
            message_to_sign = f"Estoy registrando el alias @{alias} para la dirección {address}"
            message_hash = encode_defunct(text=message_to_sign)
            recovered_address = Account.recover_message(message_hash, signature=signature)
            
            if normalize_address(recovered_address) != address:
                raise ValueError("La firma no coincide con la dirección.")

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail={"error": "invalid_signature", "message": str(e)}
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail={"error": "signature_error", "message": f"Error al procesar la firma: {str(e)}"}
            )

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
        normalized_alias = normalize_address(alias, is_alias=True)
        return storage.alias_to_address.get(normalized_alias)

    @staticmethod
    async def get_alias(address: str) -> Optional[str]:
        normalized_address = normalize_address(address)
        return storage.address_to_alias.get(normalized_address)

    @staticmethod
    async def delete(alias: str, requesting_address: str) -> bool:
        normalized_alias = normalize_address(alias, is_alias=True)
        normalized_requesting_address = normalize_address(requesting_address)

        if normalized_alias not in storage.alias_to_address:
            return False
            
        registered_address = storage.alias_to_address[normalized_alias]
        
        if registered_address != normalized_requesting_address:
            return False 

        del storage.alias_to_address[normalized_alias]
        del storage.address_to_alias[registered_address]
        return True

    @staticmethod
    async def search(query: str, limit: int = 10) -> List[Dict]:
        query = normalize_address(query, is_alias=True)

        matches = []
        for alias, address in storage.alias_to_address.items():
            if alias.startswith(query): # El alias ya está en minúsculas y sin @
                matches.append({"alias": '@' + alias, "address": address})
            
            if len(matches) >= limit:
                break
        
        return matches

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
        address = normalize_address(address)
        user_txs = [tx for tx in storage.transactions if tx.get("from_address", "") == address or 
                            tx.get("to_address", "") == address]
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
transaction_service = TransactionService()

if CircleService:
    circle_service = CircleService(
        api_key=config.CIRCLE_API_KEY,
        base_url=config.CIRCLE_BASE_URL,
        entity_id=config.CIRCLE_ENTITY_ID
    )
else:
    circle_service = None

if BlockchainService:
    blockchain_service = BlockchainService(
        rpc_url=config.ARC_RPC_URL, 
        usdc_contract_address=config.ARC_USDC_ADDRESS, 
        storage_instance=storage,
        circle_service=circle_service
    )
else:
    blockchain_service = None

ai_agent = None 
if parse_payment_command:
    print(" AI parsing function is available.")
else:
    print(" AI parsing function is missing.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f" {config.APP_NAME} started")
    yield
    print(f" {config.APP_NAME} stopped")

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
        services={"api": "operational", "blockchain": "ok" if blockchain_service else "failed", "circle": "ok" if circle_service and circle_service.is_real else "simulated"},
        stats={"aliases": len(storage.alias_to_address), "transactions": len(storage.transactions)})

# --- ALIAS MANAGEMENT ROUTES ---
@app.post("/alias/register", status_code=201)
async def register_alias(registration: AliasRegistration):
    return await alias_service.register(registration.alias, registration.address, registration.signature)

@app.get("/alias/{alias}")
async def get_alias(alias: str):
    address = await alias_service.resolve(alias)
    if not address:
        raise HTTPException(404, detail={"error": "alias_not_found"})
    return {"alias": '@' + normalize_address(alias, is_alias=True), "address": address}

@app.get("/address/{address}/alias")
async def get_address_alias(address: str):
    alias = await alias_service.get_alias(address)
    if not alias:
        raise HTTPException(404, detail={"error": "alias_not_found"})
    return {"address": normalize_address(address), "alias": '@' + alias}

@app.get("/alias/search")
async def search_aliases(query: str, limit: int = 10):
    if len(query) < 2:
        return []
    
    aliases = await alias_service.search(query, limit)
    return aliases

@app.delete("/alias/{alias}")
async def delete_alias(alias: str, user_address: str = Header(..., alias="X-Wallet-Address")):
    
    success = await alias_service.delete(alias, user_address)
    if not success:
        raise HTTPException(403, detail={"error": "alias_not_found_or_not_owner"})
    return {"success": True, "message": f"Alias @{alias} deleted"}

# --- TRANSACTION & HISTORY ROUTES ---
@app.get("/history/{address}")
async def get_history(address: str, limit: int = 50, offset: int = 0):
    return await transaction_service.get_history(address, limit, offset)

@app.get("/transaction/{tx_hash}")
async def get_transaction(tx_hash: str):
    tx = await transaction_service.get_transaction(tx_hash)
    if not tx:
        raise HTTPException(404, detail={"error": "transaction_not_found"})
    return tx

# --- ERROR HANDLERS ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content={"error": exc.detail, "timestamp": datetime.utcnow().isoformat()})

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500,
                        content={"error": {"code": "internal_error", "message": str(exc)},
                                 "timestamp": datetime.utcnow().isoformat()})

# --- AI & PAYMENT EXECUTION ---
@app.post("/process_command", response_model=PaymentIntent)
async def process_bulut_command(command: ProcessCommandRequest):
    if not parse_payment_command:
        raise HTTPException(status_code=503, detail="AI agent is not configured or agent.py is missing.")
    
    try:
        intent_data = await parse_payment_command(
            text=command.text,
            api_key=config.AI_AGENT_API_KEY,
            user_id=command.user_id,
            timezone=command.timezone
        )
        
        if intent_data.get("error"):
            print(f" AI Parsing Error: {intent_data.get('error')}")
            raise HTTPException(status_code=400, detail=intent_data.get("error"))

        intent_id = "intent_" + uuid.uuid4().hex[:16]
        storage.payment_intents[intent_id] = intent_data
        
        return PaymentIntent(**intent_data)

    except Exception as e:
        print(f" /process_command Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing command: {str(e)}")


@app.post("/execute_payment", response_model=TransactionResponse)
async def execute_bulut_payment(request: ExecutePaymentRequest, user_address_header: str = Header(..., alias="X-Wallet-Address")):
    if not blockchain_service:
        raise HTTPException(status_code=503, detail="Blockchain service is not initialized.")

    intent = request.payment_intent
    payment_type = intent.payment_type
    intent_data = intent.intent
    
    normalized_user_address = normalize_address(request.user_address)
    normalized_header_address = normalize_address(user_address_header)
    
    if normalized_header_address != normalized_user_address:
        raise HTTPException(status_code=403, detail="Header address does not match request body address (Origin address).")

    try:
        to_address = None
        if "recipient" in intent_data and "alias" in intent_data["recipient"]:
            alias = intent_data["recipient"]["alias"] # Alias ya está normalizado por agent.py/pydantic
            to_address = await alias_service.resolve(alias)
            if not to_address:
                raise HTTPException(status_code=404, detail={"error": "recipient_not_found", "alias": alias})
            intent_data["recipient"]["address"] = to_address
        
        tx_result = {}
        
        if payment_type == "single":
            tx_result = await blockchain_service.send_payment(
                from_address=normalized_user_address,
                to_address=to_address,
                amount=intent_data.get("amount", 0.0),
                currency=intent_data.get("currency", "USDC"),
                memo=intent_data.get("memo"),
                signature=request.user_signature
            )
        
        elif payment_type == "subscription":
            tx_result = await blockchain_service.create_subscription(
                from_address=normalized_user_address,
                to_address=to_address,
                amount=intent_data.get("amount", 0.0),
                frequency=intent_data.get("subscription", {}).get("frequency", "monthly"),
                start_date=intent_data.get("subscription", {}).get("start_date", datetime.utcnow().isoformat()),
                signature=request.user_signature
            )
        
        elif payment_type == "split":
            tx_result = await blockchain_service.split_payment(
                from_address=normalized_user_address,
                recipients=intent_data.get("recipients", []),
                total_amount=intent_data.get("amount", 0.0),
                memo=intent_data.get("memo"),
                signature=request.user_signature
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown payment type: {payment_type}")

        if not tx_result.get("success"):
            raise Exception(tx_result.get("error", "Blockchain transaction failed"))

        log_data = {
            "transaction_hash": tx_result.get("transaction_hash"),
            "from_address": normalized_user_address,
            "to_address": normalize_address(to_address) if to_address else "contract",
            "amount": intent_data.get("amount"),
            "currency": intent_data.get("currency", "ARC"),
            "payment_type": payment_type,
            "status": "success",
            "memo": intent_data.get("memo")
        }
        await transaction_service.log(log_data)
        
        return TransactionResponse(
            success=True,
            transaction_hash=tx_result.get("transaction_hash"),
            timestamp=tx_result.get("timestamp", datetime.utcnow().isoformat()),
            amount=intent_data.get("amount"),
            from_address=request.user_address,
            to_address=to_address,
            explorer_url=tx_result.get("explorer_url")
        )

    except Exception as e:
        print(f"❌ /execute_payment Error: {str(e)}")
        return TransactionResponse(
            success=False,
            timestamp=datetime.utcnow().isoformat(),
            error=str(e)
        )

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)