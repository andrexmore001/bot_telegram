from app.domain.ports.knowledge_base import KnowledgeBasePort

class AssistantService:
    def __init__(
        self, 
        knowledge_base: KnowledgeBasePort
    ):
        self.knowledge_base = knowledge_base

    def get_ai_response(self, question: str) -> str:
        """Obtener respuesta de la base de conocimientos."""
        return self.knowledge_base.ask(question)
