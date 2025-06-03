from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
from pydantic_settings import BaseSettings

class WebhookConfig(BaseModel):
    url: str = Field(..., min_length=1)
    secret: str = Field(..., min_length=1)
    events: List[str] = []
    active: bool = True
    metadata: Optional[Dict[str, Any]] = None

class WebhookLog(BaseModel):
    id: str
    webhook_id: str
    event: str
    payload: Dict[str, Any]
    response_status: int
    response_body: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime

class WebhookEvent(BaseModel):
    event: str
    payload: Dict[str, Any]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
