import os
import json
from typing import Dict, List
from app.domain.ports.user_repository import UserRepositoryPort
from app.domain.models.user import UserAuthorization
from app.infrastructure.logging.logger import logger

class JsonUserRepository(UserRepositoryPort):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = self._load_data()

    def _load_data(self) -> UserAuthorization:
        if not os.path.exists(self.file_path):
            logger.info(f"Creando nuevo archivo de usuarios en {self.file_path}")
            initial_data = UserAuthorization()
            self._save_to_disk(initial_data)
            return initial_data
        
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                return UserAuthorization(**content)
        except Exception as e:
            logger.error(f"Error cargando base de usuarios: {e}")
            return UserAuthorization()

    def _save_to_disk(self, data: UserAuthorization):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data.model_dump(), f, indent=2)
        except Exception as e:
            logger.error(f"Error guardando base de usuarios a disco: {e}")

    def is_verified(self, user_id: int) -> bool:
        return str(user_id) in self.data.verified_ids

    def is_phone_allowed(self, phone: str) -> bool:
        # Normalizar teléfono (quitar + y espacios)
        clean_phone = phone.replace("+", "").replace(" ", "")
        return clean_phone in self.data.whitelist_phones

    def authorize_user(self, user_id: int, phone: str):
        clean_phone = phone.replace("+", "").replace(" ", "")
        self.data.verified_ids[str(user_id)] = clean_phone
        self._save_to_disk(self.data)
        logger.info(f"Usuario {user_id} verificado con el teléfono {phone}")

    def get_whitelist(self) -> List[str]:
        return self.data.whitelist_phones

    def add_to_whitelist(self, phone: str):
        clean_phone = phone.replace("+", "").replace(" ", "")
        if clean_phone not in self.data.whitelist_phones:
            self.data.whitelist_phones.append(clean_phone)
            self._save_to_disk(self.data)
            logger.info(f"Teléfono {clean_phone} agregado a la lista blanca")

    def remove_from_whitelist(self, phone: str):
        clean_phone = phone.replace("+", "").replace(" ", "")
        if clean_phone in self.data.whitelist_phones:
            self.data.whitelist_phones.remove(clean_phone)
            # También removemos cualquier vinculación de Telegram ID asociada
            keys_to_remove = [k for k, v in self.data.verified_ids.items() if v == clean_phone]
            for k in keys_to_remove:
                del self.data.verified_ids[k]
            
            self._save_to_disk(self.data)
            logger.info(f"Teléfono {clean_phone} eliminado de la lista blanca")

