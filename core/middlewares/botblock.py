from starlette.datastructures import Headers
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.websockets import WebSocket


class BotBlockMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in (
            "http",
            "websocket",
        ):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        user_agent = headers.get("user-agent", "")
        if 'bot' not in user_agent.lower() and 'Mozilla/5.0' in user_agent:
            await self.app(scope, receive, send)
        else:
            if scope["type"] == 'websocket':
                response = WebSocket(scope=scope, receive=receive, send=send)
                await response.close()
            else:
                response = PlainTextResponse("Invalid host header", status_code=400)
                await response(scope, receive, send)
