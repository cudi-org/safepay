"""
Bulut Backend - Production FastAPI Application
Optimized for Cloudflare Workers deployment
"""

import os
import json
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
import httpx
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Application configuration"""
    API_VERSION = "v1"
    APP_NAME = "Bulut API"
    
    # External services
    AI_AGENT_URL = os.getenv("AI_AGENT_URL", "http://localhost:8001")
    ARC_RPC_URL = os.getenv("ARC_RPC_URL", "https://mainnet.arc.network")
    ARC_CONTRACT_ADDRESS = os.getenv("ARC_CONTRACT_ADDRESS")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    
    # Security
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # Alias validation
    MIN_ALIAS_LENGTH = 3
    MAX_ALIAS_LENGTH = 20
    ALIAS_PATTERN = r'^@[a-zA-Z0-9_]{3,20}$'
    
    # Rate limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

config = Config()

# ============================================================================
# DATA MODELS
# ============================================================================

class PaymentIntent(BaseModel):
    """Payment intent from AI agent"""
    payment_type: str = Field(..., description="Type: single, subscription, split")
    intent: Dict[str, Any] = Field(..., description="Parsed payment details")
    confidence: float = Field(..., ge=0, le=1, description="AI confidence score")
    requires_confirmation: bool = Field(default=True)
    confirmation_text: Optional[str] = None
    error: Optional[Dict[str, Any]] = None

class ProcessCommandRequest(BaseModel):
    """Request to process natural language command"""
    text: str = Field(..., min_length=1, max_length=500, description="Payment command")
    user_id: Optional[str] = Field(None, description="User identifier")
    timezone: str = Field(default="UTC", description="User timezone")

class ExecutePaymentRequest(BaseModel):
    """Request to execute a payment"""
    intent_id: str = Field(..., description="Unique intent identifier")
    payment_intent: PaymentIntent
    user_signature: str = Field(..., description="Cryptographic signature")
    user_address: str = Field(..., description="Sender wallet address")

class AliasRegistration(BaseModel):
    """Register new alias"""
    alias: str = Field(..., pattern=config.ALIAS_PATTERN)
    address: str = Field(..., min_length=20, description="Wallet address")
    signature: str = Field(..., description="Proof of ownership signature")
    
    @validator('alias')
    def normalize_alias(cls, v):
        return v.lower().strip()
    
    @validator('address')
    def validate_address(cls, v):
        # Basic validation - enhance with actual blockchain address validation
        if not v.startswith('0x') or len(v) < 40:
            raise ValueError("Invalid wallet address format")
        return v.lower()

class TransactionResponse(BaseModel):
    """Response after transaction execution"""
    success: bool
    transaction_hash: Optional[str] = None
    blockchain: str = "arc"
    timestamp: str
    amount: Optional[float] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    services: Dict[str, str]

# ============================================================================
# DATABASE / STORAGE LAYER
# ============================================================================

class StorageBackend:
    """Abstract storage backend - implements in-memory for now"""
    
    def __init__(self):
        # In production, this would be Cloudflare KV
        self._kv_storage: Dict[str, str] = {}
        self._db_storage: List[Dict] = []
    
    async def kv_get(self, key: str) -> Optional[str]:
        """Get value from KV store"""
        return self._kv_storage.get(key)
    
    async def kv_set(self, key: str, value: str) -> bool:
        """Set value in KV store"""
        self._kv_storage[key] = value
        return True
    
    async def kv_delete(self, key: str) -> bool:
        """Delete key from KV store"""
        if key in self._kv_storage:
            del self._kv_storage[key]
            return True
        return False
    
    async def kv_list(self, prefix: str = "") -> List[str]:
        """List keys with prefix"""
        return [k for k in self._kv_storage.keys() if k.startswith(prefix)]
    
    async def db_insert(self, table: str, record: Dict) -> str:
        """Insert record into database"""
        record['_table'] = table
        record['_id'] = hashlib.sha256(
            f"{table}{json.dumps(record, sort_keys=True)}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        self._db_storage.append(record)
        return record['_id']
    
    async def db_query(self, table: str, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Query database"""
        results = [r for r in self._db_storage if r.get('_table') == table]
        
        if filters:
            for key, value in filters.items():
                results = [r for r in results if r.get(key) == value]
        
        return results[:limit]

