import json
import os
from typing import List, Optional
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from aiogram import Bot
from aiogram.types import BufferedInputFile

from app.infrastructure.adapters.api.auth_service import auth_service

router = APIRouter(prefix="/admin", tags=["admin"])

class Channel(BaseModel):
    id: str
    name: str

@router.get("/channels", response_model=List[Channel])
async def get_channels(
    request: Request,
    user: dict = Depends(auth_service.verify_token)
):
    container = request.app.state.container
    user_repo = container.user_repository()
    
    channels_data = await user_repo.get_channels()
    return channels_data

@router.post("/send")
async def send_broadcast(
    request: Request,
    channels: str = Form(...), # JSON string list of IDs
    message: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    user: dict = Depends(auth_service.verify_token)
):
    bot: Bot = request.app.state.bot

    channel_ids = json.loads(channels)
    
    success_count = 0
    fail_count = 0
    errors = []

    for chat_id in channel_ids:
        try:
            if file:
                # Leer contenido del archivo
                file_content = await file.read()
                # Volver al inicio para el siguiente canal (aunque BufferedInputFile hace copia)
                await file.seek(0)
                
                input_file = BufferedInputFile(file_content, filename=file.filename)
                
                await bot.send_document(
                    chat_id=chat_id,
                    document=input_file,
                    caption=message
                )
            elif message:
                await bot.send_message(
                    chat_id=chat_id,
                    text=message
                )
            success_count += 1
        except Exception as e:
            from app.infrastructure.logging.logger import logger
            logger.error(f"Error interno enviando mensaje al canal {chat_id}: {str(e)}")
            fail_count += 1
            errors.append({"field": "channel_id", "issue": f"Fallo al procesar el canal {chat_id}"})

    return {
        "success": success_count,
        "failed": fail_count,
        "errors": errors
    }


@router.post("/channels")
async def add_channel(
    channel: Channel,
    request: Request,
    user: dict = Depends(auth_service.verify_token)
):
    container = request.app.state.container
    user_repo = container.user_repository()
    
    await user_repo.add_channel(channel.id, channel.name)
    return {"status": "ok", "message": "Canal agregado correctamente"}

@router.delete("/channels/{channel_id}")
async def delete_channel(
    channel_id: str,
    request: Request,
    user: dict = Depends(auth_service.verify_token)
):
    container = request.app.state.container
    user_repo = container.user_repository()
    
    await user_repo.delete_channel(channel_id)
    return {"status": "ok", "message": "Canal eliminado correctamente"}

# --- GESTION DE USUARIOS ---

@router.get("/users")
async def get_authorized_users(
    request: Request,
    user: dict = Depends(auth_service.verify_token)
):
    container = request.app.state.container
    user_repo = container.user_repository()
    return user_repo.get_whitelist()

@router.post("/users")
async def authorize_phone(
    request: Request,
    phone: str = Form(...),
    user: dict = Depends(auth_service.verify_token)
):
    container = request.app.state.container
    user_repo = container.user_repository()
    user_repo.add_to_whitelist(phone)
    return {"status": "ok", "message": f"Teléfono {phone} autorizado"}

@router.delete("/users/{phone}")
async def revoke_phone(
    request: Request,
    phone: str,
    user: dict = Depends(auth_service.verify_token)
):
    container = request.app.state.container
    user_repo = container.user_repository()
    user_repo.remove_from_whitelist(phone)
    return {"status": "ok", "message": f"Acceso revocado para {phone}"}

# --- GESTION DE CONFIGURACION ---

@router.get("/config")
async def get_config(
    user: dict = Depends(auth_service.verify_token)
):
    from app.infrastructure.config.config import config
    # No devolvemos todo por seguridad, solo lo que el admin puede editar
    return {
        "openai_api_key": config.openai_api_key[:8] + "..." if config.openai_api_key else "",
        "telegram_bot_token": config.telegram_bot_token[:8] + "..." if config.telegram_bot_token else "",
        "keycloak_url": config.keycloak_url,
        "keycloak_realm": config.keycloak_realm
    }

@router.patch("/config")
async def update_config(
    updates: dict,
    user: dict = Depends(auth_service.verify_token)
):
    # En un entorno real, aquí actualizaríamos el .env o una base de datos
    # Por ahora, vamos a simular la actualización en el objeto config
    # IMPORTANTE: Esto no persiste tras un reinicio si no se guarda en disco.
    from app.infrastructure.config.config import config
    for key, value in updates.items():
        if hasattr(config, key):
            setattr(config, key, value)
            
    return {"status": "ok", "message": "Configuración actualizada temporalmente"}

