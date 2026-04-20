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
