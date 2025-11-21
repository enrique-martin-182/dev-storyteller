
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import WebSocket, status

from src.api.v1.connection_manager import ConnectionManager


@pytest.fixture
def connection_manager():
    return ConnectionManager()

@pytest.fixture
def mock_websocket():
    ws = MagicMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.close = AsyncMock()
    ws.send_text = AsyncMock()
    return ws

@pytest.mark.asyncio
async def test_connect_success(connection_manager, mock_websocket):
    user_id = "test_user"
    result = await connection_manager.connect(mock_websocket, user_id)
    assert result is True
    assert user_id in connection_manager.active_connections
    assert connection_manager.active_connections[user_id] == mock_websocket
    assert connection_manager.user_connection_counts[user_id] == 1
    mock_websocket.accept.assert_awaited_once()

@pytest.mark.asyncio
async def test_connect_max_total_connections(connection_manager, mock_websocket):
    connection_manager.max_total_connections = 0 # Set max to 0 to easily exceed
    user_id = "test_user"
    result = await connection_manager.connect(mock_websocket, user_id)
    assert result is False
    assert user_id not in connection_manager.active_connections
    mock_websocket.close.assert_awaited_once_with(code=status.WS_1013_TRY_AGAIN_LATER, reason="Server is at maximum capacity.")

@pytest.mark.asyncio
async def test_connect_max_connections_per_user(connection_manager, mock_websocket):
    connection_manager.max_connections_per_user = 0 # Set max to 0 to easily exceed
    user_id = "test_user"
    result = await connection_manager.connect(mock_websocket, user_id)
    assert result is False
    assert user_id not in connection_manager.active_connections
    mock_websocket.close.assert_awaited_once_with(code=status.WS_1013_TRY_AGAIN_LATER, reason="Too many connections for this user.")

def test_disconnect_user_exists_multiple_connections(connection_manager, mock_websocket):
    user_id = "test_user"
    connection_manager.active_connections[user_id] = mock_websocket
    connection_manager.user_connection_counts[user_id] = 2
    connection_manager.disconnect(user_id)
    assert user_id not in connection_manager.active_connections
    assert connection_manager.user_connection_counts[user_id] == 1

def test_disconnect_user_exists_last_connection(connection_manager, mock_websocket):
    user_id = "test_user"
    connection_manager.active_connections[user_id] = mock_websocket
    connection_manager.user_connection_counts[user_id] = 1
    connection_manager.disconnect(user_id)
    assert user_id not in connection_manager.active_connections
    assert user_id not in connection_manager.user_connection_counts

def test_disconnect_user_not_exists(connection_manager):
    user_id = "non_existent_user"
    connection_manager.disconnect(user_id)
    # No error should be raised, and state should remain unchanged
    assert user_id not in connection_manager.active_connections
    assert user_id not in connection_manager.user_connection_counts

@pytest.mark.asyncio
async def test_send_personal_message_success(connection_manager, mock_websocket):
    user_id = "test_user"
    message = "Hello"
    connection_manager.active_connections[user_id] = mock_websocket
    await connection_manager.send_personal_message(message, user_id)
    mock_websocket.send_text.assert_awaited_once_with(message)

@pytest.mark.asyncio
async def test_send_personal_message_user_not_found(connection_manager, mock_websocket):
    user_id = "non_existent_user"
    message = "Hello"
    await connection_manager.send_personal_message(message, user_id)
    mock_websocket.send_text.assert_not_awaited()

@pytest.mark.asyncio
async def test_broadcast_with_active_connections(connection_manager):
    user_id1 = "user1"
    user_id2 = "user2"
    mock_websocket1 = MagicMock(spec=WebSocket)
    mock_websocket1.send_text = AsyncMock()
    mock_websocket2 = MagicMock(spec=WebSocket)
    mock_websocket2.send_text = AsyncMock()

    connection_manager.active_connections[user_id1] = mock_websocket1
    connection_manager.active_connections[user_id2] = mock_websocket2

    message = "Broadcast message"
    await connection_manager.broadcast(message)

    mock_websocket1.send_text.assert_awaited_once_with(message)
    mock_websocket2.send_text.assert_awaited_once_with(message)

@pytest.mark.asyncio
async def test_broadcast_no_active_connections(connection_manager):
    message = "Broadcast message"
    await connection_manager.broadcast(message)
    # No errors should be raised, and no send_text calls should occur
    pass # No assertions needed other than no exceptions
