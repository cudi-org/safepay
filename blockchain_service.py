import os
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any

from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

# Leemos las variables de entorno (ya no usamos GAS_PAYER_KEY aquí)
ARC_RPC_URL = os.getenv("ARC_RPC_URL", "https://mainnet.arc.network")
ARC_EXPLORER_URL = os.getenv("ARC_EXPLORER_URL", "https://explorer.arc.network")
ARC_USDC_ADDRESS = os.getenv("ARC_USDC_ADDRESS", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
# GAS_PAYER_KEY = os.getenv("GAS_PAYER_KEY", "") # Ya no es necesario aquí
ARC_CHAIN_ID = int(os.getenv("ARC_CHAIN_ID", "4224"))


class BlockchainService:
    # 🔄 MODIFICADO: Ahora acepta 'circle_service' como dependencia.
    def __init__(self, rpc_url: str, usdc_contract_address: str, storage_instance: Any, circle_service: Any):
        """
        Inicializa el servicio de blockchain.
        circle_service: Instancia del servicio de pagos P2P (Circle).
        """
        self.rpc_url = rpc_url
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.usdc_contract_address = Web3.to_checksum_address(usdc_contract_address)
        # self.gas_payer = Account.from_key(gas_payer_key) if gas_payer_key else None # Ya no se inicializa
        self.storage = storage_instance
        self.circle_service = circle_service # ⬅️ Almacenamos la dependencia
        
        if not self.web3.is_connected():
            print("⚠️ Web3 not connected to network:", rpc_url)
        else:
            print(f"✅ Connected to chain ID: {self.web3.eth.chain_id} (BlockchainService)")
        
        if not self.circle_service:
            print("🚨 CRITICAL: CircleService not passed. P2P payments will fail.")
        else:
            print(f"✅ CircleService is available (Mode: {'REAL' if self.circle_service.is_real else 'SIMULACIÓN'}).")


    def _get_explorer_url(self, tx_hash: str) -> str:
        return f"{ARC_EXPLORER_URL}/tx/{tx_hash}"

    # 🔄 MODIFICADO: Delega la ejecución del pago a CircleService
    async def send_payment(self, from_address: str, to_address: str, amount: float,
                            currency: str = "USDC", memo: Optional[str] = None, signature: str = None) -> Dict:
        
        if not self.circle_service:
            return {"success": False, "error": "Circle Payment Service is unavailable."}

        # 1. Ejecutar la transferencia P2P a través de Circle.
        # CircleService se encarga de la firma no-custodial y del Paymaster.
        # En una implementación real, la firma del usuario se usaría para autorizar 
        # a Circle a usar la billetera (con un token de sesión/JWT de Circle).
        
        tx_result = await self.circle_service.initiate_transfer(
            from_address=from_address,
            to_address=to_address,
            amount=amount,
            memo=memo
        )
        
        if tx_result["success"]:
            return {
                "success": True,
                "transaction_hash": tx_result.get("transaction_hash"),
                "status": "confirmed",
                "explorer_url": self._get_explorer_url(tx_result.get("transaction_hash")),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {"success": False, "error": f"Circle Execution Failed: {tx_result.get('error')}", 
                    "timestamp": datetime.utcnow().isoformat()}

    # Las siguientes dos funciones se mantienen como SIMULACIÓN de Smart Contracts
    
    async def create_subscription(self, from_address: str, to_address: str, amount: float,
                                    frequency: str, start_date: str, signature: str) -> Dict:
        # --- LÓGICA SIMULADA (Smart Contract) ---
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
        # --- LÓGICA SIMULADA (Smart Contract) ---
        print("Ejecutando split_payment (SIMULADO)")
        tx_hash = "0x" + uuid.uuid4().hex
        
        return {"success": True, "transaction_hash": tx_hash,
                "recipient_count": len(recipients), "total_amount": total_amount,
                "status": "confirmed", "explorer_url": self._get_explorer_url(tx_hash)}
