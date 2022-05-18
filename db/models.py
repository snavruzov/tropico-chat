from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from db.core import IDModelMixin


class WelcomeChat(IDModelMixin):
    name: str
    message: Optional[str]
    lang: str
    created_at: int


class IntroChat(BaseModel):
    name: str
    avatar: Optional[str] = None
    message: str
    quick_replies: Optional[list] = None
    lang: str


class UserInfo(IDModelMixin):
    name: str
    email: Optional[str]
    phone: Optional[str]
    city: Optional[str]
    created_at: datetime
    session_id: str
    lang: str
    context: Optional[str] = None
    is_default: Optional[bool] = True


class UserChat(IDModelMixin):
    name: str
    avatar: Optional[str] = None
    chat_id: int
    message: Optional[str]
    direction: Optional[str] = 'IN'
    created_at: int


class UserForm(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class OperatorTG(BaseModel):
    name: str
    chat_id: str


