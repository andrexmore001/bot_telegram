from pydantic import BaseModel
from typing import Dict, List

class UserAuthorization(BaseModel):
    """
    Modelo para gestionar la autorización de usuarios.
    """
    whitelist_phones: List[str] = []
    verified_ids: Dict[str, str] = {}  # telegram_id -> phone_number
