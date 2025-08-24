import io
import pytest
from fastapi import UploadFile, HTTPException
from PIL import Image
from unittest.mock import patch
from services.photo_service import PhotoService
from models import Photo, Subject

class TestUploadFile(UploadFile):
    def __init__(self, filename: str, file: io.BytesIO, content_type: str):
        headers = {"content-type": content_type}
        super().__init__(filename=filename, file=file, headers=headers)

def create_test_image():
    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(file, 'jpeg')
    file.name = "test.jpg"
    file.seek(0)
    return file

@pytest.fixture
def photo_service(db_session):
    return PhotoService(db_session)

@pytest.fixture
def upload_file():
    file = create_test_image()
    return TestUploadFile(filename=file.name, file=file, content_type="image/jpeg")

@pytest.fixture
def user_id():
    return 1

@pytest.fixture
def gallery_password():
    return "securepassword"

@pytest.fixture
def subject_name():
    return "testsubject"

def add_subject(db_session, user_id, subject_name):
    subject = Subject(name=subject_name, user_id=user_id)
    db_session.add(subject)
    db_session.commit()
    db_session.refresh(subject)
    return subject

def add_photo(db_session, user_id, subject=None, filename="photo.jpg"):
    photo = Photo(
        filename=filename,
        original_encrypted_data=b"encrypted",
        original_encryption_salt=b"salt",
        original_nonce=b"nonce",
        original_tag=b"tag",
        encrypted_data=b"encrypted",
        encryption_salt=b"salt",
        nonce=b"nonce",
        tag=b"tag",
        mime_type="image/jpeg",
        owner_id=user_id,
        subject_id=subject.id if subject else None,
        filter_applied=None
    )
    db_session.add(photo)
    db_session.commit()
    db_session.refresh(photo)
    return photo

@patch("services.photo_service.encrypt_image", return_value=(b"encdata", b"salt", b"nonce", b"tag"))
@patch("services.photo_service.predict_image", return_value="predicted_subject")
def test_upload_photo_predict_subject(mock_predict, mock_encrypt, photo_service, upload_file, gallery_password, user_id):
    photo = photo_service.upload_photo(upload_file, gallery_password, "noSubject", user_id)
    assert photo.filename == upload_file.filename
    assert photo.subject_id is not None
    assert photo.owner_id == user_id
    mock_predict.assert_called()
    mock_encrypt.assert_called()

@patch("services.photo_service.encrypt_image", return_value=(b"enc", b"s", b"n", b"t"))
def test_upload_photo_with_existing_subject(mock_encrypt, photo_service, upload_file, gallery_password, user_id, db_session):
    subject = add_subject(db_session, user_id, "existing_subject")
    photo = photo_service.upload_photo(upload_file, gallery_password, "existing_subject", user_id)
    assert photo.subject_id == subject.id
    assert photo.owner_id == user_id

def test_get_photo_success(photo_service, db_session, user_id, gallery_password):
    photo = add_photo(db_session, user_id)
    with patch("services.photo_service.decrypt_image", return_value=b"decrypteddata") as mock_decrypt:
        result_data, mime_type = photo_service.get_photo(photo.id, gallery_password, user_id)
        assert result_data == b"decrypteddata"
        assert mime_type == photo.mime_type
        mock_decrypt.assert_called_once()

def test_get_photo_not_found(photo_service, user_id, gallery_password):
    with pytest.raises(HTTPException) as exc:
        photo_service.get_photo(9999, gallery_password, user_id)
    assert exc.value.status_code == 404

def test_get_photo_decrypt_failure(photo_service, db_session, gallery_password, user_id):
    photo = add_photo(db_session, user_id)
    with patch("services.photo_service.decrypt_image", side_effect=Exception("fail")):
        with pytest.raises(HTTPException) as exc:
            photo_service.get_photo(photo.id, gallery_password, user_id)
        assert exc.value.status_code == 400

def test_get_user_photos(photo_service, db_session, user_id):
    add_photo(db_session, user_id)
    add_photo(db_session, user_id+1)
    photos = photo_service.get_user_photos(user_id)
    assert all(photo.owner_id == user_id for photo in photos)
    assert len(photos) == 1

def test_duplicate_photo_success(photo_service, db_session, user_id):
    photo = add_photo(db_session, user_id, filename="orig.jpg")
    duplicated = photo_service.duplicate_photo(photo.id, user_id)
    assert duplicated.filename == "orig_duplicated.jpg"
    assert duplicated.owner_id == user_id
    assert duplicated.id != photo.id

