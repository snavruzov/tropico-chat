import os

from aioredis import from_url
from databases import Database
from fastapi import FastAPI
from loguru import logger

from core.config import DATABASE_URL, DATABASE_URL_TEST
from db.repositories.base import BaseDatabase


async def init_redis_pool(app: FastAPI) -> None:
    try:
        redis = await from_url(
            f'redis://redis',
            encoding="utf-8",
            db="8",
            decode_responses=True,
        )
        app.state.redis = redis
    except Exception as e:
        logger.warning("--- REDIS CONNECTION ERROR ---")
        logger.warning(e)
        logger.warning("--- REDIS CONNECTION ERROR ---")


async def close_redis_pool(app: FastAPI) -> None:
    try:
        await app.state.redis.close()
    except Exception as e:
        logger.warning("--- REDIS CLOSE ERROR ---")
        logger.warning(e)
        logger.warning("--- REDIS CLOSE ERROR ---")


async def connect_to_db(app: FastAPI) -> None:
    try:
        redis = await from_url(
            f'redis://redis',
            encoding="utf-8",
            db="8",
            decode_responses=True,
        )

        if not os.environ.get("TESTING"):
            database = Database(DATABASE_URL, min_size=2, max_size=10)
            await database.connect()
        else:
            database = Database(DATABASE_URL_TEST, min_size=2, max_size=10)
            await database.connect()

        app.state.db = BaseDatabase(redis, database)

    except Exception as e:
        logger.warning("--- DB CONNECTION ERROR ---")
        logger.exception(e)
        logger.warning("--- DB CONNECTION ERROR ---")


async def close_db_connection(app: FastAPI) -> None:
    try:
        await app.state.db.db.disconnect()
    except Exception as e:
        logger.warning("--- DB DISCONNECT ERROR ---")
        logger.warning(e)
        logger.warning("--- DB DISCONNECT ERROR ---")

    try:
        await app.state.db.redis.close()
    except Exception as e:
        logger.warning("--- REDIS CLOSE ERROR ---")
        logger.warning(e)
        logger.warning("--- REDIS CLOSE ERROR ---")

