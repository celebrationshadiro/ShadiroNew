from __future__ import annotations

from typing import AsyncIterator

from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


class MongoManager:
    def __init__(self, uri: str, db_name: str) -> None:
        self.client = AsyncIOMotorClient(
            uri,
            maxPoolSize=500,
            minPoolSize=20,
            retryWrites=True,
            retryReads=True,
            w="majority",
        )
        self.db: AsyncIOMotorDatabase = self.client[db_name]

    async def ping(self) -> None:
        await self.db.command("ping")

    def close(self) -> None:
        self.client.close()

    async def session(self) -> AsyncIterator:
        async with await self.client.start_session() as session:
            yield session


def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.db

