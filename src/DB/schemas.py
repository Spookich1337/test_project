from pydantic import BaseModel
from typing import Optional
from .DBconfig import UserRole


class UserBase(BaseModel):
    name: str
    email: str
    password: str
    role: UserRole


class UserResponse(UserBase):
    id: int


class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    id: int
    name: Optional[str] = None
    role: Optional[UserRole] = None
    email: Optional[str] = None
    password: Optional[str] = None


class UserList(BaseModel):
    count: int
    users: list[UserResponse]


class NoteBase(BaseModel):
    user_id: int
    text: str
    for_admin: bool
    

class NoteResponse(NoteBase):
    id: int


class NoteCreate(NoteBase):
    pass


class NoteUpdate(NoteBase):
    id: int
    text: Optional[str] = None
    for_admin: Optional[bool] = None


class NoteList(BaseModel):
    count: int
    notes: list[NoteResponse]