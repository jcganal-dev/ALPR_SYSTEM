from typing import List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Keeps track of active connections
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    # This is the function you will call manually!
    async def send_update(self, data: dict):
        for connection in self.active_connections:
            # print(new_data)
            await connection.send_json(data)

# Create a global instance
live_video_manager = ConnectionManager()
dashboard_manager = ConnectionManager()
notifications_manager = ConnectionManager()