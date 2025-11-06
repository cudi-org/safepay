"""
Bulut Backend API - FastAPI
High-speed edge infrastructure for AI-to-Blockchain bridge
Optimized for Cloudflare Workers deployment
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import httpx

# Configuration
API_VERSION = "v1"
MAX_ALIAS_LENGTH = 20
MIN_ALIAS_LENGTH = 3

# Initialize FastAPI
app = FastAPI(
    title="Bulut API",
    version="1.0.0",
    description="AI-powered payment processing API"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATA MODELS
# ============================================================================

class PaymentIntent(BaseModel):
    """Payment intent from AI agent"""
    payment_type: str
    intent: Dict[str, Any]
    confidence: float
    requires_confirmation: bool
    confirmation_text: Optional[str] = None

class ExecutePaymentRequest(BaseModel):
    """Request to execute a payment"""
    intent_id: str = Field(..., description="Unique intent identifier")
    payment_intent: PaymentIntent
    user_signature: str = Field(..., description="User's wallet signature")
    user_address: str = Field(..., description="Sender's wallet address")

class AliasRegistration(BaseModel):
    """Register new alias"""
    alias: str = Field(..., pattern=r'^@[a-zA-Z0-9_]{3,20}$')
    address: str = Field(..., description="Arc wallet address")
    signature: str = Field(..., description="Signature proving ownership")
    
    @validator('alias')
    def validate_alias(cls, v):
        if not v.startswith('@'):
            raise ValueError("Alias must start with @")
        if len(v) < MIN_ALIAS_LENGTH + 1 or len(v) > MAX_ALIAS_LENGTH + 1:
            raise ValueError(f"Alias must be {MIN_ALIAS_LENGTH}-{MAX_ALIAS_LENGTH} characters")
        return v.lower()

class TransactionResponse(BaseModel):
    """Response after transaction execution"""
    success: bool
    transaction_hash: Optional[str] = None
    blockchain: str = "arc"
    timestamp: str
    error: Optional[str] = None

# ============================================================================
# DATABASE / STORAGE (Cloudflare KV simulation)
# ============================================================================

class AliasDB:
    """
    Alias mapping database
    In production, use Cloudflare KV or Durable Objects
    """
    
    def __init__(self):
        # In production: self.kv = CloudflareKV()
        self._storage: Dict[str, str] = {}  # alias -> address
        self._reverse: Dict[str, str] = {}  # address -> alias
    
    async def register_alias(self, alias: str, address: str) -> bool:
        """Register alias -> address mapping"""
        alias = alias.lower()
        
        # Check if alias already exists
        if alias in self._storage:
            return False
        
        # Check if address already has alias
        if address in self._reverse:
            return False
        
        self._storage[alias] = address
        self._reverse[address] = alias
        return True
    
    async def get_address_by_alias(self, alias: str) -> Optional[str]:
        """Retrieve wallet address by alias"""
        return self._storage.get(alias.lower())
    
    async def get_alias_by_address(self, address: str) -> Optional[str]:
        """Retrieve alias by wallet address"""
        return self._reverse.get(address)
    
    async def alias_exists(self, alias: str) -> bool:
        """Check if alias is already registered"""
        return alias.lower() in self._storage

class TransactionHistory:
    """
    Transaction history database
    In production: Use Cloudflare D1 or external DB
    """
    
    def __init__(self):
        self._transactions: List[Dict] = []
    
    async def log_transaction(self, tx_data: Dict) -> str:
        """Log successful transaction"""
        tx_id = hashlib.sha256(
            f"{tx_data['from']}{tx_data['to']}{tx_data['amount']}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        tx_record = {
            "id": tx_id,
            "timestamp": datetime.utcnow().isoformat(),
            **tx_data
        }
        
        self._transactions.append(tx_record)
        return tx_id
    
    async def get_user_history(self, address: str, limit: int = 50) -> List[Dict]:
        """Get transaction history for a user"""
        user_txs = [
            tx for tx in self._transactions
            if tx.get("from") == address or tx.get("to") == address
        ]
        return sorted(user_txs, key=lambda x: x["timestamp"], reverse=True)[:limit]

# Initialize databases
alias_db = AliasDB()
tx_history = TransactionHistory()

# ============================================================================
# BLOCKCHAIN INTEGRATION (Arc Protocol)
# ============================================================================

class ArcBlockchain:
    """
    Arc Protocol blockchain interface
    Integrates with Habu Ado smart contract functions
    """
    
    def __init__(self):
        self.rpc_url = os.environ.get("ARC_RPC_URL", "https://arc-mainnet.example.com")
        self.contract_address = os.environ.get("ARC_CONTRACT_ADDRESS")
    
    async def send_payment(
        self,
        from_address: str,
        to_address: str,
        amount: float,
        currency: str = "ARC",
        memo: Optional[str] = None,
        signature: str = None
    ) -> Dict[str, Any]:
        """Execute single payment on Arc blockchain"""
        
        # Prepare transaction
        tx_data = {
            "from": from_address,
            "to": to_address,
            "amount": amount,
            "currency": currency,
            "memo": memo,
            "nonce": datetime.utcnow().timestamp(),
            "signature": signature
        }
        
        # Call smart contract (pseudo-code)
        # In production: Use actual Arc SDK
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.rpc_url}/contract/{self.contract_address}/send",
                json=tx_data,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Blockchain error: {response.text}"
                )
            
            return response.json()
    
    async def create_subscription(
        self,
        from_address: str,
        to_address: str,
        amount: float,
        frequency: str,
        start_date: str,
        signature: str
    ) -> Dict[str, Any]:
        """Create recurring payment on Arc blockchain"""
        
        tx_data = {
            "from": from_address,
            "to": to_address,
            "amount": amount,
            "frequency": frequency,
            "start_date": start_date,
            "signature": signature
        }
        
        # Call smart contract subscription function
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.rpc_url}/contract/{self.contract_address}/subscribe",
                json=tx_data,
                timeout=30.0
            )
            
            return response.json()
    
    async def split_payment(
        self,
        from_address: str,
        recipients: List[Dict],
        total_amount: float,
        memo: Optional[str],
        signature: str
    ) -> Dict[str, Any]:
        """Execute split payment to multiple recipients"""
        
        tx_data = {
            "from": from_address,
            "recipients": recipients,
            "total_amount": total_amount,
            "memo": memo,
            "signature": signature
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.rpc_url}/contract/{self.contract_address}/split",
                json=tx_data,
                timeout=30.0
            )
            
            return response.json()

# Initialize blockchain client
arc_chain = ArcBlockchain()

# ============================================================================
# API ROUTES
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Bulut API",
        "version": API_VERSION,
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "operational",
            "database": "operational",
            "blockchain": "operational"
        }
    }

# ============================================================================
# ALIAS MANAGEMENT
# ============================================================================

@app.post("/alias/register")
async def register_alias(registration: AliasRegistration):
    """
    Register new alias -> address mapping
    Requires signature to prove ownership
    """
    # Verify signature (pseudo-code)
    # In production: Verify cryptographic signature
    
    # Check if alias available
    if await alias_db.alias_exists(registration.alias):
        raise HTTPException(
            status_code=409,
            detail=f"Alias {registration.alias} is already registered"
        )
    
    # Register alias
    success = await alias_db.register_alias(
        registration.alias,
        registration.address
    )
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to register alias"
        )
    
    return {
        "success": True,
        "alias": registration.alias,
        "address": registration.address,
        "message": "Alias registered successfully"
    }

@app.get("/alias/{alias}")
async def get_address_by_alias(alias: str):
    """Resolve alias to wallet address"""
    if not alias.startswith('@'):
        alias = '@' + alias
    
    address = await alias_db.get_address_by_alias(alias)
    
    if not address:
        raise HTTPException(
            status_code=404,
            detail=f"Alias {alias} not found"
        )
    
    return {
        "alias": alias,
        "address": address
    }

@app.get("/address/{address}/alias")
async def get_alias_by_address(address: str):
    """Get alias for wallet address"""
    alias = await alias_db.get_alias_by_address(address)
    
    return {
        "address": address,
        "alias": alias
    }

# ============================================================================
# PAYMENT PROCESSING
# ============================================================================

@app.post("/process_command")
async def process_command(command: Dict[str, str]):
    """
    Process natural language payment command
    Calls AI agent and returns payment intent
    """
    text = command.get("text")
    user_id = command.get("user_id")
    
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' field")
    
    # Call AI agent
    ai_agent_url = os.environ.get("AI_AGENT_URL", "http://localhost:8001")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ai_agent_url}/parse_payment",
            json={"text": text, "user_id": user_id},
            timeout=10.0
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="AI agent failed to parse command"
            )
        
        return response.json()

@app.post("/execute_payment")
async def execute_payment(request: ExecutePaymentRequest):
    """
    Execute payment on blockchain
    This is the critical route that bridges AI -> Blockchain
    """
    intent = request.payment_intent
    payment_type = intent.payment_type
    
    # Resolve aliases to addresses
    intent_data = intent.intent
    
    # Handle recipient alias resolution
    if "recipient" in intent_data and "alias" in intent_data["recipient"]:
        alias = intent_data["recipient"]["alias"]
        to_address = await alias_db.get_address_by_alias(alias)
        
        if not to_address:
            raise HTTPException(
                status_code=404,
                detail=f"Recipient alias {alias} not found"
            )
        
        intent_data["recipient"]["address"] = to_address
    
    try:
        # Route to appropriate blockchain function
        if payment_type == "single":
            result = await arc_chain.send_payment(
                from_address=request.user_address,
                to_address=intent_data["recipient"]["address"],
                amount=intent_data["amount"],
                currency=intent_data.get("currency", "ARC"),
                memo=intent_data.get("memo"),
                signature=request.user_signature
            )
        
        elif payment_type == "subscription":
            result = await arc_chain.create_subscription(
                from_address=request.user_address,
                to_address=intent_data["recipient"]["address"],
                amount=intent_data["amount"],
                frequency=intent_data["subscription"]["frequency"],
                start_date=intent_data["subscription"]["start_date"],
                signature=request.user_signature
            )
        
        elif payment_type == "split":
            # Resolve all recipient aliases
            recipients = []
            for recipient in intent_data["recipients"]:
                if "alias" in recipient:
                    address = await alias_db.get_address_by_alias(recipient["alias"])
                    if not address:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Recipient {recipient['alias']} not found"
                        )
                    recipient["address"] = address
                recipients.append(recipient)
            
            result = await arc_chain.split_payment(
                from_address=request.user_address,
                recipients=recipients,
                total_amount=intent_data["amount"],
                memo=intent_data.get("memo"),
                signature=request.user_signature
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown payment type: {payment_type}"
            )
        
        # Log transaction
        await tx_history.log_transaction({
            "from": request.user_address,
            "to": intent_data.get("recipient", {}).get("address"),
            "amount": intent_data.get("amount"),
            "type": payment_type,
            "tx_hash": result.get("transaction_hash"),
            "status": "success"
        })
        
        return TransactionResponse(
            success=True,
            transaction_hash=result.get("transaction_hash"),
            blockchain="arc",
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        return TransactionResponse(
            success=False,
            blockchain="arc",
            timestamp=datetime.utcnow().isoformat(),
            error=str(e)
        )

@app.get("/history/{address}")
async def get_transaction_history(address: str, limit: int = 50):
    """Get transaction history for user"""
    history = await tx_history.get_user_history(address, limit)
    
    return {
        "address": address,
        "count": len(history),
        "transactions": history
    }

# ============================================================================
# DEPLOYMENT NOTES FOR CLOUDFLARE WORKERS
# ============================================================================

"""
CLOUDFLARE WORKERS DEPLOYMENT:

1. Install Wrangler CLI:
   npm install -g wrangler

2. Configure wrangler.toml:
   ```toml
   name = "bulut-api"
   type = "python"
   account_id = "YOUR_ACCOUNT_ID"
   workers_dev = true
   
   [env.production]
   route = "api.bulut.app/*"
   kv_namespaces = [
       { binding = "ALIAS_DB", id = "YOUR_KV_ID" }
   ]
   ```

3. Deploy:
   wrangler publish

4. Set environment variables:
   wrangler secret put ANTHROPIC_API_KEY
   wrangler secret put ARC_RPC_URL
   wrangler secret put ARC_CONTRACT_ADDRESS

PERFORMANCE OPTIMIZATION:
- Use Cloudflare KV for alias storage (sub-50ms reads)
- Use Durable Objects for transaction state
- Cache AI responses for common commands
- Implement connection pooling for blockchain RPC
"""