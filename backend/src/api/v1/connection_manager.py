
from fastapi import WebSocket, status


class ConnectionManager:
    def __init__(self, max_total_connections: int = 1000, max_connections_per_user: int = 5):
        self.active_connections: dict[str, WebSocket] = {}
        self.user_connection_counts: dict[str, int] = {}
        self.max_total_connections = max_total_connections
        self.max_connections_per_user = max_connections_per_user

    async def connect(self, websocket: WebSocket, user_id: str):
        if len(self.active_connections) >= self.max_total_connections:
            await websocket.close(code=status.WS_1013_TRY_AGAIN_LATER, reason="Server is at maximum capacity.")
            return False

        if self.user_connection_counts.get(user_id, 0) >= self.max_connections_per_user:
            await websocket.close(code=status.WS_1013_TRY_AGAIN_LATER, reason="Too many connections for this user.")
            return False

        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_connection_counts[user_id] = self.user_connection_counts.get(user_id, 0) + 1
        return True

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            self.user_connection_counts[user_id] = self.user_connection_counts.get(user_id, 1) - 1
            if self.user_connection_counts[user_id] <= 0:
                del self.user_connection_counts[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()
