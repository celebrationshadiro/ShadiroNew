from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
import uuid

from .repository import ChatRepository


class ChatService:
    def __init__(self, repository: ChatRepository):
        self.repository = repository

    def build_message(
        self,
        chat_id: str,
        message_text: str,
        sender_id: str,
        sender_name: str = "User",
    ) -> Dict[str, Any]:
        return {
            "id": str(uuid.uuid4()),
            "chat_id": chat_id,
            "message": message_text,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "read": False,
        }

    async def persist_message(self, message: Dict[str, Any]) -> None:
        await self.repository.insert_message(message)
        await self.repository.update_chat_last_message(
            chat_id=message["chat_id"],
            message_text=message["message"],
            timestamp=message["timestamp"],
        )
