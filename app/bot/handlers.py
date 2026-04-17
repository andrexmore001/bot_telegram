from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.rag.engine import ask_question
from app.bot.states import InterrapidisimoFlow

router = Router()

def get_main_keyboard():
    """Teclado persistente con opciones rápidas."""
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
        "Puedes hacerme cualquier pregunta sobre nuestras políticas de envíos (tiempos, embalaje, líquidos) "
        "o usar los botones abajo para un flujo automático.",
        reply_markup=get_main_keyboard()
    )

# --- FLUJO: RASTREAR ENVÍO ---
@router.message(F.text == "📦 Rastrear Envío")
async def track_package(message: Message, state: FSMContext):
    await state.set_state(InterrapidisimoFlow.waiting_for_tracking_number)
    await message.answer("Por favor, ingresa tu número de guía de 12 dígitos.")

@router.message(InterrapidisimoFlow.waiting_for_tracking_number)
async def process_tracking(message: Message, state: FSMContext):
    if len(message.text) == 12 and message.text.isdigit():
        await message.answer(
            f"✅ *Guía:* `{message.text}`\n"
            f"📍 *Estado:* EN TRÁNSITO hacia la bodega local.\n"
            f"🚚 *Entrega aproximada:* Mañana.", 
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
    else:
        await message.answer("❌ El formato es incorrecto. Debe tener 12 números. Intenta de nuevo o presiona /start para salir.")

# --- FLUJO: PQR ---
@router.message(F.text == "📝 Nueva PQR")
async def start_pqr(message: Message, state: FSMContext):
    await state.set_state(InterrapidisimoFlow.waiting_for_pqr_details)
    await message.answer("Lamentamos los inconvenientes. Por favor, describe tu problema:")

@router.message(InterrapidisimoFlow.waiting_for_pqr_details)
async def process_pqr(message: Message, state: FSMContext):
    # Simulamos el guardado de una PQR
    await message.answer(
        "✅ Hemos registrado tu PQR exitosamente.\n"
        "Tu número de radicado es *PQR-93821*.", 
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

# --- RESPUESTA LIBRE (RAG LLAMAINDEX) ---
@router.message()
async def respond_with_rag(message: Message, state: FSMContext):
    """
    Cualquier mensaje que no coincida con un flujo específico o comando,
    es enviado el RAG para ser contestado en base a los documentos.
    """
    if message.text:
        msg = await message.answer("🤔 Consultando manuales logísticos de Interrapidisimo...")
        try:
            # Consultar documentos mediante LlamaIndex
            response = ask_question(message.text)
            await msg.edit_text(response)
        except Exception as e:
            await msg.edit_text("Lo siento, tuve un problema procesando tu pregunta. Intenta de nuevo más tarde.")
            print(f"Error en RAG: {e}")
