# services/auth_service.py
from datetime import timedelta
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from auth import create_access_token, verify_hashed_password
import crud


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, username: str, password: str):
        db_user = crud.get_user_by_username(self.db, username)
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        return crud.create_user(self.db, username, password)

    def login_user(self, username: str, password: str):
        db_user = crud.get_user_by_username(self.db, username)
        if not db_user or not verify_hashed_password(password, db_user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": db_user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}