def test_register(client):
    response = client.post("/register", json={
        "username": "testuser",
        "password": "testpass"
    })
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"

def test_register_negative(client):
    response = client.post("/register", json={
        "username": "testuser",
        "password": "testpass"
    })
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"

    response = client.post("/register", json={
        "username": "testuser",
        "password": "testpass"
    })

    assert response.status_code == 400


def test_login(client):

    register_response = client.post("/register", json={"username": "testuser", "password": "testpass"})
    assert register_response.status_code == 201


    response = client.post("/login",
                           json={"username": "testuser", "password": "testpass"}
                           )


    print(f"Login response status: {response.status_code}")
    print(f"Login response content: {response.text}")

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_negative(client):
    register_response = client.post("/register", json={"username": "testuser", "password": "testpass"})
    assert register_response.status_code == 201

    response = client.post("/login",
                           json={"username": "fail", "password": "fail"}
                           )

    assert response.status_code == 401