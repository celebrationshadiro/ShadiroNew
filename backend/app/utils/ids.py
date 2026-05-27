from __future__ import annotations

from bson import ObjectId
from fastapi import HTTPException, status


def oid(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid ObjectId: {value}")
    return ObjectId(value)

