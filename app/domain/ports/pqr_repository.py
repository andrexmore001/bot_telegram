from abc import ABC, abstractmethod
from app.domain.models.shipping import PQRRequest

class PQRRepositoryPort(ABC):
    @abstractmethod
    def save(self, pqr: PQRRequest) -> str:
        """Guardar una nueva PQR y devolver el número de radicado."""
        pass