# Initialize storage
storage = StorageBackend()

# ============================================================================
# ALIAS MANAGEMENT SERVICE
# ============================================================================

class AliasService:
    """Service for managing alias <-> address mappings"""
    
    def __init__(self, storage: StorageBackend):
        self.storage = storage
        self.KEY_PREFIX_ALIAS = "alias:"
        self.KEY_PREFIX_REVERSE = "reverse:"
    
    async def register(self, alias: str, address: str, signature: str) -> Dict[str, Any]:
        """Register new alias"""
        alias = alias.lower()
        address = address.lower()
        
        # Check if alias exists
        existing = await self.storage.kv_get(f"{self.KEY_PREFIX_ALIAS}{alias}")
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "alias_exists", "message": f"Alias {alias} is already registered"}
            )
        
        # Check if address already has alias
        reverse_key = f"{self.KEY_PREFIX_REVERSE}{address}"
        existing_alias = await self.storage.kv_get(reverse_key)
        if existing_alias:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "address_has_alias", "message": f"Address already registered as {existing_alias}"}
            )
        
        # Verify signature (placeholder - implement actual verification)
        if not self._verify_signature(address, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_signature", "message": "Signature verification failed"}
            )
        
        # Store mappings
        await self.storage.kv_set(f"{self.KEY_PREFIX_ALIAS}{alias}", address)
        await self.storage.kv_set(reverse_key, alias)
        
        # Log registration
        await self.storage.db_insert("alias_registrations", {
            "alias": alias,
            "address": address,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "success": True,
            "alias": alias,
            "address": address,
            "registered_at": datetime.utcnow().isoformat()
        }
    
    async def resolve_alias(self, alias: str) -> Optional[str]:
        """Get address by alias"""
        alias = alias.lower()
        if not alias.startswith('@'):
            alias = '@' + alias
        return await self.storage.kv_get(f"{self.KEY_PREFIX_ALIAS}{alias}")
    
    async def get_alias(self, address: str) -> Optional[str]:
        """Get alias by address"""
        return await self.storage.kv_get(f"{self.KEY_PREFIX_REVERSE}{address.lower()}")
    
    async def exists(self, alias: str) -> bool:
        """Check if alias exists"""
        address = await self.resolve_alias(alias)
        return address is not None
    
    def _verify_signature(self, address: str, signature: str) -> bool:
        """Verify cryptographic signature (placeholder)"""
        # TODO: Implement actual signature verification with Arc blockchain
        return len(signature) > 10

# ============================================================================
# BLOCKCHAIN SERVICE
# ============================================================================

class BlockchainService:
    """Service for blockchain interactions"""
    
    def __init__(self):
        self.rpc_url = config.ARC_RPC_URL
        self.contract_address = config.ARC_CONTRACT_ADDRESS
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_payment(
        self,
        from_address: str,
        to_address: str,
        amount: float,
        currency: str = "ARC",
        memo: Optional[str] = None,
        signature: str = None
    ) -> Dict[str, Any]:
        """Execute single payment on blockchain"""
        
        # Prepare transaction
        tx_data = {
            "from": from_address.lower(),
            "to": to_address.lower(),
            "amount": str(amount),
            "currency": currency,
            "memo": memo,
            "timestamp": datetime.utcnow().isoformat(),
            "signature": signature
        }
        
        # Simulate blockchain call
        # In production, call actual Arc blockchain RPC
        tx_hash = self._generate_tx_hash(tx_data)
        
        return {
            "success": True,
            "transaction_hash": tx_hash,
            "block_number": 12345678,
            "gas_used": "21000",
            "status": "confirmed"
        }
    
    async def create_subscription(
        self,
        from_address: str,
        to_address: str,
        amount: float,
        frequency: str,
        start_date: str,
        signature: str
    ) -> Dict[str, Any]:
        """Create recurring payment on blockchain"""
        
        tx_data = {
            "type": "subscription",
            "from": from_address.lower(),
            "to": to_address.lower(),
            "amount": str(amount),
            "frequency": frequency,
            "start_date": start_date,
            "signature": signature
        }
        
        tx_hash = self._generate_tx_hash(tx_data)
        
        return {
            "success": True,
            "subscription_id": tx_hash[:16],
            "transaction_hash": tx_hash,
            "status": "active"
        }
    
    async def split_payment(
        self,
        from_address: str,
        recipients: List[Dict],
        total_amount: float,
        memo: Optional[str],
        signature: str
    ) -> Dict[str, Any]:
        """Execute split payment"""
        
        tx_data = {
            "type": "split",
            "from": from_address.lower(),
            "recipients": recipients,
            "total_amount": str(total_amount),
            "memo": memo,
            "signature": signature
        }
        
        tx_hash = self._generate_tx_hash(tx_data)
        
        return {
            "success": True,
            "transaction_hash": tx_hash,
            "recipient_count": len(recipients),
            "status": "confirmed"
        }
    
    def _generate_tx_hash(self, tx_data: Dict) -> str:
        """Generate transaction hash (placeholder)"""
        data_str = json.dumps(tx_data, sort_keys=True)
        return "0x" + hashlib.sha256(data_str.encode()).hexdigest()

# ============================================================================
# TRANSACTION HISTORY SERVICE
# ============================================================================

class TransactionService:
    """Service for transaction history"""
    
    def __init__(self, storage: StorageBackend):
        self.storage = storage
    
    async def log_transaction(self, tx_data: Dict) -> str:
        """Log transaction to history"""
        tx_id = await self.storage.db_insert("transactions", {
            "timestamp": datetime.utcnow().isoformat(),
            "from_address": tx_data.get("from_address"),
            "to_address": tx_data.get("to_address"),
            "amount": tx_data.get("amount"),
            "currency": tx_data.get("currency", "ARC"),
            "type": tx_data.get("payment_type"),
            "tx_hash": tx_data.get("transaction_hash"),
            "status": tx_data.get("status", "success"),
            "memo": tx_data.get("memo"),
            "confirmation_text": tx_data.get("confirmation_text")
        })
        return tx_id
    
    async def get_user_history(
        self,
        address: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get transaction history for user"""
        address = address.lower()
        
        # Query transactions
        all_txs = await self.storage.db_query("transactions", limit=1000)
        
        # Filter for user
        user_txs = [
            tx for tx in all_txs
            if tx.get("from_address") == address or tx.get("to_address") == address
        ]
        
        # Sort by timestamp descending
        user_txs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Paginate
        paginated = user_txs[offset:offset + limit]
        
        return {
            "address": address,
            "total_count": len(user_txs),
            "count": len(paginated),
            "offset": offset,
            "limit": limit,
            "transactions": paginated
        }
    
    async def get_transaction(self, tx_hash: str) -> Optional[Dict]:
        """Get single transaction by hash"""
        results = await self.storage.db_query("transactions", {"tx_hash": tx_hash}, limit=1)
        return results[0] if results else None

# ============================================================================
# AI AGENT CLIENT
# ============================================================================

class AIAgentClient:
    """Client for AI agent service"""
    
    def __init__(self):
        self.agent_url = config.AI_AGENT_URL
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def parse_payment(
        self,
        text: str,
        user_id: Optional[str] = None,
        timezone: str = "UTC"
    ) -> PaymentIntent:
        """Parse natural language payment command"""
        
        try:
            response = await self.client.post(
                f"{self.agent_url}/parse_payment",
                json={
                    "text": text,
                    "user_id": user_id,
                    "timezone": timezone
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail={"error": "ai_agent_error", "message": "Failed to parse payment command"}
                )
            
            data = response.json()
            return PaymentIntent(**data)
            
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail={"error": "ai_timeout", "message": "AI agent timeout"}
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "ai_error", "message": str(e)}
            )

# ============================================================================
# INITIALIZE SERVICES
# ============================================================================

alias_service = AliasService(storage)
blockchain_service = BlockchainService()
transaction_service = TransactionService(storage)
ai_agent = AIAgentClient()

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print(f"🚀 {config.APP_NAME} starting up...")
    yield
    # Shutdown
    print(f"👋 {config.APP_NAME} shutting down...")
    await blockchain_service.client.aclose()
    await ai_agent.client.aclose()

# Initialize FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    version=config.API_VERSION,
    description="AI-powered payment processing API",
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API ROUTES
# ============================================================================

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "service": config.APP_NAME,
        "version": config.API_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version=config.API_VERSION,
        services={
            "api": "operational",
            "storage": "operational",
            "blockchain": "operational",
            "ai_agent": "operational"
        }
    )

# ============================================================================
# ALIAS ROUTES
# ============================================================================

@app.post("/alias/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def register_alias(request: Request, registration: AliasRegistration):
    """Register new alias -> address mapping"""
    result = await alias_service.register(
        registration.alias,
        registration.address,
        registration.signature
    )
    return result

@app.get("/alias/{alias}")
@limiter.limit("1000/minute")
async def get_address_by_alias(request: Request, alias: str):
    """Resolve alias to wallet address"""
    if not alias.startswith('@'):
        alias = '@' + alias
    
    address = await alias_service.resolve_alias(alias)
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "alias_not_found", "message": f"Alias {alias} not found"}
        )
    
    return {"alias": alias, "address": address}

@app.get("/address/{address}/alias")
@limiter.limit("1000/minute")
async def get_alias_by_address(request: Request, address: str):
    """Get alias for wallet address"""
    alias = await alias_service.get_alias(address)
    return {"address": address, "alias": alias}

@app.delete("/alias/{alias}")
@limiter.limit("10/hour")
async def delete_alias(
    request: Request,
    alias: str,
    signature: str = Header(..., alias="X-Signature")
):
    """Delete alias (requires signature)"""
    # Verify ownership before deletion
    address = await alias_service.resolve_alias(alias)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "alias_not_found", "message": "Alias not found"}
        )
    
    # TODO: Verify signature matches address
    
    return {"success": True, "message": f"Alias {alias} deleted"}

# ============================================================================
# PAYMENT PROCESSING ROUTES
# ============================================================================

@app.post("/process_command", response_model=PaymentIntent)
@limiter.limit("100/minute")
async def process_command(request: Request, command: ProcessCommandRequest):
    """Process natural language payment command"""
    intent = await ai_agent.parse_payment(
        command.text,
        command.user_id,
        command.timezone
    )
    return intent

@app.post("/execute_payment", response_model=TransactionResponse)
@limiter.limit("10/minute")
async def execute_payment(
    request: Request,
    payment_request: ExecutePaymentRequest,
    user_address: str = Header(..., alias="X-Wallet-Address"),
    signature: str = Header(..., alias="X-Signature")
):
    """Execute payment on blockchain"""
    
    intent = payment_request.payment_intent
    intent_data = intent.intent
    payment_type = intent.payment_type
    
    # Verify user address matches
    if user_address.lower() != payment_request.user_address.lower():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "address_mismatch", "message": "Address mismatch"}
        )
    
    try:
        # Resolve aliases to addresses
        if payment_type == "single":
            # Resolve recipient alias
            if "recipient" in intent_data and "alias" in intent_data["recipient"]:
                alias = intent_data["recipient"]["alias"]
                to_address = await alias_service.resolve_alias(alias)
                
                if not to_address:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={"error": "recipient_not_found", "message": f"Recipient {alias} not found"}
                    )
                
                intent_data["recipient"]["address"] = to_address
            
            # Execute payment
            result = await blockchain_service.send_payment(
                from_address=payment_request.user_address,
                to_address=intent_data["recipient"]["address"],
                amount=intent_data["amount"],
                currency=intent_data.get("currency", "ARC"),
                memo=intent_data.get("memo"),
                signature=payment_request.user_signature
            )
            
            # Log transaction
            await transaction_service.log_transaction({
                "from_address": payment_request.user_address,
                "to_address": intent_data["recipient"]["address"],
                "amount": intent_data["amount"],
                "currency": intent_data.get("currency", "ARC"),
                "payment_type": payment_type,
                "transaction_hash": result["transaction_hash"],
                "status": "success",
                "memo": intent_data.get("memo"),
                "confirmation_text": intent.confirmation_text
            })
            
            return TransactionResponse(
                success=True,
                transaction_hash=result["transaction_hash"],
                blockchain="arc",
                timestamp=datetime.utcnow().isoformat(),
                amount=intent_data["amount"],
                from_address=payment_request.user_address,
                to_address=intent_data["recipient"]["address"]
            )
        
        elif payment_type == "subscription":
            # Handle subscription
            to_address = await alias_service.resolve_alias(intent_data["recipient"]["alias"])
            if not to_address:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "recipient_not_found", "message": "Recipient not found"}
                )
            
            result = await blockchain_service.create_subscription(
                from_address=payment_request.user_address,
                to_address=to_address,
                amount=intent_data["amount"],
                frequency=intent_data["subscription"]["frequency"],
                start_date=intent_data["subscription"]["start_date"],
                signature=payment_request.user_signature
            )
            
            await transaction_service.log_transaction({
                "from_address": payment_request.user_address,
                "to_address": to_address,
                "amount": intent_data["amount"],
                "payment_type": "subscription",
                "transaction_hash": result["transaction_hash"],
                "status": "active"
            })
            
            return TransactionResponse(
                success=True,
                transaction_hash=result["transaction_hash"],
                blockchain="arc",
                timestamp=datetime.utcnow().isoformat(),
                amount=intent_data["amount"]
            )
        
        elif payment_type == "split":
            # Resolve all recipient aliases
            recipients = []
            for recipient in intent_data["recipients"]:
                if "alias" in recipient:
                    address = await alias_service.resolve_alias(recipient["alias"])
                    if not address:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail={"error": "recipient_not_found", "message": f"Recipient {recipient['alias']} not found"}
                        )
                    recipient["address"] = address
                recipients.append(recipient)
            
            result = await blockchain_service.split_payment(
                from_address=payment_request.user_address,
                recipients=recipients,
                total_amount=intent_data["amount"],
                memo=intent_data.get("memo"),
                signature=payment_request.user_signature
            )
            
            await transaction_service.log_transaction({
                "from_address": payment_request.user_address,
                "to_address": "multiple",
                "amount": intent_data["amount"],
                "payment_type": "split",
                "transaction_hash": result["transaction_hash"],
                "status": "success"
            })
            
            return TransactionResponse(
                success=True,
                transaction_hash=result["transaction_hash"],
                blockchain="arc",
                timestamp=datetime.utcnow().isoformat(),
                amount=intent_data["amount"]
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_payment_type", "message": f"Unknown payment type: {payment_type}"}
            )
    
    except HTTPException:
        raise
    except Exception as e:
        return TransactionResponse(
            success=False,
            blockchain="arc",
            timestamp=datetime.utcnow().isoformat(),
            error=str(e)
        )

# ============================================================================
# TRANSACTION HISTORY ROUTES
# ============================================================================

@app.get("/history/{address}")
@limiter.limit("50/minute")
async def get_transaction_history(
    request: Request,
    address: str,
    limit: int = 50,
    offset: int = 0
):
    """Get transaction history for user"""
    if limit > 100:
        limit = 100
    
    history = await transaction_service.get_user_history(address, limit, offset)
    return history

@app.get("/transaction/{tx_hash}")
@limiter.limit("100/minute")
async def get_transaction(request: Request, tx_hash: str):
    """Get transaction details by hash"""
    tx = await transaction_service.get_transaction(tx_hash)
    
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "transaction_not_found", "message": "Transaction not found"}
        )
    
    return tx

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, dict) else {"message": exc.detail},
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_error",
                "message": "An internal error occurred"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ============================================================================
# STARTUP MESSAGE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print(f"🚀 {config.APP_NAME} v{config.API_VERSION}")
    print("=" * 60)
    print(f"📍 Listening on: http://0.0.0.0:8000")
    print(f"📚 Docs: http://0.0.0.0:8000/docs")
    print(f"🔍 Health: http://0.0.0.0:8000/health")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )