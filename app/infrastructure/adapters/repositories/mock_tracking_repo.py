from typing import Optional
from app.domain.ports.tracking_repository import TrackingRepositoryPort
from app.domain.models.shipping import TrackingInfo

class MockTrackingRepository(TrackingRepositoryPort):
    def get_by_id(self, guide_number: str) -> Optional[TrackingInfo]:
        """Devuelve datos simulados para cualquier guía."""
        # Simulación: Si el número de guía termina en '0', diremos que no existe
        if guide_number.endswith('0'):
            return None
            
        return TrackingInfo(
            guide_number=guide_number,
            status="EN TRÁNSITO hacia la bodega local (Mock Repo)",
            estimated_delivery="Mañana antes de las 5:00 PM"
        )
