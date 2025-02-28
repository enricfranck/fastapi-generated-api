from typing import List

from fastapi import WebSocket

from app import schemas


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[schemas.SocketModel] = []

    async def connect(self, websocket: schemas.SocketModel, list_message: List[str]):
        await websocket.wb.accept()
        for message in list_message:
            await websocket.wb.send_json(message)
        self.active_connections.append(websocket)

    def disconnect(self, websocket: schemas.SocketModel):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast_all(self, message: str):
        for connection in self.active_connections:
            await connection.wb.send_json(message)

    async def broadcast_id(self, message: str, email_receive: str):
        for connection in self.active_connections:
            if connection.id == email_receive:
                await connection.wb.send_json(message)
