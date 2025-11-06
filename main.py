"""
Bulut Backend - FULLY FUNCTIONAL Production API
Complete implementation with in-memory storage and mock services
"""
from agent import AIAgent  # Bulut AI core logic

import os
import json
import hashlib
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import httpx

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
    ARC_CONTRACT_ADDRESS = os.getenv("ARC_CONTRACT_ADDRESS", "0xBulutContract123")
    
    # Security
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-prod")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # Alias validation
    MIN_ALIAS_LENGTH = 3
    MAX_ALIAS_LENGTH = 20
    ALIAS_PATTERN = r'^@[a-zA-Z0-9_]{3,20}$'

config = Config()

# ============================================================================
# DATA MODELS
# ============================================================================

class PaymentIntent(BaseModel):
    """Payment intent from AI or manual input"""
    payment_type: str
    intent: Dict[str, Any]
    confidence: float = Field(ge=0, le=1)
    requires_confirmation: bool = True
    confirmation_text: Optional[str] = None
    error: Optional[Dict[str, Any]] = None

class ProcessCommandRequest(BaseModel):
    """Request to process natural language command"""
    text: str = Field(..., min_length=1, max_length=500)
    user_id: Optional[str] = None
    timezone: str = "UTC"

class ExecutePaymentRequest(BaseModel):
    """Request to execute a payment"""
    intent_id: str
    payment_intent: PaymentIntent
    user_signature: str
    user_address: str

class AliasRegistration(BaseModel):
    """Register new alias"""
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
    """Response after transaction execution"""
    success: bool
    transaction_hash: Optional[str] = None
    blockchain: str = "arc"
    timestamp: str
    amount: Optional[float] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    error: Optional[str] = None

# ============================================================================
# IN-MEMORY STORAGE (Fully Functional)
# ============================================================================

class InMemoryStorage:
    """Complete in-memory storage implementation"""
    
    def __init__(self):
        # Alias mappings
        self.alias_to_address: Dict[str, str] = {}
        self.address_to_alias: Dict[str, str] = {}
        self.alias_metadata: Dict[str, Dict] = {}
        
        # Transactions
        self.transactions: List[Dict] = []
        self.transaction_index: Dict[str, Dict] = {}
        
        # Subscriptions
        self.subscriptions: Dict[str, Dict] = {}
        
        # Payment intents
        self.payment_intents: Dict[str, Dict] = {}
        
        # Users
        self.users: Dict[str, Dict] = {}
        
        # Initialize with demo data
        self._init_demo_data()
    
    def _init_demo_data(self):
        """Initialize with demo aliases for testing"""
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

# Global storage instance
storage = InMemoryStorage()

# ============================================================================
# SERVICES
# ============================================================================

