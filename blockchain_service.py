import os
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any

from web3 import Web3
from eth_account import Account

# Leemos las variables de entorno directamente
ARC_RPC_URL = os.getenv("ARC_RPC_URL", "https://mainnet.arc.network")
ARC_EXPLORER_URL = os.getenv("ARC_EXPLORER_URL", "https://explorer.arc.network")
ARC_USDC_ADDRESS = os.getenv("ARC_USDC_ADDRESS", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
GAS_PAYER_KEY = os.getenv("GAS_PAYER_KEY", "")
ARC_CHAIN_ID = int(os.getenv("ARC_CHAIN_ID", "4224"))


class BlockchainService:
    def __init__(self, rpc_url: str, usdc_contract_address: str, gas_payer_key: str, storage_instance: Any):
        """
        Inicializa el servicio de blockchain.
        storage_instance: Es la BBDD en memoria, necesaria para las funciones SIMULADAS.
        """
        self.rpc_url = rpc_url
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.usdc_contract_address = Web3.to_checksum_address(usdc_contract_address)
        self.gas_payer = Account.from_key(gas_payer_key) if gas_payer_key else None
        self.storage = storage_instance # Almacenamiento para simulaciones

        if not self.web3.is_connected():
            print("⚠️ Web3 not connected to network:", rpc_url)
        else:
            print(f"✅ Connected to chain ID: {self.web3.eth.chain_id} (BlockchainService)")
            if not self.gas_payer:
                print("⚠️ GAS_PAYER_KEY not set. Real transactions will fail.")
            else:
                 print(f"✅ Gas Payer Address: {self.gas_payer.address}")


    def _get_explorer_url(self, tx_hash: str) -> str:
        return f"{ARC_EXPLORER_URL}/tx/{tx_hash}"

    async def send_payment(self, from_address: str, to_address: str, amount: float,
                           currency: str = "ARC", memo: Optional[str] = None, signature: str = None) -> Dict:
        # --- LÓGICA 100% REAL ---
        print("Ejecutando send_payment (REAL)...")
        try:
            from_addr = Web3.to_checksum_address(from_address)
            to_addr = Web3.to_checksum_address(to_address)
            value_wei = self.web3.to_wei(amount, "ether")
            
            if not self.gas_payer:
                raise Exception("Gas payer key not configured")
                
            nonce = self.web3.eth.get_transaction_count(self.gas_payer.address)
            tx = {
                "nonce": nonce,
                "to": to_addr,
                "value": value_wei,
                "gas": 21000,
                "gasPrice": self.web3.eth.gas_price,
                "chainId": ARC_CHAIN_ID,
            }
            
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
        # --- LÓGICA SIMULADA (No hay Smart Contract) ---
        print("Ejecutando create_subscription (SIMULADO)")
        sub_id = "sub_" + hashlib.sha256(f"{from_address}{to_address}{datetime.utcnow()}".encode()).hexdigest()[:16]
        tx_hash = "0x" + uuid.uuid4().hex # Hash falso
        
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
        # --- LÓGICA SIMULADA (No hay Smart Contract) ---
        print("Ejecutando split_payment (SIMULADO)")
        tx_hash = "0x" + uuid.uuid4().hex # Hash falso
        
        return {"success": True, "transaction_hash": tx_hash,
                "recipient_count": len(recipients), "total_amount": total_amount,
                "status": "confirmed", "explorer_url": self._get_explorer_url(tx_hash)}
