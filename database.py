# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./gallery.db"  # Pentru început, putem folosi SQLite

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # doar pentru SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependență pentru DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()