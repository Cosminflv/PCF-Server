# main.py
from datetime import timedelta

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from starlette import status

import crud
import schemas
from models import User, Photo, Subject
from database import SessionLocal, Base, engine
from auth import get_current_user, verify_password, create_access_token
from crypto_utils import encrypt_image

# Base.metadata.drop_all(bind=engine)
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Image Gallery API")

# Dependență pentru DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Endpoint pentru înregistrare
@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db, user.username, user.password)


# Endpoint pentru autentificare
@app.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, user.username)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/photos/", response_model=schemas.PhotoOut)
async def upload_photo(
        file: UploadFile = File(...),
        gallery_password: str = Form(...),
        subject_name: str = Form(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # Citirea imaginii
    image_data = await file.read()

    # Criptarea imaginii
    encrypted_data, salt, nonce, tag = encrypt_image(image_data, gallery_password)

    # Gestionare subiect
    subject = None
    if subject_name:
        subject = db.query(Subject).filter(
            Subject.name == subject_name,
            Subject.user_id == current_user.id
        ).first()
        if not subject:
            subject = Subject(name=subject_name, user_id=current_user.id)
            db.add(subject)
            db.commit()
            db.refresh(subject)

    # Crearea înregistrării foto
    photo = Photo(
        filename=file.filename,
        encrypted_data=encrypted_data,
        encryption_salt=salt,
        nonce=nonce,
        tag=tag,
        mime_type=file.content_type,
        owner_id=current_user.id,
        subject_id=subject.id if subject else None
    )

    db.add(photo)
    db.commit()
    db.refresh(photo)

    return photo


from fastapi.responses import Response
from crypto_utils import decrypt_image

@app.get("/photos/{photo_id}")
async def get_photo(
        photo_id: int,
        gallery_password: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    photo = db.query(Photo).filter(
        Photo.id == photo_id,
        Photo.owner_id == current_user.id
    ).first()

    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    try:
        decrypted_data = decrypt_image(
            photo.encrypted_data,
            photo.encryption_salt,
            photo.nonce,
            photo.tag,
            gallery_password
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail="Decryption failed")

    return Response(
        content=decrypted_data,
        media_type=photo.mime_type
    )

@app.get("/photos/", response_model=list[schemas.PhotoOut])
def get_user_photos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    photos = db.query(Photo).filter(Photo.owner_id == current_user.id).all()
    return photos

@app.get("/subjects/", response_model=list[schemas.SubjectOut])
def get_user_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    subjects = db.query(Subject).filter(Subject.user_id == current_user.id).all()
    return subjects

@app.post("/subject/", response_model=schemas.SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(
    name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # find existing subject (first() returns an instance or None)
    found_subject = db.query(Subject).filter_by(user_id=current_user.id, name=name).first()

    if found_subject:
        # either return existing or raise a 409 conflict
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Subject already exists")

    subject = Subject(name=name, user_id=current_user.id)
    db.add(subject)
    db.commit()
    db.refresh(subject)

    return subject

@app.post("/photos/{photo_id}/duplicate", response_model=schemas.PhotoOut)
def duplicate_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the original photo
    original_photo = db.query(Photo).filter(
        Photo.id == photo_id,
        Photo.owner_id == current_user.id
    ).first()

    if not original_photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    filename_parts = original_photo.filename.split('.')
    if len(filename_parts) > 1:
        base_name = '.'.join(filename_parts[:-1])
        extension = filename_parts[-1]
        new_filename = f"{base_name}_duplicated.{extension}"
    else:
        new_filename = f"{original_photo.filename}_duplicated"

    duplicated_photo = Photo(
        filename=new_filename,
        encrypted_data=original_photo.encrypted_data,
        encryption_salt=original_photo.encryption_salt,
        nonce=original_photo.nonce,
        tag=original_photo.tag,
        mime_type=original_photo.mime_type,
        owner_id=current_user.id,
        subject_id=original_photo.subject_id,
        filter_applied=original_photo.filter_applied
    )

    db.add(duplicated_photo)
    db.commit()
    db.refresh(duplicated_photo)

    return duplicated_photo


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)
