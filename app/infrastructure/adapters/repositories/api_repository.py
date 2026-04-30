import httpx
from typing import List, Dict, Optional
from app.domain.ports.user_repository import UserRepositoryPort
from app.infrastructure.logging.logger import logger

class ApiRepository(UserRepositoryPort):
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def _get_data(self) -> Dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error consultando API externa de datos: {e}")
            return {"Authorize_user": [], "channels": []}

    def is_verified(self, user_id: int) -> bool:
        # Nota: Esto podría requerir una caché o un endpoint específico si hay miles de usuarios
        # Por ahora lo dejamos como stub o implementación simple
        return False

    def is_phone_allowed(self, phone: str) -> bool:
        # Se debería consultar la lista blanca de la API
        return False

    def authorize_user(self, user_id: int, phone: str):
        logger.info(f"Autorización de usuario {user_id} vía API (No implementado en persistencia externa)")

    def get_whitelist(self) -> List[str]:
        # En un flujo real, esto sería async, pero el puerto actual es síncrono.
        # Se recomienda actualizar el puerto a async en el futuro.
        return []

    def add_to_whitelist(self, phone: str):
        pass

    def remove_from_whitelist(self, phone: str):
        pass

    # --- Gestión de Canales ---
    async def get_channels(self) -> List[Dict]:
        data = await self._get_data()
        return data.get("channels", [])

    async def add_channel(self, channel_id: str, name: str):
        logger.info(f"Agregando canal {name} ({channel_id}) vía API externa")
        # Aquí iría un POST a la API externa

    async def delete_channel(self, channel_id: str):
        logger.info(f"Eliminando canal {channel_id} vía API externa")
        # Aquí iría un DELETE a la API externa
