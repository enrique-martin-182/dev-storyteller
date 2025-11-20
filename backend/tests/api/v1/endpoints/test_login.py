import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.core.security import get_password_hash
from src.db import crud, models


@patch("src.core.security.pwd_context")
def test_login_for_access_token(mock_pwd_context, client: TestClient, db_session):
    # Configure the mock pwd_context
    mock_pwd_context.hash.side_effect = lambda password: f"hashed_{password}"
    mock_pwd_context.verify.side_effect = lambda plain, hashed: hashed == f"hashed_{plain}"

    # Create a test user in the database
    username = "testuser"
    password = "short"
    hashed_password = get_password_hash(password)
    user = models.User(username=username, hashed_password=hashed_password)
    db_session.add(user)
    db_session.commit()

    response = client.post("/api/v1/token", data={"username": username, "password": password})
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"