def test_duplicate_photo_not_found(photo_service, user_id):
    with pytest.raises(HTTPException) as exc:
        photo_service.duplicate_photo(9999, user_id)
    assert exc.value.status_code == 404

def test_update_photo_subject_creates_new_subject(photo_service, db_session, user_id):
    photo = add_photo(db_session, user_id)
    new_subject_name = "NewSubject"
    updated_photo = photo_service.update_photo_subject(photo.id, new_subject_name, user_id)
    assert updated_photo.subject_id is not None
    subject = db_session.query(Subject).filter(Subject.id == updated_photo.subject_id).first()
    assert subject.name == new_subject_name

def test_update_photo_subject_with_existing(photo_service, db_session, user_id):
    subject = add_subject(db_session, user_id, "ExistingSubject")
    photo = add_photo(db_session, user_id)
    updated_photo = photo_service.update_photo_subject(photo.id, "ExistingSubject", user_id)
    assert updated_photo.subject_id == subject.id

def test_update_photo_subject_photo_not_found(photo_service, user_id):
    with pytest.raises(HTTPException) as exc:
        photo_service.update_photo_subject(9999, "AnySubject", user_id)
    assert exc.value.status_code == 404

@patch("services.photo_service.decrypt_image", return_value=create_test_image().getvalue())
@patch("services.photo_service.encrypt_image", return_value=(b"encrypted", b"salt", b"nonce", b"tag"))
def test_apply_filter_none_restores_original(mock_encrypt, mock_decrypt, photo_service, db_session, user_id, gallery_password):
    photo = add_photo(db_session, user_id)
    updated_photo = photo_service.apply_filter_to_photo(photo.id, "none", gallery_password, user_id)
    assert updated_photo.filter_applied is None
    assert updated_photo.encrypted_data == photo.original_encrypted_data

@patch("services.photo_service.decrypt_image", return_value=create_test_image().getvalue())
@patch("services.photo_service.encrypt_image", return_value=(b"encrypted", b"salt", b"nonce", b"tag"))
def test_apply_filter_sepia(mock_encrypt, mock_decrypt, photo_service, db_session, user_id, gallery_password):
    photo = add_photo(db_session, user_id)
    updated_photo = photo_service.apply_filter_to_photo(photo.id, "sepia", gallery_password, user_id)
    assert updated_photo.filter_applied == "sepia"
    mock_encrypt.assert_called_once()

@patch("services.photo_service.decrypt_image", return_value=create_test_image().getvalue())
@patch("services.photo_service.encrypt_image", return_value=(b"encrypted", b"salt", b"nonce", b"tag"))
def test_apply_filter_black_and_white(mock_encrypt, mock_decrypt, photo_service, db_session, user_id, gallery_password):
    photo = add_photo(db_session, user_id)
    updated_photo = photo_service.apply_filter_to_photo(photo.id, "black and white", gallery_password, user_id)
    assert updated_photo.filter_applied == "black and white"

@patch("services.photo_service.decrypt_image", return_value=create_test_image().getvalue())
@patch("services.photo_service.encrypt_image", return_value=(b"encrypted", b"salt", b"nonce", b"tag"))
def test_apply_filter_color_inversion(mock_encrypt, mock_decrypt, photo_service, db_session, user_id, gallery_password):
    photo = add_photo(db_session, user_id)
    updated_photo = photo_service.apply_filter_to_photo(photo.id, "color inversion", gallery_password, user_id)
    assert updated_photo.filter_applied == "color inversion"

def test_apply_filter_invalid_filter(photo_service, db_session, user_id, gallery_password):
    photo = add_photo(db_session, user_id)
    with pytest.raises(HTTPException) as exc:
        photo_service.apply_filter_to_photo(photo.id, "invalid-filter", gallery_password, user_id)
    assert exc.value.status_code == 400

def test_apply_filter_photo_not_found(photo_service, user_id, gallery_password):
    with pytest.raises(HTTPException) as exc:
        photo_service.apply_filter_to_photo(9999, "none", gallery_password, user_id)
    assert exc.value.status_code == 404

@patch("services.photo_service.decrypt_image", side_effect=Exception("fail"))
def test_apply_filter_decrypt_fail(mock_decrypt, photo_service, db_session, user_id, gallery_password):
    photo = add_photo(db_session, user_id)
    with pytest.raises(HTTPException) as exc:
        photo_service.apply_filter_to_photo(photo.id, "sepia", gallery_password, user_id)
    assert exc.value.status_code == 400
