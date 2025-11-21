from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.db.database import get_db
from src.main import app  # Assuming your FastAPI app instance is in src.main

client = TestClient(app)

@pytest.fixture
def mock_db_session():
    """Pytest fixture for a mock SQLAlchemy session."""
    db_session = MagicMock()
    yield db_session

def test_login_for_access_token_success(mock_db_session):
    """
    Test successful login and token generation.
    """
    with patch("src.api.v1.endpoints.login.crud.get_user_by_username") as mock_get_user, \
         patch("src.api.v1.endpoints.login.verify_password", return_value=True) as mock_verify_password, \
         patch("src.api.v1.endpoints.login.create_access_token", return_value="fake-token") as mock_create_token:

        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.id = 1
        mock_user.hashed_password = "fakehashedpassword"
        mock_get_user.return_value = mock_user

        app.dependency_overrides[get_db] = lambda: mock_db_session

        response = client.post("/api/v1/login/token", data={"username": "testuser", "password": "testpassword"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"access_token": "fake-token", "token_type": "bearer"}
        mock_get_user.assert_called_once_with(mock_db_session, username="testuser")
        mock_verify_password.assert_called_once_with("testpassword", "fakehashedpassword")
        mock_create_token.assert_called_once()
        app.dependency_overrides = {}


def test_login_for_access_token_invalid_username(mock_db_session):
    """
    Test login with an invalid username.
    """
    with patch("src.api.v1.endpoints.login.crud.get_user_by_username", return_value=None) as mock_get_user:

        app.dependency_overrides[get_db] = lambda: mock_db_session

        response = client.post("/api/v1/login/token", data={"username": "wronguser", "password": "testpassword"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {"detail": "Incorrect username or password"}
        mock_get_user.assert_called_once_with(mock_db_session, username="wronguser")
        app.dependency_overrides = {}


def test_login_for_access_token_invalid_password(mock_db_session):
    """
    Test login with a valid username but an invalid password.
    """
    with patch("src.api.v1.endpoints.login.crud.get_user_by_username") as mock_get_user, \
         patch("src.api.v1.endpoints.login.verify_password", return_value=False) as mock_verify_password:

        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.id = 1
        mock_user.hashed_password = "fakehashedpassword"
        mock_get_user.return_value = mock_user

        app.dependency_overrides[get_db] = lambda: mock_db_session

        response = client.post("/api/v1/login/token", data={"username": "testuser", "password": "wrongpassword"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {"detail": "Incorrect username or password"}
        mock_get_user.assert_called_once_with(mock_db_session, username="testuser")
        mock_verify_password.assert_called_once_with("wrongpassword", "fakehashedpassword")
        app.dependency_overrides = {}
