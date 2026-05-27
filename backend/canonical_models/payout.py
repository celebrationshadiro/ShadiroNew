from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from canonical_models.common import LedgerEntryType, PayoutStatus, utcnow


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class VendorLedgerEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: _new_id("led"))
    vendor_id: str
    booking_id: str
    entry_type: LedgerEntryType
    amount_paise: int = Field(ge=0)
    balance_after_paise: int = Field(ge=0)
    note: str = ""
    created_at: datetime = Field(default_factory=utcnow)


class PayoutRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vendor_id: str
    note: str = ""


class Payout(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: _new_id("po"))
    vendor_id: str
    amount_paise: int = Field(ge=0)
    status: PayoutStatus = PayoutStatus.PENDING
    note: str = ""
    approved_by: Optional[str] = None
    processed_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

