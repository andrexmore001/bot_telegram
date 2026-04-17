import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiogram import Bot, Dispatcher

# Inyección de Dependencias
from app.infrastructure.container import Container
from app.infrastructure.adapters.telegram import handlers as telegram_handlers

# Configurar logs
logging.basicConfig(level=logging.INFO)

# Inicializar Contenedor e Inyectar
container = Container()
container.wire(modules=[telegram_handlers])

config = container.config()

# Verificar token
if config.telegram_bot_token == "tu_token_de_telegram_aqui":
    logging.warning("¡ATENCIÓN! No has configurado tu TELEGRAM_BOT_TOKEN en el archivo .env")

# Instanciar Bot
bot = Bot(token=config.telegram_bot_token)
dp = Dispatcher()
dp.include_router(telegram_handlers.router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Levantando FastAPI y RAG (Lifespan)...")
    yield

# Instanciar FastAPI
app = FastAPI(title="PoC Interrapidisimo RAG Bot (Hexagonal)", lifespan=lifespan)

@app.get("/")
def read_root():
    return {"status": "ok", "app": "Interrapidisimo Telegram Bot Refactored"}

# Script para ejecutar todo mediante Long Polling (ideal para local)
if __name__ == "__main__":
    logging.info("Iniciando componentes de infraestructura...")
    # Aseguramos que el adaptador de LlamaIndex se inicialice
    container.knowledge_base().setup()
    
    logging.info("Iniciando bot de Telegram en modo Local (Polling)...")
    asyncio.run(dp.start_polling(bot))
