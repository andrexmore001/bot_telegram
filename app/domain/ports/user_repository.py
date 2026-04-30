from abc import ABC, abstractmethod

class UserRepositoryPort(ABC):
    @abstractmethod
    def is_verified(self, user_id: int) -> bool:
        """Verifica si el ID de Telegram ya está vinculado a un teléfono autorizado."""
        pass

    @abstractmethod
    def is_phone_allowed(self, phone: str) -> bool:
        """Verifica si el número de teléfono está en la lista blanca."""
        pass

    @abstractmethod
    def authorize_user(self, user_id: int, phone: str):
        """Vincula un ID de Telegram con un teléfono y guarda la persistencia."""
        pass

    @abstractmethod
    def get_whitelist(self) -> list[str]:
        """Obtiene la lista completa de teléfonos autorizados."""
        pass

    @abstractmethod
    def add_to_whitelist(self, phone: str):
        """Agrega un teléfono a la lista blanca."""
        pass

    @abstractmethod
    def remove_from_whitelist(self, phone: str):
        """Elimina un teléfono de la lista blanca."""
        pass

    # --- Gestión de Canales ---
    @abstractmethod
    async def get_channels(self) -> list[dict]:
        """Obtiene la lista de canales registrados."""
        pass

    @abstractmethod
    async def add_channel(self, channel_id: str, name: str):
        """Registra un nuevo canal."""
        pass

    @abstractmethod
    async def delete_channel(self, channel_id: str):
        """Elimina un canal registrado."""
        pass
