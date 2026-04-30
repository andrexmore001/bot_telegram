from app.domain.ports.knowledge_base import KnowledgeBasePort

class AssistantService:
    def __init__(
        self, 
        knowledge_base: KnowledgeBasePort
    ):
        self.knowledge_base = knowledge_base

    def get_ai_response(self, question: str) -> str:
        """Obtener respuesta de la base de conocimientos (IA desactivada)."""
        return (
            "Hola. Por el momento, las consultas inteligentes están desactivadas. "
            "Pronto estaré disponible para responder tus dudas sobre logística."
        )
