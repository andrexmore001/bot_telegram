from pydantic import BaseModel
from typing import Optional

class TrackingInfo(BaseModel):
    guide_number: str
    status: str
    estimated_delivery: str

class PQRRequest(BaseModel):
    user_name: str
    details: str
    reference_number: Optional[str] = None
