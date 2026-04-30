from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, ChatMemberUpdated
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, IS_NOT_MEMBER, MEMBER
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
                invite_group = await message.bot.create_chat_invite_link(
                    chat_id=config.vip_group_id,
                    member_limit=1,
                    name=f"Pase VIP para {message.from_user.first_name}"
                )
                invite_link_text += f"\n\n🔗 **Tu pase al Grupo de Interrapidisimo:** [Unirse]({invite_group.invite_link})"
            except Exception as e:
                logger.error(f"No se pudo crear link para grupo: {e}")
                
        if config.vip_channel_id:
            try:
                invite_channel = await message.bot.create_chat_invite_link(
                    chat_id=config.vip_channel_id,
                    member_limit=1,
                    name=f"Pase VIP para {message.from_user.first_name}"
                )
                invite_link_text += f"\n\n🔗 **Tu pase al  Canal de Interrapidísimo:** [Unirse]({invite_channel.invite_link})"
            except Exception as e:
                logger.error(f"No se pudo crear link para canal: {e}")
        
        if not invite_link_text:
            invite_link_text = "\n\n⚠️ Estás autorizado, pero no pude generar enlaces a las comunidades."
                
        await message.answer(
            f"✅ **¡Acceso Concedido!**\n\n"
            f"Tu número `{phone}` ha sido verificado exitosamente. "
            "Ahora puedes usar todas mis funciones en privado." + invite_link_text,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
    else:
        logger.warning(f"Intento de acceso fallido: teléfono {phone} no está en whitelist.")
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Validar mi número de teléfono", request_contact=True)]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer(
            "❌ **Acceso Denegado**\n\n"
            "Lo siento, tu número de teléfono no tiene autorización para usar este servicio en privado. "
            "Contacta al administrador para ser agregado a la lista blanca y luego vuelve a intentarlo.",
            reply_markup=keyboard,
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
        else:
            await message.answer(
                f"🎉 ¡Bienvenido/a {new_member.first_name} al Grupo de Interrapidísimo!\n\n"
                f"Nos alegra tenerte por aquí. 📦"
            )

@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> MEMBER))
@inject
async def on_user_join_channel_or_group(
    event: ChatMemberUpdated,
    user_repository: UserRepositoryPort = Provide[Container.user_repository]
):
    """Guardia (Bouncer) genérico para Canales y Grupos."""
    from app.infrastructure.config.config import config
    
    def normalize_tg_id(tg_id: str) -> str:
        return tg_id.replace("-100", "-") if tg_id.startswith("-100") else tg_id

    chat_id_norm = normalize_tg_id(str(event.chat.id))
    group_id_norm = normalize_tg_id(config.vip_group_id) if config.vip_group_id else None
    channel_id_norm = normalize_tg_id(config.vip_channel_id) if config.vip_channel_id else None

    # Solo procesamos si el evento ocurre en el grupo o canal VIP
    if chat_id_norm not in [group_id_norm, channel_id_norm] or chat_id_norm is None:
        return
        
    user = event.new_chat_member.user
    if user.is_bot:
        return
        
    if not user_repository.is_verified(user.id):
        logger.warning(f"Usuario denegado en {event.chat.type}: ID {user.id} ({user.first_name}). Expulsando.")
        try:
            await event.chat.ban(user.id)
            await event.chat.unban(user.id)
        except Exception as e:
            logger.error(f"Error expulsando usuario {user.id} de {event.chat.type}: {e}")

@router.message(Command("start"))
@inject
async def cmd_start(
    message: Message, 
    state: FSMContext,
    user_repository: UserRepositoryPort = Provide[Container.user_repository]
):
    await state.clear()
    
    user_id = message.from_user.id
    if user_repository.is_verified(user_id):
        await message.answer(
            "¡Hola! 📦\n\n"
            "Tu número ya ha sido validado.\n"
            "Recuerda que actualmente este bot funciona **exclusivamente para la validación de identidad** y administración de accesos.",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Validar mi número de teléfono", request_contact=True)]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(
            "¡Hola! 📦\n\n"
            "Para poder continuar, debes validar tu número de teléfono.\n"
            "Por favor, haz clic en el botón de abajo **📱 Validar mi número de teléfono**.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

@router.message()
@inject
async def respond_with_rag(
    message: Message, 
    state: FSMContext,
    assistant_service: AssistantService = Provide[Container.assistant_service]
):
    """
    Maneja las preguntas de los usuarios y las envía al sistema RAG (IA).
    Si la pregunta se hace en un grupo, responde por mensaje privado.
    """
    
    # Cambia esto a True cuando quieras volver a activar la Inteligencia Artificial
    AI_ENABLED = False

    
    if not AI_ENABLED:
        await message.answer(
            "📦 **¡Hola! Estamos ajustando nuestro flujo de información.**\n\n"
            "¡Muy pronto estaré listo para darte la mejor ruta de respuesta a tus dudas! 🚀",
            parse_mode="Markdown"
        )
        return

    if not message.text:
        return

    text = message.text
    bot_info = await message.bot.get_me()
    bot_mention = f"@{bot_info.username}"
    is_group = message.chat.type in ["group", "supergroup"]

    # Si es un grupo, verificar mención o reply
    if is_group:
        is_mentioned = bot_mention in text
        is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id
        
        if not (is_mentioned or is_reply_to_bot):
            return

    # Limpiar la mención del texto para no confundir al LLM
    text = text.replace(bot_mention, "").strip()
    
    if not text:
        return

    user_name = message.from_user.first_name
    user_id = message.from_user.id

    if is_group:
        # Lógica para Grupos: Responder por privado
        msg_group = await message.reply(f"🤔 {user_name}, estoy consultando mis manuales. Te enviaré la respuesta por mensaje privado 📩")
        
        try:
            # Notificamos por privado que estamos procesando
            msg_priv = await message.bot.send_message(
                chat_id=user_id,
                text=f"🤔 Hola {user_name}, estoy procesando tu pregunta del grupo:\n_{text}_\n\nDame un momento..."
            )
            
            # Consultar IA
            response = assistant_service.get_ai_response(text)
            
            # Actualizamos mensaje privado con la respuesta final
            await msg_priv.edit_text(
                f"🗨️ **Tú preguntaste en el grupo:**\n_{text}_\n\n✅ **Respuesta de Interrapidísimo:**\n{response}", 
                parse_mode="Markdown"
            )
            
            # Avisamos en el grupo que ya le respondimos
            await msg_group.edit_text(f"✅ {user_name}, te he enviado la respuesta por mensaje privado 📩")
            
        except Exception as e:
            logger.error(f"Error procesando RAG o enviando DM a {user_id}: {e}", exc_info=True)
            await msg_group.edit_text(
                f"⚠️ {user_name}, intenté enviarte la respuesta por privado pero no pude. "
                "Asegúrate de no haberme bloqueado o haber borrado nuestro chat privado."
            )
    else:
        # Lógica para Chat Privado normal
        msg_priv = await message.reply(f"🤔 {user_name}, estoy consultando los manuales logísticos...")
        try:
            response = assistant_service.get_ai_response(text)
            await msg_priv.edit_text(f"✅ *Respuesta para {user_name}:*\n\n{response}", parse_mode="Markdown")
        except Exception as e:
            await msg_priv.edit_text(f"Lo siento {user_name}, tuve un problema procesando tu pregunta.")
            logger.error(f"Error procesando RAG para {user_name}: {e}", exc_info=True)

