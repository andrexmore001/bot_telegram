from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import inject, Provide

from app.domain.services.assistant_service import AssistantService
from app.infrastructure.adapters.telegram.states import InterrapidisimoFlow
from app.infrastructure.container import Container

router = Router()

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Rastrear Envío")],
            [KeyboardButton(text="📝 Nueva PQR")]
        ],
        resize_keyboard=True
    )

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "¡Hola! Soy el asistente virtual de Interrapidisimo 📦.\n\n"
        "Puedes hacerme cualquier pregunta sobre nuestras políticas de envíos o usar los botones abajo.",
        reply_markup=get_main_keyboard()
    )

@router.message(F.text == "📦 Rastrear Envío")
async def track_package(message: Message, state: FSMContext):
    await state.set_state(InterrapidisimoFlow.waiting_for_tracking_number)
    await message.answer("Por favor, ingresa tu número de guía de 12 dígitos.")

@router.message(InterrapidisimoFlow.waiting_for_tracking_number)
@inject
async def process_tracking(
    message: Message, 
    state: FSMContext,
    assistant_service: AssistantService = Provide[Container.assistant_service]
):
    if assistant_service.validate_tracking_number(message.text):
        info = assistant_service.get_tracking_status(message.text)
        await message.answer(
            f"✅ *Guía:* `{info.guide_number}`\n"
            f"📍 *Estado:* {info.status}\n"
            f"🚚 *Entrega aproximada:* {info.estimated_delivery}.", 
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
    else:
        await message.answer("❌ El formato es incorrecto. Debe tener 12 números.")

# --- FLUJO: PQR ---
@router.message(F.text == "📝 Nueva PQR")
async def start_pqr(message: Message, state: FSMContext):
    await state.set_state(InterrapidisimoFlow.waiting_for_pqr_details)
    await message.answer("Lamentamos los inconvenientes. Por favor, describe tu problema:")

@router.message(InterrapidisimoFlow.waiting_for_pqr_details)
@inject
async def process_pqr(
    message: Message, 
    state: FSMContext,
    assistant_service: AssistantService = Provide[Container.assistant_service]
):
    radicado = assistant_service.create_pqr(message.from_user.first_name, message.text)
    await message.answer(
        f"✅ Hemos registrado tu PQR exitosamente.\n"
        f"Tu número de radicado es *{radicado}*.", 
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

@router.message()
@inject
async def respond_with_rag(
    message: Message, 
    state: FSMContext,
    assistant_service: AssistantService = Provide[Container.assistant_service]
):
    """
    Cualquier mensaje que no coincida con un flujo específico, es enviado al RAG.
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
        print(f"Error: {e}")
