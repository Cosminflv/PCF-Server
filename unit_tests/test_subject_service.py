import pytest
from fastapi import HTTPException
from starlette import status

from services.subject_service import SubjectService
from models import Subject

@pytest.fixture
def subject_service(db_session):
    return SubjectService(db_session)

def test_get_user_subjects_empty(subject_service):
    user_id = 1
    subjects = subject_service.get_user_subjects(user_id)
    assert subjects == []

def test_create_subject_success(subject_service, db_session):
    user_id = 1
    name = "Math"
    subject = subject_service.create_subject(name, user_id)
    assert subject.name == name
    assert subject.user_id == user_id

    # Verify it is persisted
    persisted = db_session.query(Subject).filter_by(id=subject.id).one_or_none()
    assert persisted is not None
    assert persisted.name == name

def test_create_subject_already_exists(subject_service, db_session):
    user_id = 1
    name = "Science"
    # create existing subject directly
    existing_subject = Subject(name=name, user_id=user_id)
    db_session.add(existing_subject)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        subject_service.create_subject(name, user_id)

    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert exc.value.detail == "Subject already exists"

def test_get_user_subjects_nonempty(subject_service, db_session):
    user_id = 2
    # Add subjects for this user
    sub1 = Subject(name="Physics", user_id=user_id)
    sub2 = Subject(name="Chemistry", user_id=user_id)
    # Add subject for different user (should not be returned)
    sub3 = Subject(name="History", user_id=user_id+1)
    db_session.add_all([sub1, sub2, sub3])
    db_session.commit()

    subjects = subject_service.get_user_subjects(user_id)
    assert len(subjects) == 2
    names = {sub.name for sub in subjects}
    assert names == {"Physics", "Chemistry"}
