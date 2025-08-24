# main.py
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from starlette import status

from auth import get_current_user
from database import  get_db
from models import User
from services.auth_service import AuthService
from services.photo_service import PhotoService
from services.subject_service import SubjectService
import schemas

app = FastAPI(title="Image Gallery API")

@app.post(
    "/register",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Register a user by providing a unique username and password. Returns the created user details upon success.",
    responses={
        201: {"description": "User registered successfully"},
        400: {"description": "Username already registered"},
    },
    tags=["Authentication"],
)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.register_user(user.username, user.password)


@app.post(
    "/login",
    response_model=schemas.Token,
    status_code=status.HTTP_200_OK,
    summary="Log in and obtain an access token",
    description="Authenticate with username and password to obtain a JWT access token valid for 30 minutes.",
    responses={
        200: {"description": "Access token returned successfully"},
        401: {"description": "Invalid username or password"},
    },
    tags=["Authentication"],
)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.login_user(user.username, user.password)


@app.post("/photos/", response_model=schemas.PhotoOut)
async def upload_photo(
        file: UploadFile = File(...),
        gallery_password: str = Form(...),
        subject_name: str = Form(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    photo_service = PhotoService(db)
    return photo_service.upload_photo(file, gallery_password, subject_name, current_user.id)


@app.get("/photos/{photo_id}")
async def get_photo(
        photo_id: int,
        gallery_password: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    photo_service = PhotoService(db)
    decrypted_data, mime_type = photo_service.get_photo(photo_id, gallery_password, current_user.id)

    return Response(
        content=decrypted_data,
        media_type=mime_type
    )


@app.get("/photos/", response_model=list[schemas.PhotoOut])
def get_user_photos(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    photo_service = PhotoService(db)
    return photo_service.get_user_photos(current_user.id)


@app.get(
    "/subjects/",
    response_model=list[schemas.SubjectOut],
    summary="Get all subjects for the current user",
    description="Retrieve the list of all subjects (categories or tags) belonging to the authenticated user.",
    responses={
        200: {"description": "List of subjects returned successfully"},
        401: {"description": "Unauthorized - user authentication required"}
    },
    tags=["Subjects"],
)
def get_user_subjects(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    subject_service = SubjectService(db)
    return subject_service.get_user_subjects(current_user.id)


@app.post(
    "/subject/",
    response_model=schemas.SubjectOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new subject for the current user",
    description="Create a subject (category or tag) with a unique name for the authenticated user.",
    responses={
        201: {"description": "Subject created successfully"},
        401: {"description": "Unauthorized - user authentication required"},
        409: {"description": "Subject with the given name already exists for this user"}
    },
    tags=["Subjects"],
)
def create_subject(
        name: str = Form(..., example="Vacation"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    subject_service = SubjectService(db)
    return subject_service.create_subject(name, current_user.id)


@app.post("/photos/{photo_id}/duplicate", response_model=schemas.PhotoOut)
def duplicate_photo(
        photo_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    photo_service = PhotoService(db)
    return photo_service.duplicate_photo(photo_id, current_user.id)


@app.patch("/photos/{photo_id}/subject", response_model=schemas.PhotoOut)
def update_photo_subject(
        photo_id: int,
        subject_name: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    photo_service = PhotoService(db)
    return photo_service.update_photo_subject(photo_id, subject_name, current_user.id)


@app.patch("/photos/{photo_id}/filter", response_model=schemas.PhotoOut)
async def apply_filter_to_photo(
        photo_id: int,
        filter_name: str = Form(...),
        gallery_password: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    photo_service = PhotoService(db)
    return photo_service.apply_filter_to_photo(photo_id, filter_name, gallery_password, current_user.id)


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)