import os
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any

from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

from .utils import normalize_address

ARC_RPC_URL = os.getenv("ARC_RPC_URL", "https://mainnet.arc.network")
ARC_EXPLORER_URL = os.getenv("ARC_EXPLORER_URL", "https://explorer.arc.network")
CIRCLE_TX_EXPLORER_URL = os.getenv("CIRCLE_TX_EXPLORER_URL", "https://etherscan.io/tx/")
ARC_USDC_ADDRESS = os.getenv("ARC_USDC_ADDRESS", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
ARC_CHAIN_ID = int(os.getenv("ARC_CHAIN_ID", "4224"))


class BlockchainService:
    
    def __init__(self, rpc_url: str, usdc_contract_address: str, storage_instance: Any, circle_service: Any):
        self.rpc_url = rpc_url
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.usdc_contract_address = Web3.to_checksum_address(usdc_contract_address)
        self.storage = storage_instance
        self.circle_service = circle_service
        
        if not self.web3.is_connected():
            print(" Web3 not connected to network:", rpc_url)
        else:
            print(f" Connected to chain ID: {self.web3.eth.chain_id} (BlockchainService)")
        
        if not self.circle_service:
            print(" CRITICAL: CircleService not passed. P2P payments will fail.")
        else:
            print(f" CircleService is available (Mode: {'REAL' if self.circle_service.is_real else 'SIMULACIÓN'}).")

    @staticmethod
    def verify_user_signature(from_address: str, message: str, signature: str) -> bool:
        if not signature:
            return False
        
        try:
            encoded_message = encode_defunct(text=message)
            recovered_address = Account.recover_message(encoded_message, signature=signature)
            
            normalized_expected = normalize_address(from_address)
            normalized_recovered = normalize_address(recovered_address)

            return normalized_recovered == normalized_expected
        except Exception as e:
            print(f"Error al verificar la firma: {e}")
            return False

    def _get_explorer_url(self, tx_hash: str, is_circle_tx: bool = False) -> str:
        if is_circle_tx:
            return f"{CIRCLE_TX_EXPLORER_URL}{tx_hash}"
        return f"{ARC_EXPLORER_URL}/tx/{tx_hash}"

    async def send_payment(self, from_address: str, to_address: str, amount: float,
                            currency: str = "USDC", memo: Optional[str] = None, signature: str = None) -> Dict:
        
        if not self.circle_service:
            return {"success": False, "error": "Circle Payment Service is unavailable."}

        auth_message = f"Pagar {amount} {currency} a {to_address} desde {from_address}."
        
        if not self.verify_user_signature(from_address, auth_message, signature):
            return {"success": False, "error": "Autorización denegada: Firma inválida o faltante para la dirección de origen.",
                    "timestamp": datetime.utcnow().isoformat()}
        
        # NOTA: En producción, 'wallet_id' debe obtenerse de un lookup Circle Address -> Circle walletId.
        wallet_id = from_address 

        tx_result = await self.circle_service.initiate_transfer(
            wallet_id=wallet_id, 
            to_address=to_address,
            amount=amount,
            memo=memo
        )
        
        if tx_result["success"]:
            status = tx_result.get("status", "pending")
            tx_hash = tx_result.get("transaction_hash")
            
            is_final_status = status in ["confirmed", "complete", "success"]
            timestamp = datetime.utcnow().isoformat() if is_final_status or not self.circle_service.is_real else None
            
            return {
                "success": True,
                "transaction_hash": tx_hash,
                "status": status,
                "explorer_url": self._get_explorer_url(tx_hash, is_circle_tx=True),
                "timestamp": timestamp
            }
        else:
            return {"success": False, "error": f"Circle Execution Failed: {tx_result.get('error')}", 
                    "timestamp": datetime.utcnow().isoformat()}

    async def create_subscription(self, from_address: str, to_address: str, amount: float,
                                    frequency: str, start_date: str, signature: str) -> Dict:
        
        print("Ejecutando create_subscription (SIMULADO)")
        sub_id = "sub_" + hashlib.sha256(f"{from_address}{to_address}{datetime.utcnow()}".encode()).hexdigest()[:16]
        tx_hash = "0x" + uuid.uuid4().hex
        
        self.storage.subscriptions[sub_id] = {
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
        
        print("Ejecutando split_payment (SIMULADO)")
        tx_hash = "0x" + uuid.uuid4().hex
        
        return {"success": True, "transaction_hash": tx_hash,
                "recipient_count": len(recipients), "total_amount": total_amount,
                "status": "confirmed", "explorer_url": self._get_explorer_url(tx_hash)}