# services/photo_service.py
import io
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from PIL import Image, ImageOps
import numpy as np

from models import Photo, Subject
from crypto_utils import encrypt_image, decrypt_image
from subject_predictor import predict_image


class PhotoService:
    def __init__(self, db: Session):
        self.db = db

    def upload_photo(self, file: UploadFile, gallery_password: str, subject_name: str, user_id: int):
        image_data = file.file.read()

        if subject_name == 'noSubject':
            try:
                subject_name = predict_image(image_data)
            except Exception as e:
                subject_name = "unclassified"

        encrypted_data, salt, nonce, tag = encrypt_image(image_data, gallery_password)

        # Handle subject
        subject = None
        if subject_name:
            subject = self.db.query(Subject).filter(
                Subject.name == subject_name,
                Subject.user_id == user_id
            ).first()
            if not subject:
                subject = Subject(name=subject_name, user_id=user_id)
                self.db.add(subject)
                self.db.commit()
                self.db.refresh(subject)

        photo = Photo(
            filename=file.filename,
            original_encrypted_data=encrypted_data,
            original_encryption_salt=salt,
            original_nonce=nonce,
            original_tag=tag,
            encrypted_data=encrypted_data,
            encryption_salt=salt,
            nonce=nonce,
            tag=tag,
            mime_type=file.content_type,
            owner_id=user_id,
            subject_id=subject.id if subject else None
        )

        self.db.add(photo)
        self.db.commit()
        self.db.refresh(photo)

        return photo

    def get_photo(self, photo_id: int, gallery_password: str, user_id: int):
        photo = self.db.query(Photo).filter(
            Photo.id == photo_id,
            Photo.owner_id == user_id
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

        return decrypted_data, photo.mime_type

    def get_user_photos(self, user_id: int):
        return self.db.query(Photo).filter(Photo.owner_id == user_id).all()

    def duplicate_photo(self, photo_id: int, user_id: int):
        original_photo = self.db.query(Photo).filter(
            Photo.id == photo_id,
            Photo.owner_id == user_id
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
            original_encrypted_data=original_photo.encrypted_data,
            original_encryption_salt=original_photo.encryption_salt,
            original_nonce=original_photo.nonce,
            original_tag=original_photo.tag,
            encrypted_data=original_photo.encrypted_data,
            encryption_salt=original_photo.encryption_salt,
            nonce=original_photo.nonce,
            tag=original_photo.tag,
            mime_type=original_photo.mime_type,
            owner_id=user_id,
            subject_id=original_photo.subject_id,
            filter_applied=original_photo.filter_applied
        )

        self.db.add(duplicated_photo)
        self.db.commit()
        self.db.refresh(duplicated_photo)

        return duplicated_photo

    def update_photo_subject(self, photo_id: int, subject_name: str, user_id: int):
        photo = self.db.query(Photo).filter(
            Photo.id == photo_id,
            Photo.owner_id == user_id
        ).first()

        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")

        subject = None
        if subject_name:
            subject = self.db.query(Subject).filter(
                Subject.name == subject_name,
                Subject.user_id == user_id
            ).first()
            if not subject:
                subject = Subject(name=subject_name, user_id=user_id)
                self.db.add(subject)
                self.db.commit()
                self.db.refresh(subject)

        photo.subject_id = subject.id if subject else None
        self.db.commit()
        self.db.refresh(photo)

        return photo

    def apply_filter_to_photo(self, photo_id: int, filter_name: str, gallery_password: str, user_id: int):
        photo = self.db.query(Photo).filter(
            Photo.id == photo_id,
            Photo.owner_id == user_id
        ).first()

        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")

        # For the "none" filter, restore the original image
        if filter_name == "none":
            photo.encrypted_data = photo.original_encrypted_data
            photo.encryption_salt = photo.original_encryption_salt
            photo.nonce = photo.original_nonce
            photo.tag = photo.original_tag
            photo.filter_applied = None

            self.db.commit()
            self.db.refresh(photo)
            return photo

        # For other filters, decrypt the original image and apply the filter
        try:
            decrypted_data = decrypt_image(
                photo.original_encrypted_data,
                photo.original_encryption_salt,
                photo.original_nonce,
                photo.original_tag,
                gallery_password
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail="Decryption failed")

        # Apply filter
        try:
            image = Image.open(io.BytesIO(decrypted_data))

            if image.mode != 'RGB':
                image = image.convert('RGB')

            if filter_name == "sepia":
                img_array = np.array(image)
                sepia_matrix = np.array([
                    [0.393, 0.769, 0.189],
                    [0.349, 0.686, 0.168],
                    [0.272, 0.534, 0.131]
                ])
                transformed_sepia = np.dot(img_array, sepia_matrix.T).clip(0, 255).astype(np.uint8)
                filtered_image = Image.fromarray(transformed_sepia)

            elif filter_name == "black and white":
                filtered_image = image.convert('L').convert('RGB')

            elif filter_name == "color inversion":
                filtered_image = ImageOps.invert(image)

            else:
                raise HTTPException(status_code=400,
                                    detail="Invalid filter name. Available filters: none, sepia, black and white, color inversion")

            img_byte_arr = io.BytesIO()
            format = image.format if image.format else 'JPEG'
            filtered_image.save(img_byte_arr, format=format)
            filtered_data = img_byte_arr.getvalue()

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error applying filter: {str(e)}")

        # Re-encrypt the filtered image
        encrypted_data, salt, nonce, tag = encrypt_image(filtered_data, gallery_password)

        # Update the photo record
        photo.encrypted_data = encrypted_data
        photo.encryption_salt = salt
        photo.nonce = nonce
        photo.tag = tag
        photo.filter_applied = filter_name

        self.db.commit()
        self.db.refresh(photo)

        return photo