from typing import Callable, Type

from fastapi import Depends, Request, WebSocket

from db.repositories.base import BaseRepository, BaseDatabase
from db.repositories.models import UserRepository


def get_database(request: Request) -> BaseDatabase:
    return request.app.state._db


def get_ws_headers(ws: WebSocket):
    channel_id = ws.path_params
    return channel_id["channel"]


def get_headers(r: Request):
    return r.headers.get('x-session-id'), r.headers.get("x-accept-language", 'en'), r.headers.get("x-forwarded-for"), \
           r.headers.get('x-path', '')


def get_ws_database(websocket: WebSocket) -> BaseDatabase:
    return websocket.app.state._db


def get_repository(repo_type: Type[UserRepository]) -> Callable:
    def get_repo(db: BaseDatabase = Depends(get_database),
                 headers: tuple = Depends(get_headers)) -> UserRepository:
        return repo_type(db, session_id=headers[0], lang=headers[1], x_forwarded_for=headers[2],
                         query_params=headers[3])

    return get_repo


def get_ws_repository(repo_type: Type[UserRepository]) -> Callable:
    def get_repo(db: BaseDatabase = Depends(get_ws_database),
                 headers: str = Depends(get_ws_headers)) -> UserRepository:
        return repo_type(db, session_id=headers)

    return get_repo


def get_agent_repository(repo_type: Type[BaseRepository]) -> Callable:
    def get_repo(db: BaseDatabase = Depends(get_database)) -> BaseRepository:
        return repo_type(db)

    return get_repo
