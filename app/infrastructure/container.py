from dependency_injector import containers, providers
from app.infrastructure.config.config import config
from app.infrastructure.adapters.llamaindex.adapter import LlamaIndexAdapter
from app.domain.services.assistant_service import AssistantService

class Container(containers.DeclarativeContainer):
    # Configuración
    config = providers.Object(config)

    # Adaptadores de Datos (Driven Adapters)
    knowledge_base = providers.Singleton(
        LlamaIndexAdapter,
        api_key=config.provided.openai_api_key
    )
    
    # Servicios de Dominio
    assistant_service = providers.Factory(
        AssistantService,
        knowledge_base=knowledge_base
    )
