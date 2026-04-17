from abc import ABC, abstractmethod
from typing import Optional
from app.domain.models.shipping import TrackingInfo

class TrackingRepositoryPort(ABC):
    @abstractmethod
    def get_by_id(self, guide_number: str) -> Optional[TrackingInfo]:
        """Obtener información de seguimiento por número de guía."""
        pass
