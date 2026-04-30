import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher
from aiogram.types import ErrorEvent, Update

# Inyección de Dependencias y Logging
from app.infrastructure.container import container
from app.infrastructure.adapters.telegram import handlers as telegram_handlers
from app.infrastructure.adapters.api.admin_router import router as admin_router
from app.infrastructure.adapters.api.error_handlers import register_error_handlers
from app.infrastructure.adapters.telegram.middleware import AccessControlMiddleware
from app.infrastructure.adapters.telegram.retry_middleware import RetryAfterMiddleware
from app.infrastructure.logging.logger import logger

# Inyectar
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
            "Ha ocurrido un error interno inesperado. "
            "Ya hemos notificado al equipo técnico."
        )

# Instanciar Bot y Dispatcher
bot = Bot(token=config.telegram_bot_token)

# Registrar Middleware de Sesión para FloodWait (Anti-Spam de Telegram)
bot.session.middleware(RetryAfterMiddleware())

dp = Dispatcher()

# Seguridad para evitar el error "Router is already attached" durante recargas de Uvicorn
if telegram_handlers.router.parent_router is not None:
    telegram_handlers.router.parent_router = None

dp.include_router(telegram_handlers.router)
dp.errors.register(global_error_handler)


# Registrar Middleware de Seguridad
dp.message.middleware(AccessControlMiddleware(user_repository=user_repo))

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Levantando FastAPI y RAG (Lifespan)...")
    
    # Almacenar objetos en el estado de la app para acceso desde routers
    app.state.bot = bot
    app.state.config = config
    app.state.container = container

    # Configurar Webhook si hay una URL definida
    if config.webhook_url:
        webhook_address = f"{config.webhook_url}{config.webhook_path}"
        logger.info(f"Configurando Webhook en: {webhook_address}")
        await bot.set_webhook(
            url=webhook_address,
            secret_token=config.webhook_secret,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True
        )
    else:
        logger.warning("No se ha definido WEBHOOK_URL. El bot NO recibirá mensajes externos.")
    
    yield
    
    logger.info("Cerrando Bot y FastAPI...")
    if config.webhook_url:
        logger.info("Eliminando Webhook...")
        await bot.delete_webhook()
    
    logger.info("Servidor detenido correctamente.")

# Instanciar FastAPI
app = FastAPI(title="PoC Interrapidisimo RAG Bot", lifespan=lifespan)

# Registrar manejadores de excepciones globales
register_error_handlers(app)

# Registrar Routers
app.include_router(admin_router)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción deberías restringir esto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MIDDLEWARE DE LOGGING DE API ---
import time
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Procesar la petición
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = "{0:.2f}".format(process_time)
    
    # No loggear el root o health checks si son muy ruidosos (opcional)
    if request.url.path not in ["/", "/favicon.ico"]:
        logger.info(
            f"API {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {formatted_process_time}ms"
        )
        
    return response


@app.get("/")
def read_root():
    return {"status": "ok", "app": "Interrapidisimo Telegram Bot", "webhook_configured": bool(config.webhook_url)}

@app.post(config.webhook_path)
async def telegram_webhook(request: Request):
    """Endpoint que recibe las actualizaciones de Telegram."""
    # Verificar el token secreto si está configurado
    if config.webhook_secret:
        x_telegram_bot_api_secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if x_telegram_bot_api_secret_token != config.webhook_secret:
            logger.warning("Intento de acceso al webhook con token secreto inválido.")
            return {"status": "error", "message": "Unauthorized"}

    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

# Script para ejecutar todo mediante Uvicorn
if __name__ == "__main__":
    logger.info("Iniciando servidor API y Bot...")
    # Usamos el objeto 'app' directamente para evitar la doble importación que causa conflictos en Aiogram
    uvicorn.run(app, host="0.0.0.0", port=8000)


