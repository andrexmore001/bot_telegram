from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import inject, Provide

from app.domain.services.assistant_service import AssistantService
from app.domain.ports.user_repository import UserRepositoryPort
from app.infrastructure.logging.logger import logger
from app.infrastructure.container import Container

router = Router()

@router.message(F.contact)
@inject
async def process_contact(
    message: Message, 
    user_repository: UserRepositoryPort = Provide[Container.user_repository]
):
    """Procesa el contacto compartido por el usuario."""
    contact = message.contact
    phone = contact.phone_number
    user_id = message.from_user.id
    
    if user_repository.is_phone_allowed(phone):
        user_repository.authorize_user(user_id, phone)
        await message.answer(
            f"✅ **¡Acceso Concedido!**\n\n"
            f"Tu número `{phone}` ha sido verificado exitosamente. "
            "Ahora puedes usar todas mis funciones en privado.",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
    else:
        logger.warning(f"Intento de acceso fallido: teléfono {phone} no está en whitelist.")
        await message.answer(
            "❌ **Acceso Denegado**\n\n"
            "Lo siento, tu número de teléfono no tiene autorización para usar este servicio en privado. "
            "Contacta al administrador para ser agregado a la lista blanca.",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "¡Hola! Soy el asistente virtual de Interrapidisimo 📦.\n\n"
        "Puedes hacerme cualquier pregunta sobre nuestras políticas de envíos, tiempos de entrega y mercancías prohibidas.",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message()
@inject
async def respond_with_rag(
    message: Message, 
    state: FSMContext,
    assistant_service: AssistantService = Provide[Container.assistant_service]
):
    """
    Cualquier mensaje es enviado al RAG.
    En grupos, solo responde si es mencionado o si es un reply al bot.
    """
    if not message.text:
        return

    # Si es un grupo, verificar mención o reply
    if message.chat.type in ["group", "supergroup"]:
        bot_info = await message.bot.get_me()
        is_mentioned = f"@{bot_info.username}" in message.text
        is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id
        
        if not (is_mentioned or is_reply_to_bot):
            return

    user_name = message.from_user.first_name
    msg = await message.reply(f"🤔 {user_name}, estoy consultando los manuales logísticos...")
    try:
        response = assistant_service.get_ai_response(message.text)
        await msg.edit_text(f"✅ *Respuesta para {user_name}:*\n\n{response}", parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"Lo siento {user_name}, tuve un problema procesando tu pregunta.")
        logger.error(f"Error procesando RAG para {user_name}: {e}", exc_info=True)
