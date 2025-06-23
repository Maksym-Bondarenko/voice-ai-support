from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ValidateRequest(BaseModel):
    tracking_id: str
    postal_code: str

class ValidateResponse(BaseModel):
    tracking_id: str
    customer_name: str
    eligible: bool
    status: str
    scheduled_at: Optional[datetime] = None

class RescheduleRequest(BaseModel):
    tracking_id: str
    new_slot: datetime

class GenericAck(BaseModel):
    ok: bool
    detail: Optional[str] = None