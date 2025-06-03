from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class Token(BaseModel):
    """Token schema"""
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """Token payload schema"""
    sub: Optional[int] = None
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class TokenData(BaseModel):
    """Token data schema"""
    email: Optional[str] = None
    scopes: list[str] = []

class TokenCreate(BaseModel):
    """Token creation schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenRefresh(BaseModel):
    """Token refresh schema"""
    refresh_token: str

class TokenRefreshResponse(Token):
    """Token refresh response schema"""
    refresh_token: str
    expires_in: int
