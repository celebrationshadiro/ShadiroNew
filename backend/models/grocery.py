from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class GroceryCategory(str, Enum):
    VEGETABLES = "vegetables"
    FRUITS = "fruits"
    DAIRY = "dairy"
    GRAINS = "grains"
    SPICES = "spices"
    BEVERAGES = "beverages"
    SNACKS = "snacks"
    MEAT_FISH = "meat_fish"
    BAKERY = "bakery"
    OTHER = "other"


class GroceryUnit(str, Enum):
    KG = "kg"
    GRAM = "gram"
    LITRE = "litre"
    ML = "ml"
    PIECE = "piece"
    DOZEN = "dozen"
    PACKET = "packet"
    BUNDLE = "bundle"


class GroceryOrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUND_REQUESTED = "refund_requested"
    REFUNDED = "refunded"


class GroceryProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    category: GroceryCategory
    price_per_unit_paise: int = Field(gt=0)
    unit: GroceryUnit
    min_order_quantity: float = Field(default=1.0, gt=0)
    max_order_quantity: Optional[float] = Field(None, gt=0)
    in_stock: bool = True
    image_url: Optional[str] = None


class GroceryProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_per_unit_paise: Optional[int] = Field(None, gt=0)
    in_stock: Optional[bool] = None
    min_order_quantity: Optional[float] = Field(None, gt=0)
    image_url: Optional[str] = None


class GroceryVendorProfileCreate(BaseModel):
    shop_name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    city: str = Field(min_length=2, max_length=50)
    area: str = Field(min_length=2, max_length=100)
    full_address: str = Field(min_length=10, max_length=300)
    pincode: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    phone: str = Field(min_length=10, max_length=13)
    delivery_radius_km: float = Field(default=5.0, gt=0, le=50)
    min_order_amount_paise: int = Field(default=10000, gt=0)
    delivery_charge_paise: int = Field(default=2000, ge=0)
    free_delivery_above_paise: Optional[int] = Field(None, gt=0)
    working_hours_start: str = Field(default="08:00")
    working_hours_end: str = Field(default="22:00")
    accepts_cash_on_delivery: bool = True


class GroceryCartItem(BaseModel):
    product_id: str
    quantity: float = Field(gt=0)


class GroceryOrderCreate(BaseModel):
    vendor_id: str
    items: List[GroceryCartItem] = Field(min_length=1, max_length=50)
    delivery_address: str = Field(min_length=10, max_length=300)
    delivery_pincode: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    special_instructions: Optional[str] = Field(None, max_length=300)
    idempotency_key: str = Field(min_length=8, max_length=128)


class GroceryOrderStatusUpdate(BaseModel):
    status: GroceryOrderStatus
    note: Optional[str] = Field(None, max_length=200)
