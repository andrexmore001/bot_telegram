import json
import os
import uuid
from datetime import datetime
from app.domain.ports.pqr_repository import PQRRepositoryPort
from app.domain.models.shipping import PQRRequest

class JsonPQRRepository(PQRRepositoryPort):
    def __init__(self, file_path: str = "data/pqrs.json"):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def save(self, pqr: PQRRequest) -> str:
        """Guarda la PQR en un archivo JSON."""
        radicado = f"PQR-{uuid.uuid4().hex[:8].upper()}"
        
        new_entry = {
            "radicado": radicado,
            "user_name": pqr.user_name,
            "details": pqr.details,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.file_path, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(new_entry)
            f.seek(0)
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        return radicado
