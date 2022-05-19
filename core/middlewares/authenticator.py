from starlette.datastructures import Headers
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class AuthenticateMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in (
            "http"
        ):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        x_session_id = headers.get("x-session-id")
        if x_session_id:
            await self.app(scope, receive, send)
        else:
            response = PlainTextResponse("No session provided.", status_code=400)
            await response(scope, receive, send)
