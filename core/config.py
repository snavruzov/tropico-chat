from databases import DatabaseURL
from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")

PROJECT_NAME = "tropico_chat"
VERSION = "1.0.0"

POSTGRES_USER = config("DB_USER", cast=str)
POSTGRES_PASSWORD = config("DB_PASSWD", cast=Secret)
POSTGRES_SERVER = config("DB_HOST", cast=str, default="db")
POSTGRES_PORT = config("DB_PORT", cast=str, default="5432")
POSTGRES_DB = config("DB_NAME", cast=str)

RABBIT_HOST = config("RABBIT_HOST", cast=str)
RABBIT_PORT = config("RABBIT_PORT", cast=str)
RABBIT_USERNAME = config("RABBIT_USERNAME", cast=str)
RABBIT_PASSWORD = config("RABBIT_PASSWORD", cast=str)

DATABASE_URL_TEST = config(
        "DATABASE_URL",
        cast=DatabaseURL,
        default="sqlite:///./sql_app.db"
)

DATABASE_URL = config(
    "DATABASE_URL",
    cast=DatabaseURL,
    default=f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

MEDIA_URL = 'https://d7i54qaggkyj3.cloudfront.net/'

AVAILABLE_CHANNELS = dict()
BITRIX_URL = "https://crm.axcap.ae/"
WS_SESSION_ID_PREFIX = 'WS_EX_'
TG_API_TOKEN = ''
TG_CHANNEL_ID = ""

