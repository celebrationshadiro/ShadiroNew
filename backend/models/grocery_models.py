"""Grocery domain models: catalog items, order items, grocery orders."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from .shared_models import BookingContext, GroceryDeliveryAddress


class GroceryOrderStatus(str, Enum):
    PLACED = "placed"
    PACKED = "packed"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class GroceryCatalogItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    name: str
    category: Optional[str] = None
    unit: str = "kg"
    unit_price: float
    stock_qty: int = 0
    is_available: bool = True
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class GroceryOrderItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    item_id: str
    name: str
    qty: int = 1
    unit_price: float = 0.0
    unit: str = "item"
    total_price: float = 0.0


class GroceryOrderBase(BaseModel):
    user_id: str
    vendor_id: str
    items: List[GroceryOrderItem]
    delivery_address: GroceryDeliveryAddress
    delivery_eta: str
    total_amount: float
    commission_percentage: Optional[float] = None
    minimum_commission: Optional[float] = None
    commission_amount: Optional[float] = None
    vendor_payout_amount: Optional[float] = None
    gateway_fee: Optional[float] = None
    booking_context: Optional[BookingContext] = BookingContext.GROCERY
    serviceability_warning: Optional[str] = None
    delivery_zone: Optional[str] = None
    ai_context_address: Optional[Dict[str, Any]] = None


class GroceryOrderCreate(GroceryOrderBase):
    pass


class GroceryOrder(GroceryOrderBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: GroceryOrderStatus = GroceryOrderStatus.PLACED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
