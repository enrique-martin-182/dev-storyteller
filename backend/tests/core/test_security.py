
import unittest
from unittest.mock import ANY, MagicMock, patch

import pytest
from fastapi import HTTPException, WebSocket, WebSocketException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.core.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    get_current_user,
    get_current_websocket_user,
)
from src.db import models  # Import crud and models


class TestSecurity(unittest.TestCase):

    def test_create_access_token(self):
        data = {"username": "testuser"} # Changed from "sub" to "username"
        token = create_access_token(data=data)
        self.assertIsInstance(token, str)

        # Decode to verify
        decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        self.assertEqual(decoded_payload["sub"], "testuser")
        self.assertIn("exp", decoded_payload)



    @pytest.mark.asyncio
    @patch("src.core.security.verify_token")
    @patch("src.core.security.crud")
    async def test_get_current_user_success(self, mock_crud, mock_verify_token):
        mock_verify_token.return_value = "testuser"
        mock_crud.get_user_by_username.return_value = models.User(id=1, username="testuser")

        db_session = MagicMock(spec=Session)

        token_data = await get_current_user("dummy_token", db_session)
        self.assertEqual(token_data.username, "testuser")
        self.assertEqual(token_data.id, 1)
        mock_verify_token.assert_called_once_with("dummy_token", ANY)
        mock_crud.get_user_by_username.assert_called_once_with(db_session, username="testuser")

    @pytest.mark.asyncio
    @patch("src.core.security.verify_token")
    @patch("src.core.security.crud")
    async def test_get_current_user_not_found(self, mock_crud, mock_verify_token):
        mock_verify_token.return_value = "testuser"
        mock_crud.get_user_by_username.return_value = None

        db_session = MagicMock(spec=Session)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("dummy_token", db_session)
        self.assertEqual(exc_info.value.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_verify_token.assert_called_once_with("dummy_token", ANY)
        mock_crud.get_user_by_username.assert_called_once_with(db_session, username="testuser")

    @pytest.mark.asyncio
    @patch("src.core.security.jwt.decode")
    @patch("src.core.security.crud")
    async def test_get_current_websocket_user_success(self, mock_crud, mock_jwt_decode):
        mock_jwt_decode.return_value = {"sub": "wsuser"}
        mock_crud.get_user_by_username.return_value = models.User(id=2, username="wsuser")

        db_session = MagicMock(spec=Session)
        websocket = MagicMock(spec=WebSocket)

        token_data = await get_current_websocket_user(websocket, token="ws_token", db=db_session)
        self.assertEqual(token_data.username, "wsuser")
        self.assertEqual(token_data.id, 2)
        mock_jwt_decode.assert_called_once_with("ws_token", SECRET_KEY, algorithms=[ALGORITHM])
        mock_crud.get_user_by_username.assert_called_once_with(db_session, username="wsuser")

    @pytest.mark.asyncio
    @patch("src.core.security.jwt.decode", side_effect=JWTError)
    async def test_get_current_websocket_user_invalid_token(self, mock_jwt_decode):
        db_session = MagicMock(spec=Session)
        websocket = MagicMock(spec=WebSocket)

        with pytest.raises(WebSocketException) as exc_info:
            await get_current_websocket_user(websocket, token="invalid_ws_token", db=db_session)
        self.assertEqual(exc_info.value.code, status.WS_1008_POLICY_VIOLATION)
        mock_jwt_decode.assert_called_once_with("invalid_ws_token", SECRET_KEY, algorithms=[ALGORITHM])

    @pytest.mark.asyncio
    @patch("src.core.security.jwt.decode", return_value={"sub": None})
    async def test_get_current_websocket_user_no_username_in_payload(self, mock_jwt_decode):
        db_session = MagicMock(spec=Session)
        websocket = MagicMock(spec=WebSocket)

        with pytest.raises(WebSocketException) as exc_info:
            await get_current_websocket_user(websocket, token="ws_token_no_user", db=db_session)
        self.assertEqual(exc_info.value.code, status.WS_1008_POLICY_VIOLATION)
        mock_jwt_decode.assert_called_once_with("ws_token_no_user", SECRET_KEY, algorithms=[ALGORITHM])

    @pytest.mark.asyncio
    @patch("src.core.security.jwt.decode", return_value={"sub": "wsuser"})
    @patch("src.core.security.crud")
    async def test_get_current_websocket_user_not_found(self, mock_crud, mock_jwt_decode):
        mock_crud.get_user_by_username.return_value = None

        db_session = MagicMock(spec=Session)
        websocket = MagicMock(spec=WebSocket)

        with pytest.raises(WebSocketException) as exc_info:
            await get_current_websocket_user(websocket, token="ws_token", db=db_session)
        self.assertEqual(exc_info.value.code, status.WS_1008_POLICY_VIOLATION)
        mock_jwt_decode.assert_called_once_with("ws_token", SECRET_KEY, algorithms=[ALGORITHM])
        mock_crud.get_user_by_username.assert_called_once_with(db_session, username="wsuser")

