def test_get_user_subjects(client):
    # Register a new user
    register_response = client.post("/register", json={"username": "testuser", "password": "testpass"})
    assert register_response.status_code == 201

    # Login to get token
    login_response = client.post("/login", json={"username": "testuser", "password": "testpass"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Prepare authorization header
    headers = {"Authorization": f"Bearer {token}"}

    # Get subjects for the user (should be empty initially)
    response = client.get("/subjects/", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 0  # Assuming no subjects yet

    # Optional: Create a subject to test retrieval
    from fastapi.testclient import TestClient

    subject_name = "testsubject"
    create_response = client.post("/subject/", data={"name": subject_name}, headers=headers)
    assert create_response.status_code == 201
    created_subject = create_response.json()
    assert created_subject["name"] == subject_name

    # Retrieve subjects again, should contain the newly created subject
    response = client.get("/subjects/", headers=headers)
    assert response.status_code == 200
    subjects = response.json()
    assert any(subject["name"] == subject_name for subject in subjects)

def test_duplicate_subjects(client):
    # Register a new user
    register_response = client.post("/register", json={"username": "testuser", "password": "testpass"})
    assert register_response.status_code == 201

    # Login to get token
    login_response = client.post("/login", json={"username": "testuser", "password": "testpass"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Prepare authorization header
    headers = {"Authorization": f"Bearer {token}"}

    # Get subjects for the user (should be empty initially)
    response = client.get("/subjects/", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 0  # Assuming no subjects yet

    # Optional: Create a subject to test retrieval
    from fastapi.testclient import TestClient

    subject_name = "testsubject"
    create_response = client.post("/subject/", data={"name": subject_name}, headers=headers)
    assert create_response.status_code == 201
    created_subject = create_response.json()
    assert created_subject["name"] == subject_name

    subject_name = "testsubject"
    create_response = client.post("/subject/", data={"name": subject_name}, headers=headers)
    assert create_response.status_code == 409
