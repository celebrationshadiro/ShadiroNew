from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


class MongoManager:
    def __init__(self, mongo_url: str, db_name: str):
        self.client = AsyncIOMotorClient(mongo_url)
        self.db: AsyncIOMotorDatabase = self.client[db_name]

    def close(self) -> None:
        self.client.close()


def init_mongo(app: FastAPI, manager: MongoManager) -> None:
    app.state.mongo = manager
    app.state.db = manager.db


def close_mongo(app: FastAPI) -> None:
    mongo = getattr(app.state, "mongo", None)
    if mongo:
        mongo.close()


def get_db_from_request(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.db

