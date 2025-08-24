# services/subject_service.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from models import Subject


class SubjectService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_subjects(self, user_id: int):
        return self.db.query(Subject).filter(Subject.user_id == user_id).all()

    def create_subject(self, name: str, user_id: int):
        found_subject = self.db.query(Subject).filter_by(user_id=user_id, name=name).first()

        if found_subject:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Subject already exists")

        subject = Subject(name=name, user_id=user_id)
        self.db.add(subject)
        self.db.commit()
        self.db.refresh(subject)

        return subject