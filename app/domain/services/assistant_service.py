from typing import Optional
from app.domain.ports.knowledge_base import KnowledgeBasePort
from app.domain.ports.tracking_repository import TrackingRepositoryPort
from app.domain.ports.pqr_repository import PQRRepositoryPort
from app.domain.models.shipping import TrackingInfo, PQRRequest

class AssistantService:
    def __init__(
        self, 
        knowledge_base: KnowledgeBasePort,
        tracking_repo: TrackingRepositoryPort,
        pqr_repo: PQRRepositoryPort
    ):
        self.knowledge_base = knowledge_base
        self.tracking_repo = tracking_repo
        self.pqr_repo = pqr_repo

    def get_ai_response(self, question: str) -> str:
        """Obtener respuesta de la base de conocimientos."""
        return self.knowledge_base.ask(question)

    def validate_tracking_number(self, number: str) -> bool:
        """Validar si un número de guía es válido (12 dígitos numéricos)."""
        return len(number) == 12 and number.isdigit()

    def get_tracking_status(self, guide_number: str) -> Optional[TrackingInfo]:
        """Obtener el estado de un envío desde el repositorio."""
        return self.tracking_repo.get_by_id(guide_number)

    def create_pqr(self, user_name: str, details: str) -> str:
        """Registrar una nueva PQR."""
        pqr = PQRRequest(user_name=user_name, details=details)
        return self.pqr_repo.save(pqr)
