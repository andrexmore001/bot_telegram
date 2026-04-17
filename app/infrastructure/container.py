from dependency_injector import containers, providers
from app.infrastructure.config.config import config
from app.infrastructure.adapters.llamaindex.adapter import LlamaIndexAdapter
from app.infrastructure.adapters.repositories.mock_tracking_repo import MockTrackingRepository
from app.infrastructure.adapters.repositories.json_pqr_repo import JsonPQRRepository
from app.domain.services.assistant_service import AssistantService

class Container(containers.DeclarativeContainer):
    # Configuración
    config = providers.Object(config)

    # Adaptadores de Datos (Driven Adapters)
    knowledge_base = providers.Singleton(
        LlamaIndexAdapter,
        api_key=config.provided.openai_api_key
    )
    
    tracking_repository = providers.Singleton(
        MockTrackingRepository
    )
    
    pqr_repository = providers.Singleton(
        JsonPQRRepository,
        file_path="data/pqrs.json"
    )

    # Servicios de Dominio
    assistant_service = providers.Factory(
        AssistantService,
        knowledge_base=knowledge_base,
        tracking_repo=tracking_repository,
        pqr_repo=pqr_repository
    )