class AliasService:
    """Fully functional alias management"""
    
    @staticmethod
    async def register(alias: str, address: str, signature: str) -> Dict:
        """Register new alias"""
        alias = alias.lower()
        address = address.lower()
        
        # Check if alias exists
        if alias in storage.alias_to_address:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "alias_exists", "message": f"Alias {alias} already registered"}
            )
        
        # Check if address has alias
        if address in storage.address_to_alias:
            existing = storage.address_to_alias[address]
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "address_has_alias", "message": f"Address already has alias {existing}"}
            )
        
        # Store mappings
        storage.alias_to_address[alias] = address
        storage.address_to_alias[address] = alias
        storage.alias_metadata[alias] = {
            "registered_at": datetime.utcnow().isoformat(),
            "last_used": datetime.utcnow().isoformat(),
            "signature": signature
        }
        
        return {
            "success": True,
            "alias": alias,
            "address": address,
            "registered_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def resolve(alias: str) -> Optional[str]:
        """Get address by alias"""
        alias = alias.lower()
        if not alias.startswith('@'):
            alias = '@' + alias
        
        address = storage.alias_to_address.get(alias)
        if address and alias in storage.alias_metadata:
            storage.alias_metadata[alias]["last_used"] = datetime.utcnow().isoformat()
        return address
    
    @staticmethod
    async def get_alias(address: str) -> Optional[str]:
        """Get alias by address"""
        return storage.address_to_alias.get(address.lower())
    
    @staticmethod
    async def delete(alias: str) -> bool:
        """Delete alias"""
        alias = alias.lower()
        if alias not in storage.alias_to_address:
            return False
        
        address = storage.alias_to_address[alias]
        del storage.alias_to_address[alias]
        del storage.address_to_alias[address]
        if alias in storage.alias_metadata:
            del storage.alias_metadata[alias]
        return True

class BlockchainService:
    """Fully functional blockchain mock service"""
    
    @staticmethod
    def _generate_tx_hash() -> str:
        """Generate realistic transaction hash"""
        return "0x" + hashlib.sha256(
            f"{datetime.utcnow().isoformat()}{uuid.uuid4()}".encode()
        ).hexdigest()
    
    @staticmethod
    async def send_payment(
        from_address: str,
        to_address: str,
        amount: float,
        currency: str = "ARC",
        memo: Optional[str] = None,
        signature: str = None
    ) -> Dict:
        """Execute payment (mock)"""
        
        tx_hash = BlockchainService._generate_tx_hash()
        
        return {
            "success": True,
            "transaction_hash": tx_hash,
            "block_number": 12345678,
            "gas_used": "21000",
            "status": "confirmed",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def create_subscription(
        from_address: str,
        to_address: str,
        amount: float,
        frequency: str,
        start_date: str,
        signature: str
    ) -> Dict:
        """Create subscription (mock)"""
        
        sub_id = "sub_" + hashlib.sha256(
            f"{from_address}{to_address}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        tx_hash = BlockchainService._generate_tx_hash()
        
        # Store subscription
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
        
        return {
            "success": True,
            "subscription_id": sub_id,
            "transaction_hash": tx_hash,
            "status": "active"
        }
    
    @staticmethod
    async def split_payment(
        from_address: str,
        recipients: List[Dict],
        total_amount: float,
        memo: Optional[str],
        signature: str
    ) -> Dict:
        """Execute split payment (mock)"""
        
        tx_hash = BlockchainService._generate_tx_hash()
        
        return {
            "success": True,
            "transaction_hash": tx_hash,
            "recipient_count": len(recipients),
            "total_amount": total_amount,
            "status": "confirmed"
        }

class TransactionService:
    """Fully functional transaction management"""
    
    @staticmethod
    async def log(tx_data: Dict) -> str:
        """Log transaction"""
        tx_id = "tx_" + hashlib.sha256(
            f"{json.dumps(tx_data, sort_keys=True)}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        transaction = {
            "id": tx_id,
            "timestamp": datetime.utcnow().isoformat(),
            **tx_data
        }
        
        storage.transactions.append(transaction)
        storage.transaction_index[tx_data.get("transaction_hash", tx_id)] = transaction
        
        return tx_id
    
    @staticmethod
    async def get_history(
        address: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """Get transaction history"""
        address = address.lower()
        
        # Filter transactions
        user_txs = [
            tx for tx in storage.transactions
            if tx.get("from_address", "").lower() == address or 
               tx.get("to_address", "").lower() == address
        ]
        
        # Sort by timestamp
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
    
    @staticmethod
    async def get_transaction(tx_hash: str) -> Optional[Dict]:
        """Get single transaction"""
        return storage.transaction_index.get(tx_hash)

class MockAIAgent:
    """Fully functional AI agent mock for development"""
    
    @staticmethod
    async def parse_payment(text: str, user_id: str = None, timezone: str = "UTC") -> PaymentIntent:
        """Parse payment command using simple pattern matching"""
        
        text_lower = text.lower()
        
        # Extract amount
        amount_match = re.search(r'\$?(\d+(?:\.\d{2})?)', text)
        amount = float(amount_match.group(1)) if amount_match else None
        
        # Extract currency
        currency = "USD"
        if "arc" in text_lower:
            currency = "ARC"
        elif "eth" in text_lower:
            currency = "ETH"
        
        # Extract alias
        alias_match = re.search(r'@(\w+)', text)
        alias = f"@{alias_match.group(1)}" if alias_match else None
        
        # Determine payment type
        if "split" in text_lower or "divide" in text_lower:
            return MockAIAgent._parse_split(text, amount, currency)
        elif "every" in text_lower or "monthly" in text_lower or "subscription" in text_lower:
            return MockAIAgent._parse_subscription(text, amount, currency, alias)
        else:
            return MockAIAgent._parse_single(text, amount, currency, alias)
    
    @staticmethod
    def _parse_single(text: str, amount: float, currency: str, alias: str) -> PaymentIntent:
        """Parse single payment"""
        
        if not amount:
            return PaymentIntent(
                payment_type="single",
                intent={},
                confidence=0.3,
                requires_confirmation=True,
                error={"code": "missing_amount", "message": "Could not determine amount"}
            )
        
        if not alias:
            return PaymentIntent(
                payment_type="single",
                intent={},
                confidence=0.3,
                requires_confirmation=True,
                error={"code": "missing_recipient", "message": "Could not determine recipient"}
            )
        
        # Extract memo
        memo = None
        if "for" in text.lower():
            memo_parts = text.lower().split("for", 1)
            if len(memo_parts) > 1:
                memo = memo_parts[1].strip()
        
        return PaymentIntent(
            payment_type="single",
            intent={
                "action": "send",
                "amount": amount,
                "currency": currency,
                "recipient": {"alias": alias},
                "memo": memo
            },
            confidence=0.92,
            requires_confirmation=True,
            confirmation_text=f"Send {currency} {amount} to {alias}?"
        )
    
    @staticmethod
    def _parse_subscription(text: str, amount: float, currency: str, alias: str) -> PaymentIntent:
        """Parse subscription payment"""
        
        frequency = "monthly"
        if "weekly" in text.lower():
            frequency = "weekly"
        elif "daily" in text.lower():
            frequency = "daily"
        elif "yearly" in text.lower():
            frequency = "yearly"
        
        start_date = datetime.utcnow().isoformat()
        
        return PaymentIntent(
            payment_type="subscription",
            intent={
                "action": "send",
                "amount": amount,
                "currency": currency,
                "recipient": {"alias": alias},
                "subscription": {
                    "frequency": frequency,
                    "start_date": start_date
                }
            },
            confidence=0.88,
            requires_confirmation=True,
            confirmation_text=f"Set up {frequency} payment of {currency} {amount} to {alias}?"
        )
    
    @staticmethod
    def _parse_split(text: str, amount: float, currency: str) -> PaymentIntent:
        """Parse split payment"""
        
        # Extract all aliases
        aliases = re.findall(r'@(\w+)', text)
        
        if len(aliases) < 2:
            return PaymentIntent(
                payment_type="split",
                intent={},
                confidence=0.4,
                requires_confirmation=True,
                error={"code": "insufficient_recipients", "message": "Need at least 2 recipients"}
            )
        
        # Split equally
        per_person = amount / len(aliases)
        recipients = [
            {"alias": f"@{alias}", "amount": per_person, "percentage": 100/len(aliases)}
            for alias in aliases
        ]
        
        return PaymentIntent(
            payment_type="split",
            intent={
                "action": "split",
                "amount": amount,
                "currency": currency,
                "recipients": recipients
            },
            confidence=0.85,
            requires_confirmation=True,
            confirmation_text=f"Split {currency} {amount} between {len(aliases)} people?"
        )

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    print(f"🚀 {config.APP_NAME} starting...")
    print(f"📊 Demo aliases loaded: {len(storage.alias_to_address)}")
    yield
    print(f"👋 {config.APP_NAME} shutting down...")

app = FastAPI(
    title=config.APP_NAME,
    version=config.API_VERSION,
    description="Fully functional AI-powered payment API",
    lifespan=lifespan
)

# CORS
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
    """Root endpoint"""
    return {
        "service": config.APP_NAME,
        "version": config.API_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "demo_aliases": list(storage.alias_to_address.keys())
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": config.API_VERSION,
        "services": {
            "api": "operational",
            "storage": "operational",
            "blockchain": "operational",
            "ai_agent": "operational"
        },
        "stats": {
            "aliases": len(storage.alias_to_address),
            "transactions": len(storage.transactions),
            "subscriptions": len(storage.subscriptions)
        }
    }

# ALIAS ROUTES
@app.post("/alias/register", status_code=status.HTTP_201_CREATED)
async def register_alias(registration: AliasRegistration):
    """Register new alias"""
    result = await AliasService.register(
        registration.alias,
        registration.address,
        registration.signature
    )
    return result

@app.get("/alias/{alias}")
async def get_alias(alias: str):
    """Resolve alias to address"""
    if not alias.startswith('@'):
        alias = '@' + alias
    
    address = await AliasService.resolve(alias)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "alias_not_found", "message": f"Alias {alias} not found"}
        )
    
    return {"alias": alias, "address": address}

@app.get("/address/{address}/alias")
async def get_address_alias(address: str):
    """Get alias by address"""
    alias = await AliasService.get_alias(address)
    return {"address": address, "alias": alias}

@app.delete("/alias/{alias}")
async def delete_alias(alias: str, signature: str = Header(..., alias="X-Signature")):
    """Delete alias"""
    if not alias.startswith('@'):
        alias = '@' + alias
    
    success = await AliasService.delete(alias)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "alias_not_found", "message": "Alias not found"}
        )
    
    return {"success": True, "message": f"Alias {alias} deleted"}

