import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiogram import Bot, Dispatcher

from app.core.config import config
from app.bot.handlers import router
from app.rag.engine import setup_rag

# Configurar logs
logging.basicConfig(level=logging.INFO)

# Verificar token
if config.telegram_bot_token == "tu_token_de_telegram_aqui":
    logging.warning("¡ATENCIÓN! No has configurado tu TELEGRAM_BOT_TOKEN en el archivo .env")

# Instanciar Bot
bot = Bot(token=config.telegram_bot_token)
dp = Dispatcher()
dp.include_router(router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Levantando FastAPI y RAG (Lifespan)...")
    # Solo inicializamos RAG explícitamente si se lanza via uvicorn.
    yield

# Instanciar FastAPI
app = FastAPI(title="PoC Interrapidisimo RAG Bot", lifespan=lifespan)

@app.get("/")
def read_root():
    return {"status": "ok", "app": "Interrapidisimo Telegram Bot"}

# Script para ejecutar todo mediante Long Polling (ideal para local)
if __name__ == "__main__":
    logging.info("Iniciando indexador de RAG...")
    setup_rag()
    
    logging.info("Iniciando bot de Telegram en modo Local (Polling)...")
    asyncio.run(dp.start_polling(bot))
