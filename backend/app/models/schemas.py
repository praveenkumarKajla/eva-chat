from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
from datetime import datetime

class User(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

class UserInDB(User):
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class Message(BaseModel):
    id: uuid.UUID
    content: str
    sender: uuid.UUID
    timestamp: datetime
    role: str  # 'user' or 'assistant'

class MessageCreate(BaseModel):
    content: str
    id: uuid.UUID