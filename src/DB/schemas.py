from pydantic import BaseModel
from typing import Optional
from .DBconfig import UserRole


class UserBase(BaseModel):
    role: UserRole
    email: str
    password: str


class UserResponse(UserBase):
    id: int


class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    id: int
    role: Optional[UserRole] = None
    email: Optional[str] = None
    password: Optional[str] = None


class NoteBase(BaseModel):
    text: str
    in_black_list: bool
    

class NoteResponse(NoteBase):
    id: int


class NoteCreate(NoteBase):
    pass


class NoteUpdate(NoteBase):
    id: int
    text: Optional[str] = None
    in_black_list: Optional[bool] = None