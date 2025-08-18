# auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from starlette.status import HTTP_401_UNAUTHORIZED

from database import SessionLocal
from models import User
from utils import verify_password  # rămâne importul pentru verificarea parolei

SECRET_KEY = "your_fixed_secret_key_which_is_at_least_32_bytes_long"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# înlocuire: HTTP Bearer (nu e OAuth2)
bearer_scheme = HTTPBearer()  # automat adaugă schema Bearer în OpenAPI

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    token este un obiect HTTPAuthorizationCredentials cu .scheme (ex: "Bearer")
    și .credentials (token-ul JWT efectiv).
    """
    if token is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    jwt_token = token.credentials  # tokenul JWT (fără prefix)
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # funcție locală pentru a evita import circular
    def get_user_by_username(db: Session, username: str):
        return db.query(User).filter(User.username == username).first()

    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception

    return user
