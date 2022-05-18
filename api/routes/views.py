import asyncio
import json
from typing import List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Header, Depends, HTTPException, Body
from loguru import logger
from starlette.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from api.dependencies.database import get_repository, get_ws_repository
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
    pubsub = websocket.app.state._db.redis.pubsub()
    try:
        ws_status = asyncio.ensure_future(
             receiving(websocket)
        )

        chat_info = await users_repo.get_chat_info()
        if not chat_info:
            await websocket.close()
            raise WebSocketDisconnect()

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
                    msg_data = json.loads(msg.get('data'))
                    if msg_data.get('channel_id') == channel:
                        await websocket.send_json(msg)

            await pubsub.unsubscribe(channel)

    except WebSocketDisconnect:
        logger.warning("WS CLOSED!")
        await pubsub.close()
    except ConnectionClosedError:
        await websocket.close()
    except ConnectionClosedOK:
        await websocket.close()
    except RuntimeError as err:
        logger.error(err)
        await pubsub.close()
    finally:
        await pubsub.close()


@router.post("/user/publish", name='user-publish', status_code=201)
async def chat_publish(
        request: Request,
        users_repo: UserRepository = Depends(get_repository(UserRepository)),
        x_session_id: Optional[str] = Header(None)):

    if not x_session_id:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No session found with that query.")

    body_ = await request.json()
    if body_:
        await users_repo.set_chat_message(message=body_['message'])
    else:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="No message passed.")

    return {"success": 1}


@router.post("/wp/user/publish", name='user-wp-publish', status_code=201)
async def chat_wp_publish(
        request: Request,
        users_repo: UserRepository = Depends(get_repository(UserRepository)),
        x_session_id: Optional[str] = Header(None)):

    if not x_session_id:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No session found with that query.")

    body_ = await request.json()
    if body_:
        await users_repo.set_wp_chat_message(message=body_['message'], name=body_['name'], phone=body_['phone'])
    else:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="No message passed.")

    return {"success": 1}


@router.post("/update", name='form-update', status_code=201)
async def chat_update(
        user_form: UserForm = Body(...),
        users_repo: UserRepository = Depends(get_repository(UserRepository)),
        x_session_id: Optional[str] = Header(None)):

    if not x_session_id:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No session found with that query.")

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
        users_repo: UserRepository = Depends(get_repository(UserRepository)),
        x_session_id: Optional[str] = Header(None)):
    if not x_session_id:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No session found with that query.")

    return await users_repo.get_last_chat_history()
