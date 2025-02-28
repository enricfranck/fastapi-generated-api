from fastapi import APIRouter

from app.api.api_v1.endpoints import utils
from app.api.api_v1.endpoints import socket
from app.api.api_v1.endpoints import login

api_router = APIRouter()
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(socket.router, prefix="/socket", tags=["socket"])
api_router.include_router(login.router, prefix="/login", tags=["login"])
