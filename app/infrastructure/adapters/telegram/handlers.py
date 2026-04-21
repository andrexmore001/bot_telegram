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
        
        invite_link_text = ""
        from app.infrastructure.config.config import config
        if config.vip_group_id:
            try:
                invite = await message.bot.create_chat_invite_link(
                    chat_id=config.vip_group_id,
                    member_limit=1,
                    name=f"Pase VIP para {message.from_user.first_name}"
                )
                invite_link_text = f"\n\n🔗 **Tu pase de acceso:** [Al Grupo]({invite.invite_link})\n_(Este enlace es de uso único)_"
            except Exception as e:
                logger.error(f"No se pudo crear link: {e}")
                invite_link_text = "\n\n⚠️ Estás autorizado, pero no pude generar el enlace al grupo"
                
        await message.answer(
            f"✅ **¡Acceso Concedido!**\n\n"
            f"Tu número `{phone}` ha sido verificado exitosamente. "
            "Ahora puedes usar todas mis funciones en privado." + invite_link_text,
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

@router.message(F.new_chat_members)
@inject
async def on_new_chat_members(
    message: Message,
    user_repository: UserRepositoryPort = Provide[Container.user_repository]
):
    """Guardia (Bouncer) del grupo VIP."""
    from app.infrastructure.config.config import config
    
    logger.info(f"👀 Evento 'Nuevo Miembro' detectado en el chat ID: {message.chat.id}. VIP Esperado: {config.vip_group_id}")
    
    def normalize_tg_id(tg_id: str) -> str:
        return tg_id.replace("-100", "-") if tg_id.startswith("-100") else tg_id

    if not config.vip_group_id or normalize_tg_id(str(message.chat.id)) != normalize_tg_id(config.vip_group_id):
        logger.info("Ignorando evento porque el ID del grupo no coincide o no está configurado.")
        return
        
    bot_info = await message.bot.get_me()

    
    for new_member in message.new_chat_members:
        if new_member.id == bot_info.id:
            continue
            
        if not user_repository.is_verified(new_member.id):
            logger.warning(f"Usuario denegado detectado: ID {new_member.id} ({new_member.first_name}) intentó entrar sin autorización. Expulsando.")
            try:
                # Ban y luego Unban para hacer solo "Kick"
                await message.chat.ban(new_member.id)
                await message.chat.unban(new_member.id)
                await message.answer(f"🔒 {new_member.first_name} ha sido retirado porque no cuenta con verificación en el chat privado.")
            except Exception as e:
                logger.error(f"Error intentando expulsar al usuario {new_member.id}: {e}")

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

    text = message.text
    bot_info = await message.bot.get_me()
    bot_mention = f"@{bot_info.username}"

    # Si es un grupo, verificar mención o reply
    if message.chat.type in ["group", "supergroup"]:
        is_mentioned = bot_mention in text
        is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id
        
        if not (is_mentioned or is_reply_to_bot):
            return

    # Limpiar la mención del texto para no confundir al LLM
    text = text.replace(bot_mention, "").strip()
    
    if not text:
        return

    user_name = message.from_user.first_name
    msg = await message.reply(f"🤔 {user_name}, estoy consultando los manuales logísticos...")
    try:
        response = assistant_service.get_ai_response(text)
        await msg.edit_text(f"✅ *Respuesta para {user_name}:*\n\n{response}", parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"Lo siento {user_name}, tuve un problema procesando tu pregunta.")
        logger.error(f"Error procesando RAG para {user_name}: {e}", exc_info=True)

