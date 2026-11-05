from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


UserRoleValue = Literal["admin", "recruiter"]


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    role: UserRoleValue
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
