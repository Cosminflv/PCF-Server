import io
from PIL import Image

from models import Subject


def create_test_image():
    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(file, 'jpeg')
    file.name = "test.jpg"
    file.seek(0)
    return file


def test_upload_photo(client, db_session):
    # Register and login first
    client.post("/register", json={"username": "testuser", "password": "testpass"})
    login = client.post("/login", json={"username": "testuser", "password": "testpass"})
    token = login.json()["access_token"]

    # Upload photo
    test_image = create_test_image()
    response = client.post(
        "/photos/",
        files={"file": test_image},
        data={"gallery_password": "testpass", 'subject_name': "my_subject"},
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"RESPONSE: {response.json()}")

    assert response.status_code == 200
    assert response.json()["filename"] == "test.jpg"
    assert response.json()["subject_id"] == 1
    assert response.json()["filter_applied"] is None

def test_upload_photo_no_subject(client, db_session):
    # Register and login first
    client.post("/register", json={"username": "testuser", "password": "testpass"})
    login = client.post("/login", json={"username": "testuser", "password": "testpass"})
    token = login.json()["access_token"]

    # Upload photo
    test_image = create_test_image()
    response = client.post(
        "/photos/",
        files={"file": test_image},
        data={"gallery_password": "testpass", 'subject_name': "noSubject"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "test.jpg"
    assert response.json()["subject_id"] == 1
    assert response.json()["filter_applied"] is None

def test_get_user_photos(client, db_session):
    # Register and login first
    client.post("/register", json={"username": "testuser", "password": "testpass"})
    login = client.post("/login", json={"username": "testuser", "password": "testpass"})
    token = login.json()["access_token"]

    # Upload photo
    test_image = create_test_image()
    response = client.post(
        "/photos/",
        files={"file": test_image},
        data={"gallery_password": "testpass", 'subject_name': "my_subject"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "test.jpg"
    assert response.json()["subject_id"] == 1
    assert response.json()["filter_applied"] is None

    response = client.get("/photos/",
                          headers={"Authorization": f"Bearer {token}"})

    assert  response.status_code == 200

    print("RESPONSE:", response.json())

    assert len(response.json()) > 0

def test_duplicate_photo(client, db_session):
    # Register and login
    client.post("/register", json={"username": "testuser", "password": "testpass"})
    login = client.post("/login", json={"username": "testuser", "password": "testpass"})
    token = login.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Upload a photo using the test image
    test_image = create_test_image()
    upload_response = client.post(
        "/photos/",
        files={"file": ("test.jpg", test_image, "image/jpeg")},
        data={"gallery_password": "testpass", "subject_name": "my_subject"},
        headers=headers
    )
    assert upload_response.status_code == 200
    original_photo = upload_response.json()
    original_photo_id = original_photo["id"]
    original_filename = original_photo["filename"]

    # Duplicate the photo
    duplicate_response = client.post(f"/photos/{original_photo_id}/duplicate", headers=headers)
    assert duplicate_response.status_code == 200

    duplicated_photo = duplicate_response.json()

    # Expected duplicated filename
    if "." in original_filename:
        base_name, extension = original_filename.rsplit(".", 1)
        expected_filename = f"{base_name}_duplicated.{extension}"
    else:
        expected_filename = f"{original_filename}_duplicated"

    assert duplicated_photo["filename"] == expected_filename
    assert duplicated_photo["id"] != original_photo_id
    assert duplicated_photo["owner_id"] == original_photo["owner_id"]

def test_update_photo_subject(client, db_session):
    # Register and login
    client.post("/register", json={"username": "testuser", "password": "testpass"})
    login = client.post("/login", json={"username": "testuser", "password": "testpass"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload a photo to update
    test_image = create_test_image()
    upload_response = client.post(
        "/photos/",
        files={"file": ("test.jpg", test_image, "image/jpeg")},
        data={"gallery_password": "testpass", "subject_name": "original_subject"},
        headers=headers
    )
    assert upload_response.status_code == 200
    photo = upload_response.json()
    photo_id = photo["id"]
    assert photo["subject_id"] == 1  # Assuming first subject ID is 1

    # Update photo's subject to a new subject
    new_subject_name = "new_subject"
    update_response = client.patch(
        f"/photos/{photo_id}/subject",
        data={"subject_name": new_subject_name},
        headers=headers
    )
    assert update_response.status_code == 200
    updated_photo = update_response.json()

    # Verify photo is updated with new subject_id
    assert updated_photo["subject_id"] != photo["subject_id"]

    # Optionally check the new subject exists in DB for current_user
    subject_in_db = db_session.query(Subject).filter_by(name=new_subject_name).first()
    assert subject_in_db is not None
    assert subject_in_db.id == updated_photo["subject_id"]

def test_apply_filter_to_photo(client, db_session):
    # Register and login
    client.post("/register", json={"username": "testuser", "password": "testpass"})
    login = client.post("/login", json={"username": "testuser", "password": "testpass"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload a photo first
    test_image = create_test_image()
    upload_response = client.post(
        "/photos/",
        files={"file": ("test.jpg", test_image, "image/jpeg")},
        data={"gallery_password": "testpass", "subject_name": "my_subject"},
        headers=headers
    )
    assert upload_response.status_code == 200
    photo = upload_response.json()
    photo_id = photo["id"]

    # Define filters to test including restore 'none'
    filters = ["none", "sepia", "black and white", "color inversion"]

    for filter_name in filters:
        response = client.patch(
            f"/photos/{photo_id}/filter",
            data={"filter_name": filter_name, "gallery_password": "testpass"},
            headers=headers
        )
        assert response.status_code == 200
        updated_photo = response.json()
        assert updated_photo["filter_applied"] == (None if filter_name == "none" else filter_name)
