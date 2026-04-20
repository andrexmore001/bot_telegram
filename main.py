import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from aiogram.types import ErrorEvent

# Inyección de Dependencias y Logging
from app.infrastructure.container import Container
from app.infrastructure.adapters.telegram import handlers as telegram_handlers
from app.infrastructure.adapters.telegram.middleware import AccessControlMiddleware
from app.infrastructure.logging.logger import logger

# Inicializar Contenedor e Inyectar
container = Container()
container.wire(modules=[telegram_handlers])

config = container.config()
user_repo = container.user_repository()

# Verificar token
if config.telegram_bot_token == "tu_token_de_telegram_aqui":
    logger.warning("¡ATENCIÓN! No has configurado tu TELEGRAM_BOT_TOKEN en el archivo .env")

# --- MANEJO DE ERRORES GLOBAL ---
async def global_error_handler(event: ErrorEvent):
    """Captura cualquier error no controlado en los handlers."""
    logger.error(f"Error no controlado: {event.exception}", exc_info=True)
    
    # Intentar informar al usuario si el error ocurrió durante un mensaje
    if event.update.message:
        await event.update.message.answer(
            "⚠️ Ups, ha ocurrido un error interno inesperado. "
            "Ya hemos notificado al equipo técnico."
        )

# Instanciar Bot y Dispatcher
bot = Bot(token=config.telegram_bot_token)
dp = Dispatcher()
dp.include_router(telegram_handlers.router)
dp.errors.register(global_error_handler)

# Registrar Middleware de Seguridad
dp.message.middleware(AccessControlMiddleware(user_repository=user_repo))

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Levantando FastAPI y RAG (Lifespan)...")
    yield

# Instanciar FastAPI
app = FastAPI(title="PoC Interrapidisimo RAG Bot (Hexagonal)", lifespan=lifespan)

@app.get("/")
def read_root():
    return {"status": "ok", "app": "Interrapidisimo Telegram Bot Refactored"}

# Script para ejecutar todo mediante Long Polling (ideal para local)
if __name__ == "__main__":
    logger.info("Iniciando componentes de infraestructura...")
    try:
        # Aseguramos que el adaptador de LlamaIndex se inicialice
        container.knowledge_base().setup()
        
        logger.info("Iniciando bot de Telegram en modo Local (Polling)...")
        asyncio.run(dp.start_polling(bot))
    except Exception as e:
        logger.critical(f"Fallo crítico durante el arranque: {e}", exc_info=True)
