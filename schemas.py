# schemas.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True  # allows returning SQLAlchemy models directly

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PhotoBase(BaseModel):
    filename: str
    filter_applied: Optional[str] = None

class PhotoCreate(PhotoBase):
    gallery_password: str
    subject_name: Optional[str] = None

class PhotoOut(PhotoBase):
    id: int
    uploaded_at: datetime
    owner_id: int
    subject_id: Optional[int] = None
    subject_name: Optional[str] = None
    mime_type: str

    class Config:
        orm_mode = True

class SubjectBase(BaseModel):
    name: str

class SubjectOut(SubjectBase):
    id: int
    user_id: int
    photos: list[PhotoOut] = []

    class Config:
        orm_mode = True
