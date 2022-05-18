from aioredis import Redis
from databases import Database


class BaseDatabase:
    redis: Redis = None
    db: Database = None

    def __init__(self, redis: Redis, db: Database) -> None:
        self.redis = redis
        self.db = db


class BaseRepository:
    def __init__(self, bsd: BaseDatabase) -> None:
        self.redis = bsd.redis
        self.db = bsd.db

