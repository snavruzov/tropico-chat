import os

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from api.routes import router as api_router
from core import tasks
from core.middlewares.botblock import BotBlockMiddleware


def get_application():
    app = FastAPI()
    if not os.environ.get("TESTING"):
        sentry_sdk.init(dsn="")
        app.add_middleware(SentryAsgiMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(BotBlockMiddleware)

    app.add_event_handler("startup", tasks.create_start_app_handler(app))
    app.add_event_handler("shutdown", tasks.create_stop_app_handler(app))

    app.include_router(api_router, prefix="/ws")

    return app


app = get_application()