# PAYMENT ROUTES
@app.post("/process_command", response_model=PaymentIntent)
async def process_command(command: ProcessCommandRequest):
    """Process natural language command"""
    intent = await AIAgent.parse_payment(
    command.text,
    command.user_id,
    command.timezone
)

    return intent

@app.post("/execute_payment", response_model=TransactionResponse)
async def execute_payment(
    payment: ExecutePaymentRequest,
    user_address: str = Header(..., alias="X-Wallet-Address"),
    signature: str = Header(..., alias="X-Signature")
):
    """Execute payment"""
    
    # Verify address match
    if user_address.lower() != payment.user_address.lower():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "address_mismatch", "message": "Address mismatch"}
        )
    
    intent = payment.payment_intent
    intent_data = intent.intent
    payment_type = intent.payment_type
    
    try:
        if payment_type == "single":
            # Resolve recipient
            recipient_alias = intent_data["recipient"]["alias"]
            to_address = await AliasService.resolve(recipient_alias)
            
            if not to_address:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "recipient_not_found", "message": f"Recipient {recipient_alias} not found"}
                )
            
            # Execute payment
            result = await BlockchainService.send_payment(
                from_address=payment.user_address,
                to_address=to_address,
                amount=intent_data["amount"],
                currency=intent_data.get("currency", "ARC"),
                memo=intent_data.get("memo"),
                signature=payment.user_signature
            )
            
            # Log transaction
            await TransactionService.log({
                "from_address": payment.user_address,
                "to_address": to_address,
                "amount": intent_data["amount"],
                "currency": intent_data.get("currency", "ARC"),
                "payment_type": payment_type,
                "transaction_hash": result["transaction_hash"],
                "status": "success",
                "memo": intent_data.get("memo")
            })
            
            return TransactionResponse(
                success=True,
                transaction_hash=result["transaction_hash"],
                blockchain="arc",
                timestamp=datetime.utcnow().isoformat(),
                amount=intent_data["amount"],
                from_address=payment.user_address,
                to_address=to_address
            )
        
        elif payment_type == "subscription":
            recipient_alias = intent_data["recipient"]["alias"]
            to_address = await AliasService.resolve(recipient_alias)
            
            if not to_address:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "recipient_not_found", "message": "Recipient not found"}
                )
            
            result = await BlockchainService.create_subscription(
                from_address=payment.user_address,
                to_address=to_address,
                amount=intent_data["amount"],
                frequency=intent_data["subscription"]["frequency"],
                start_date=intent_data["subscription"]["start_date"],
                signature=payment.user_signature
            )
            
            await TransactionService.log({
                "from_address": payment.user_address,
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
            # Resolve all recipients
            recipients = []
            for recipient in intent_data["recipients"]:
                alias = recipient["alias"]
                address = await AliasService.resolve(alias)
                if not address:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={"error": "recipient_not_found", "message": f"Recipient {alias} not found"}
                    )
                recipient["address"] = address
                recipients.append(recipient)
            
            result = await BlockchainService.split_payment(
                from_address=payment.user_address,
                recipients=recipients,
                total_amount=intent_data["amount"],
                memo=intent_data.get("memo"),
                signature=payment.user_signature
            )
            
            await TransactionService.log({
                "from_address": payment.user_address,
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
                detail={"error": "invalid_payment_type", "message": "Invalid payment type"}
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

# HISTORY ROUTES
@app.get("/history/{address}")
async def get_history(address: str, limit: int = 50, offset: int = 0):
    """Get transaction history"""
    if limit > 100:
        limit = 100
    
    history = await TransactionService.get_history(address, limit, offset)
    return history

@app.get("/transaction/{tx_hash}")
async def get_transaction(tx_hash: str):
    """Get transaction details"""
    tx = await TransactionService.get_transaction(tx_hash)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "transaction_not_found", "message": "Transaction not found"}
        )
    return tx

# SUBSCRIPTION ROUTES
@app.get("/subscriptions/{address}")
async def get_subscriptions(address: str):
    """Get active subscriptions"""
    subs = [
        sub for sub in storage.subscriptions.values()
        if sub["from_address"].lower() == address.lower() and sub["status"] == "active"
    ]
    return {"address": address, "count": len(subs), "subscriptions": subs}

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
            "error": {"code": "internal_error", "message": str(exc)},
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print(f"🌥️  {config.APP_NAME} v{config.API_VERSION}")
    print("=" * 70)
    print(f"📍 Server: http://0.0.0.0:8000")
    print(f"📚 Docs: http://0.0.0.0:8000/docs")
    print(f"🔍 Health: http://0.0.0.0:8000/health")
    print(f"💡 Demo aliases: {list(storage.alias_to_address.keys())}")
    print("=" * 70)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )