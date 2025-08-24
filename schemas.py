from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(..., example="john_doe")
    password: str = Field(..., example="secretpassword123")

class UserOut(BaseModel):
    id: int = Field(..., example=1)
    username: str = Field(..., example="john_doe")

    class Config:
        orm_mode = True  # allows returning SQLAlchemy models directly

class UserLogin(BaseModel):
    username: str = Field(..., example="john_doe")
    password: str = Field(..., example="secretpassword123")

class Token(BaseModel):
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field(..., example="bearer")

class PhotoBase(BaseModel):
    filename: str = Field(..., example="beach_sunset.jpg")
    filter_applied: Optional[str] = Field(None, example="sepia")

class PhotoCreate(PhotoBase):
    gallery_password: str = Field(..., example="galleryPass123")
    subject_name: Optional[str] = Field(None, example="Holiday")

class PhotoOut(PhotoBase):
    id: int = Field(..., example=101)
    uploaded_at: datetime = Field(..., example="2025-08-20T15:23:01Z")
    owner_id: int = Field(..., example=1)
    subject_id: Optional[int] = Field(None, example=5)
    subject_name: Optional[str] = Field(None, example="Holiday")
    mime_type: str = Field(..., example="image/jpeg")

    class Config:
        orm_mode = True

class SubjectBase(BaseModel):
    name: str = Field(..., example="Vacation")

class SubjectOut(SubjectBase):
    id: int = Field(..., example=5)
    user_id: int = Field(..., example=1)
    photos: list[PhotoOut] = []

    class Config:
        orm_mode = True
