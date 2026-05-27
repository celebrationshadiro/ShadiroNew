from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set, Tuple
import logging

import socketio
from motor.motor_asyncio import AsyncIOMotorDatabase

from modules.chat import ChatRepository, ChatService

logger = logging.getLogger(__name__)


class ChatSocketGateway:
    def __init__(self, sio: socketio.AsyncServer, service: ChatService):
        self.sio = sio
        self.service = service
        self.active_users: Dict[str, str] = {}
        self.active_chats: Dict[str, Set[str]] = {}
        self._register_handlers()

    async def _broadcast_online_users(self, chat_id: str) -> None:
        online = list(self.active_chats.get(chat_id, set()))
        await self.sio.emit("online_users", {"user_ids": online}, room=chat_id)

    async def _handle_connect(self, sid: str) -> bool:
        logger.info(f"Client connected: {sid}")
        return True

    async def _handle_disconnect(self, sid: str) -> None:
        logger.info(f"Client disconnected: {sid}")
        user_id = self.active_users.pop(sid, None)
        if user_id:
            logger.info(f"User {user_id} disconnected")

    async def _handle_join_chat(self, sid: str, data: Dict[str, Any]) -> None:
        user_id = data.get("user_id")
        chat_id = data.get("chat_id")
        user_name = data.get("user_name", "User")

        if not user_id or not chat_id:
            await self.sio.emit("error", {"message": "Missing user_id or chat_id"}, room=sid)
            return

        self.active_users[sid] = user_id
        await self.sio.enter_room(sid, chat_id)
        self.active_chats.setdefault(chat_id, set()).add(user_id)

        await self.sio.emit(
            "user_joined",
            {
                "user_id": user_id,
                "user_name": user_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            room=chat_id,
            skip_sid=sid,
        )
        await self._broadcast_online_users(chat_id)
        logger.info(f"User {user_id} joined chat {chat_id}")

    async def _handle_send_message(self, sid: str, data: Dict[str, Any]) -> None:
        chat_id = data.get("chat_id")
        message_text = data.get("message")
        sender_id = data.get("sender_id")
        sender_name = data.get("sender_name", "User")

        if not all([chat_id, message_text, sender_id]):
            await self.sio.emit("error", {"message": "Missing required fields"}, room=sid)
            return

        message = self.service.build_message(
            chat_id=chat_id,
            message_text=message_text,
            sender_id=sender_id,
            sender_name=sender_name,
        )

        try:
            await self.service.persist_message(message)
        except Exception as exc:
            logger.error(f"Failed to save message to DB: {str(exc)}")

        await self.sio.emit("new_message", message, room=chat_id)
        logger.info(f"Message sent in chat {chat_id} by {sender_id}")

    async def _handle_leave_chat(self, sid: str, data: Dict[str, Any]) -> None:
        chat_id = data.get("chat_id")
        user_id = data.get("user_id")
        if not chat_id or not user_id:
            return

        await self.sio.leave_room(sid, chat_id)

        users = self.active_chats.get(chat_id)
        if users is not None:
            users.discard(user_id)
            if not users:
                del self.active_chats[chat_id]

        await self.sio.emit(
            "user_left",
            {"user_id": user_id, "timestamp": datetime.now(timezone.utc).isoformat()},
            room=chat_id,
        )
        if chat_id in self.active_chats:
            await self._broadcast_online_users(chat_id)
        logger.info(f"User {user_id} left chat {chat_id}")

    async def _handle_typing(self, sid: str, data: Dict[str, Any]) -> None:
        chat_id = data.get("chat_id")
        user_id = data.get("user_id")
        user_name = data.get("user_name")
        if not all([chat_id, user_id]):
            return

        await self.sio.emit(
            "user_typing",
            {"user_id": user_id, "user_name": user_name},
            room=chat_id,
            skip_sid=sid,
        )

    async def _handle_mark_read(self, data: Dict[str, Any]) -> None:
        chat_id = data.get("chat_id")
        reader_id = data.get("reader_id")
        if not chat_id or not reader_id:
            return

        await self.sio.emit("messages_read", {"reader_id": reader_id, "chat_id": chat_id}, room=chat_id)

    def get_chat_users(self, chat_id: str) -> list[str]:
        return list(self.active_chats.get(chat_id, set()))

    def _register_handlers(self) -> None:
        @self.sio.event
        async def connect(sid, environ):
            try:
                return await self._handle_connect(sid)
            except Exception as exc:
                logger.error(f"Error in connect: {str(exc)}")
                return False

        @self.sio.event
        async def disconnect(sid):
            try:
                await self._handle_disconnect(sid)
            except Exception as exc:
                logger.error(f"Error in disconnect: {str(exc)}")

        @self.sio.event
        async def join_chat(sid, data):
            try:
                await self._handle_join_chat(sid, data or {})
            except Exception as exc:
                logger.error(f"Error in join_chat: {str(exc)}")
                await self.sio.emit("error", {"message": str(exc)}, room=sid)

        @self.sio.event
        async def send_message(sid, data):
            try:
                await self._handle_send_message(sid, data or {})
            except Exception as exc:
                logger.error(f"Error in send_message: {str(exc)}")
                await self.sio.emit("error", {"message": str(exc)}, room=sid)

        @self.sio.event
        async def leave_chat(sid, data):
            try:
                await self._handle_leave_chat(sid, data or {})
            except Exception as exc:
                logger.error(f"Error in leave_chat: {str(exc)}")

        @self.sio.event
        async def typing(sid, data):
            try:
                await self._handle_typing(sid, data or {})
            except Exception as exc:
                logger.error(f"Error in typing: {str(exc)}")

        @self.sio.event
        async def mark_read(sid, data):
            try:
                _ = sid
                await self._handle_mark_read(data or {})
            except Exception as exc:
                logger.error(f"Error in mark_read: {str(exc)}")


def build_chat_socket_server(
    db: AsyncIOMotorDatabase,
    *,
    cors_allowed_origins: str = "*",
    enable_socket_logging: bool = True,
) -> Tuple[socketio.AsyncServer, ChatSocketGateway]:
    sio = socketio.AsyncServer(
        async_mode="asgi",
        cors_allowed_origins=cors_allowed_origins,
        logger=enable_socket_logging,
        engineio_logger=enable_socket_logging,
    )
    repository = ChatRepository(db)
    service = ChatService(repository)
    gateway = ChatSocketGateway(sio, service)
    return sio, gateway
