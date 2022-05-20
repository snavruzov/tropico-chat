import asyncio
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException, Body
from loguru import logger
from starlette.status import HTTP_400_BAD_REQUEST

from api.dependencies.database import get_repository, get_ws_repository
from core.exceptions import ConnectionErrorException
from db.models import UserChat, UserForm
from db.repositories.models import UserRepository

router = APIRouter()


class SocketManager:
    def __init__(self):
        self.active_connections: List[(WebSocket, str)] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()


manager = SocketManager()


async def receiving(websocket):
    try:
        while True:
            await websocket.receive_json()
    except WebSocketDisconnect:
        logger.debug("WS Disconnected!")


@router.websocket("/subscribe/{channel}", name='chat-ws')
async def chat(
        channel: str,
        websocket: WebSocket,
        users_repo: UserRepository = Depends(get_ws_repository(UserRepository))):

    await manager.connect(websocket)
    pubsub = websocket.app.state.db.redis.pubsub()
    ws_status = asyncio.ensure_future(
         receiving(websocket)
    )

    chat_info = await users_repo.check_chat_info()
    if not chat_info:
        await websocket.close()
        raise ConnectionErrorException()

    async with pubsub as p:
        await p.subscribe(channel)
        asyncio.ensure_future(
            users_repo.initial_pass_chat_info(ch_info=chat_info)
        )
        while True:
            if ws_status.done() or ws_status.cancelled():
                break
            msg = await pubsub.get_message(ignore_subscribe_messages=True)
            if msg and msg.get('data'):
                await websocket.send_json(msg)


@router.post("/user/publish", name='user-publish', status_code=201)
async def chat_publish(
        request: Request,
        users_repo: UserRepository = Depends(get_repository(UserRepository))):

    body_ = await request.json()
    if body_ and body_.get('message'):
        await users_repo.set_chat_message(message=body_['message'])
    else:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="No message passed.")

    return {"success": 1}


@router.post("/update", name='form-update', status_code=201)
async def chat_update(
        user_form: UserForm = Body(...),
        users_repo: UserRepository = Depends(get_repository(UserRepository))):

    if not user_form.phone and not user_form.email:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="At least one contact information required")

    if user_form:
        await users_repo.set_chat_info(email=user_form.email,
                                       phone=user_form.phone,
                                       name=user_form.name)

    return {"success": 1}


@router.get("/history",
            response_model=List[UserChat],
            name='chat-history',
            response_model_exclude={"id", "chat_id"},
            status_code=200)
async def chat_history(
        users_repo: UserRepository = Depends(get_repository(UserRepository))):
    return await users_repo.get_last_chat_history()
