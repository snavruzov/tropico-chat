from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import WebSocketException


class ConnectionErrorException(WebSocketDisconnect, WebSocketException):
    pass
