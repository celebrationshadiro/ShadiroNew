from fastapi import Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from auth import get_current_user


def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.db


def get_razorpay_client(request: Request):
    return request.app.state.razorpay_client


def require_roles(*roles: str):
    async def _checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in set(roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user

    return _checker

