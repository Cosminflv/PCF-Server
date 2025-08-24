import pytest
from fastapi import HTTPException
from datetime import timedelta

from services.auth_service import AuthService
import crud  # Make sure this is your actual crud module

@pytest.fixture
def auth_service(db_session):
    return AuthService(db_session)

def test_register_user_success(auth_service, db_session):
    # Register a new user
    username = "newuser"
    password = "pass123"
    user = auth_service.register_user(username, password)

    # Verify user is persisted
    db_user = crud.get_user_by_username(db_session, username)
    assert db_user is not None
    assert db_user.username == username
    assert user.username == username

def test_register_user_username_already_exists(auth_service, db_session):
    username = "existinguser"
    password = "pass123"
    # Create first user via crud helper to simulate existing user
    crud.create_user(db_session, username, password)

    # Attempt to register again should raise HTTPException
    with pytest.raises(HTTPException) as exc:
        auth_service.register_user(username, password)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Username already registered"

def test_login_user_success(auth_service, db_session):
    username = "testuser"
    password = "pass123"
    # Create user (must be hashed as crud.create_user does)
    crud.create_user(db_session, username, password)

    result = auth_service.login_user(username, password)
    assert "access_token" in result
    assert result["token_type"] == "bearer"

def test_login_user_invalid_username(auth_service):
    with pytest.raises(HTTPException) as exc:
        auth_service.login_user("wronguser", "pass123")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid username or password"

def test_login_user_invalid_password(auth_service, db_session):
    username = "user1"
    password = "correctpass"
    crud.create_user(db_session, username, password)

    with pytest.raises(HTTPException) as exc:
        auth_service.login_user(username, "wrongpass")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid username or password"
