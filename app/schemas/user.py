from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    username: EmailStr
    password: str


class UserLogin(BaseModel):
    username: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str

