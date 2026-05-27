from __future__ import annotations

from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorDatabase


class ChatRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def insert_message(self, message: Dict[str, Any]) -> None:
        await self.db.chat_messages.insert_one(message)

    async def update_chat_last_message(self, chat_id: str, message_text: str, timestamp: str) -> None:
        await self.db.chats.update_one(
            {"id": chat_id},
            {"$set": {"last_message": message_text, "last_message_at": timestamp}},
        )
