from abc import ABC, abstractmethod

class KnowledgeBasePort(ABC):
    @abstractmethod
    def ask(self, question: str) -> str:
        """Consultar la base de conocimientos."""
        pass
