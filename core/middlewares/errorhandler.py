from loguru import logger
from starlette.types import ASGIApp, Receive, Scope, Send

from core.exceptions import ConnectionErrorException


class WebsocketErrorHandlerMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in (
            "websocket",
        ):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
        except ConnectionErrorException as err:
            logger.warning('Raised connection error', err)

