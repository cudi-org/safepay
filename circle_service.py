import os
import uuid
import httpx
from httpx import HTTPStatusError
from typing import Dict, Any, Optional
from datetime import datetime


CIRCLE_API_KEY = os.getenv("CIRCLE_API_KEY", "")
CIRCLE_BASE_URL = os.getenv("CIRCLE_BASE_URL", "https://api.circle.com/v1/w3s")
CIRCLE_ENTITY_ID = os.getenv("CIRCLE_ENTITY_ID", "")


class CircleService:
    """
    Servicio para interactuar con el Circle Developer-Controlled Wallets API.
    Este servicio es la clave para la gestión no-custodial y las transacciones gasless.
    """

    def __init__(self, api_key: str, base_url: str, entity_id: str):
        self.api_key = api_key
        self.base_url = base_url
        self.entity_id = entity_id
        self.is_real = bool(api_key and entity_id)

        if self.is_real:
            print("CircleService: Inicializado en modo REAL (utilizando la API de Circle).")
            self.client = httpx.AsyncClient(
                base_url=base_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0
            )
        else:
            print("CircleService: Inicializado en modo SIMULACIÓN (faltan claves de Circle).")
            self._mock_wallets: Dict[str, Dict] = {}
            self._init_demo_wallets()

    def _init_demo_wallets(self):
        """Simula la existencia de billeteras iniciales del demo en memoria."""
        demo_addresses = {
            "@alice": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "@bob": "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199",
        }
        for alias, address in demo_addresses.items():
            # Corrección: Normalizar a minúsculas al guardar
            normalized_address = address.lower()
            self._mock_wallets[normalized_address] = {
                "wallet_id": f"wal_mock_{alias[1:]}",
                "address": address, 
                "user_id": alias,  
                "status": "active"
            }
            
    async def get_wallet_by_address(self, address: str) -> Optional[Dict]:
        """Intenta mapear una dirección a una billetera (solo en modo simulación)."""
        if not self.is_real:
            return self._mock_wallets.get(address.lower())
        
        return None 


    async def initiate_transfer(self, from_address: str, to_address: str, amount: float, memo: Optional[str]) -> Dict[str, Any]:
        """
        Delega el pago P2P, cubriendo la firma y el gas con el Paymaster.
        from_address: La dirección pública del usuario (usada como key de búsqueda en simulación).
        """
        if self.is_real:
            
            ref_id = uuid.uuid4().hex
            payload = {
                "entityId": self.entity_id,
                "walletId": "REAL_WALLET_ID_HERE",
                "destinationAddress": to_address,
                "token": "USDC",
                "amount": str(amount),
                "refId": ref_id,
                "fee": {"type": "GAS"} 
            }
            try:
                response = await self.client.post("/user-controlled-wallets/transactions/transfer", json=payload)
                response.raise_for_status()
                data = response.json().get("data", {})
                return {
                    "success": True, 
                    "transaction_hash": data.get("txHash"), 
                    "circle_id": data.get("id"),
                    "status": data.get("status")
                }
            except HTTPStatusError as e:
                return {"success": False, "error": f"Error de Circle: {e.response.text}"}
            except Exception as e:
                return {"success": False, "error": f"Error general: {str(e)}"}
            
        else:
            # Corrección: Añadir await para llamar a la función async
            if not await self.get_wallet_by_address(from_address):
                return {"success": False, "error": "Simulación: Billetera de origen no encontrada en Circle."}
                
            tx_hash = "0xCircleMockTx" + uuid.uuid4().hex[:20]
            return {
                "success": True,
                "transaction_hash": tx_hash,
                "status": "confirmed",
                "circle_id": f"mock_tx_{uuid.uuid4().hex[:10]}",
                "timestamp": datetime.utcnow().isoformat()
            }
