# models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    photos = relationship("Photo", back_populates="owner")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))  # Adăugăm user_id pentru proprietate

    photos = relationship("Photo", back_populates="subject")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filter_applied = Column(String, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Fields for the original encrypted image
    original_encrypted_data = Column(LargeBinary, nullable=False)
    original_encryption_salt = Column(LargeBinary, nullable=False)
    original_nonce = Column(LargeBinary, nullable=False)
    original_tag = Column(LargeBinary, nullable=False)

    # Fields for the current (possibly filtered) encrypted image
    encrypted_data = Column(LargeBinary, nullable=False)
    encryption_salt = Column(LargeBinary, nullable=False)
    nonce = Column(LargeBinary, nullable=False)
    tag = Column(LargeBinary, nullable=False)

    mime_type = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)

    owner = relationship("User", back_populates="photos")
    subject = relationship("Subject", back_populates="photos")
