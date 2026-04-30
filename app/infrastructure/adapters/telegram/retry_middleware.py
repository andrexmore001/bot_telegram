import asyncio
from aiogram import Bot
from aiogram.client.session.middlewares.base import BaseRequestMiddleware, NextRequestMiddlewareType
from aiogram.exceptions import TelegramRetryAfter
from aiogram.methods import Response, TelegramMethod
from aiogram.methods.base import TelegramType
from app.infrastructure.logging.logger import logger

class RetryAfterMiddleware(BaseRequestMiddleware):
    """
    Middleware para la sesión del Bot que maneja automáticamente los errores FloodWait (TelegramRetryAfter).
    Pausa el bot asíncronamente el tiempo que Telegram pide y luego reintenta el mensaje de forma transparente.
    """
    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        attempts = 3
        for attempt in range(attempts):
            try:
                # Intentamos ejecutar la petición hacia Telegram
                return await make_request(bot, method)
            except TelegramRetryAfter as e:
                # Si Telegram nos bloquea por ir muy rápido y es nuestro último intento, arrojamos el error
                if attempt == attempts - 1:
                    logger.error(f"Fallo definitivo tras {attempts} reintentos de FloodWait para el método {method.__class__.__name__}")
                    raise
                
                # Si no, esperamos el tiempo que Telegram nos exija
                logger.warning(
                    f"⚠️ FloodWait (Anti-Spam de Telegram) activado para la acción '{method.__class__.__name__}'. "
                    f"El bot esperará pacientemente {e.retry_after} segundos antes de enviar este mensaje..."
                )
                await asyncio.sleep(e.retry_after)
