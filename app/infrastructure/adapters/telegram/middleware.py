from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from app.domain.ports.user_repository import UserRepositoryPort
from app.infrastructure.logging.logger import logger

class AccessControlMiddleware(BaseMiddleware):
    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repo = user_repository
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Solo aplicar a mensajes (no comandos de sistema internos si los hubiera)
        if not isinstance(event, Message):
            return await handler(event, data)

        # Si es un grupo, permitir paso libre (según requerimiento)
        if event.chat.type in ["group", "supergroup"]:
            return await handler(event, data)

        # Si es chat privado, verificar autorización
        user_id = event.from_user.id
        
        # Excepción: si el mensaje es el contacto que estamos pidiendo, dejarlo pasar al handler
        if event.contact:
            return await handler(event, data)
        
        # Excepción: comandos básicos como /start para que no se bloquee el inicio
        if event.text and event.text.startswith("/start"):
            return await handler(event, data)

        if self.user_repo.is_verified(user_id):
            return await handler(event, data)

        # Si no está verificado, pedir el contacto
        logger.info(f"Acceso denegado en privado para user_id {user_id}. Solicitando contacto.")
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Validar mi número de teléfono", request_contact=True)]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await event.answer(
            "🔒 **Acceso Restringido**\n\n"
            "Para usar este asistente en privado, primero debemos validar si tu número de teléfono está autorizado.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return  # Detener la propagación del evento
