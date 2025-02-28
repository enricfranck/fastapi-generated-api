import random
import string
from typing import List, Dict

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse

from app import crud, schemas
from app.api import deps
from app.api.deps import get_db
import logging

from app.db.session import SessionLocal

router = APIRouter()

# Define the database model
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            const months = [43, 46, 49];
            const random = Math.floor(Math.random() * months.length);
            var client_id = months[random];
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8081/api/v1/utils/notification/${client_id}?resource="client"`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@router.get("/")
async def get():
    return HTMLResponse(html)


@router.put("/read_notification")
async def read_notification(
        db: Session = Depends(get_db),
        *,
        notification_id: int,
        notification_in: schemas.NotificationUpdate,
):
    notification = crud.notification.get(db=db, id=notification_id)
    if notification:
        notification = crud.notification.update(
            db=db, obj_in=notification_in, db_obj=notification
        )

    return notification


@router.get("/all")
async def read_notification(
        db: Session = Depends(get_db), *, client_id: int, skip: int = 0, limit: int = 20
):
    user_notification = crud.user_notification.get_user(
        db=db, id_user=client_id, skip=skip, limit=limit
    )
    return user_notification


@router.get("/new")
async def read_notification(
        db: Session = Depends(get_db), *, client_id: int, skip: int = 0, limit: int = 4
):
    user_notification = crud.user_notification.get_new(
        db=db, id_user=client_id, skip=skip, limit=limit
    )
    return user_notification


@router.get("/count")
async def count_notification(
        db: Session = Depends(get_db),
        *,
        client_id: int,
):
    user_notification = crud.user_notification.get_count_notif(db=db, id_user=client_id)
    return user_notification


@router.delete("/delete_notification")
async def delete_notification(
        db: Session = Depends(get_db), *, notification_id: int, resource_id: int
):
    notification = crud.user_notification.get_by_id_notification(
        db=db, notification_id=notification_id, resource_id=resource_id
    )
    if notification:
        crud.user_notification.remove(db=db, id=notification.id)
    return notification


@router.get("/")
async def get():
    return HTMLResponse(html)


# WebSocket connection manager
logging.basicConfig(level=logging.INFO)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, schemas.SocketModel] = {}
        self.update_websockets: List[WebSocket] = []

    async def connect(self, websocket: schemas.SocketModel):
        if websocket.id in self.active_connections:
            existing_connection = self.active_connections[websocket.id]
            await self.disconnect(existing_connection)

        await websocket.wb.accept()
        self.active_connections[websocket.id] = websocket
        await self.notify_update()
        logging.info(f"Client {websocket.id} connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: schemas.SocketModel):
        if websocket.id in self.active_connections:
            del self.active_connections[websocket.id]
            if await self.is_websocket_open(websocket.wb):
                await websocket.wb.close()
            await self.notify_update()
            logging.info(f"Client {websocket.id} disconnected. Remaining connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: schemas.SocketModel):
        if await self.is_websocket_open(websocket.wb):
            await websocket.wb.send_json(message)

    async def broadcast(self, message: dict):
        for client_id, connection in self.active_connections.items():
            if await self.is_websocket_open(connection.wb):
                await connection.wb.send_json(message)
                logging.info(f"Broadcast message sent to client {client_id}")

    async def broadcast_filter(self, message: dict, client_id: str):
        connection = self.active_connections.get(client_id)
        if connection and await self.is_websocket_open(connection.wb):
            await connection.wb.send_json(message)
            logging.info(f"Filtered broadcast message sent to client {client_id}")

    async def broadcast_filter_multy(self, message: dict, client_ids: List[str]):
        for client_id in client_ids:
            await self.broadcast_filter(message, client_id)

    def get_active_connections(self) -> List[str]:
        return list(self.active_connections.keys())

    async def notify_update(self):
        connections = self.get_active_connections()
        for websocket in self.update_websockets:
            if await self.is_websocket_open(websocket):
                await websocket.send_json(jsonable_encoder(connections))

    async def add_update_websocket(self, websocket: WebSocket):
        await websocket.accept()
        self.update_websockets.append(websocket)
        await self.notify_update()  # Send initial update

    async def remove_update_websocket(self, websocket: WebSocket):
        if websocket in self.update_websockets:
            self.update_websockets.remove(websocket)
            if await self.is_websocket_open(websocket):
                await websocket.close()
                logging.info(
                    f"Client {websocket} disconnected. Remaining connections: {len(self.active_connections)}")
            await self.notify_update()  # Notify after removal

    async def is_websocket_open(self, websocket: WebSocket) -> bool:
        try:
            await websocket.send_text("")
        except WebSocketDisconnect:
            return False
        except RuntimeError:  # Catching additional runtime errors
            return False
        return True


manager = ConnectionManager()


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


@router.websocket("/message/{client_id}")
async def websocket_endpoint(
        websocket: WebSocket,
        client_id: str,
        resource: str = id_generator(),
        db: Session = Depends(deps.get_db),
):
    client = schemas.SocketModel(**{"id": client_id, "wb": websocket})
    await manager.connect(client)
    try:
        # Send all existing messages when a client connects
        user_messages = crud.user_message.get_resource_id(
            db=db, resource=resource, resource_id=client_id
        )
        for message_ in user_messages:
            message = crud.message.get(db=db, id=message_.id_message)
            await manager.send_personal_message(jsonable_encoder(message), client)

        while True:
            data = await websocket.receive_json()
            message = crud.message.create(
                db=db, obj_in=schemas.MessageCreate(**{"content": f"{data['message']}"})
            )
            if message:
                crud.user_message.create(
                    db=db,
                    obj_in=schemas.UserMessageCreate(
                        **{
                            "id_message": message.id,
                            "resource": resource,
                            "resource_id": client_id,
                            "type": "sender",
                        }
                    ),
                )

                crud.user_message.create(
                    db=db,
                    obj_in=schemas.UserMessageCreate(
                        **{
                            "id_message": message.id,
                            "resource": resource,
                            "resource_id": data["id_receiver"],
                            "type": "receiver",
                        }
                    ),
                )
            await manager.send_personal_message(data["message"], client)
            # Broadcast the new message to all connected clients
            # await manager.broadcast(f"Client #{client_id} says: {data}")
            await manager.broadcast_filter(
                jsonable_encoder(message), data["id_receiver"]
            )

    except WebSocketDisconnect:
        await manager.disconnect(client)
        # await manager.broadcast(f"Client #{client_id} left the chat")


@router.get("/connections", response_model=List[str])
async def get_connections():
    return manager.get_active_connections()


@router.websocket("/updates")
async def updates(websocket: WebSocket):
    await manager.add_update_websocket(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect as e:
        await manager.remove_update_websocket(websocket)
        logging.info(f"WebSocket disconnected: code={e.code}, reason={e.reason}")


@router.websocket("/notification/{client_id}")
async def websocket_endpoint(
        websocket: WebSocket,
        client_id: str,
        resource: str = id_generator(),
        db: Session = Depends(deps.get_db),
):
    client = schemas.SocketModel(**{"id": client_id, "wb": websocket})
    await manager.connect(client)
    try:
        # Send all existing messages when a client connects

        while True:
            data = await websocket.receive_json()
            if "status" in dict(data):
                for id_user in dict(data)["id_receiver"]:
                    await manager.broadcast_filter(dict(data), str(id_user))
            else:
                notification = crud.notification.create(
                    db=db,
                    obj_in=schemas.NotificationCreate(
                        **{"content": f"{data['content']}"}),
                )
                if notification:
                    for id_user in data["id_receiver"]:
                        user_notification_ = crud.user_notification.create(
                            db=db,
                            obj_in=schemas.UserNotificationCreate(
                                **{
                                    "id_notification": notification.id,
                                    "id_user": id_user,
                                    "id_message_from": data["id_sender"],
                                }
                            ),
                        )
                        if user_notification_:
                            user_notification_ = crud.user_notification.get_by_id(
                                db=db, id=user_notification_.id
                            )
                            await manager.broadcast_filter(
                                jsonable_encoder(user_notification_), id_user
                            )
            # else:
            #     for id_user in data["id_receiver"]:
            #         await manager.broadcast_filter(dict({"status": "refresh"}), id_user)

    except WebSocketDisconnect as e:
        await manager.disconnect(client)
        # await manager.broadcast(f"Client #{client_id} left the chat")
