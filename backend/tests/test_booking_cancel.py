from types import SimpleNamespace
from unittest.mock import patch
import inspect

import pytest

from routers.bookings import BookingCancelRequest, cancel_booking


pytestmark = pytest.mark.asyncio


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def start_transaction(self):
        return FakeTransaction()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeClient:
    async def start_session(self):
        return FakeSession()


class FakeCollection:
    def __init__(self, db, name):
        self.db = db
        self.name = name

    async def find_one(self, query, projection=None, session=None):
        if self.name == "bookings":
            return dict(self.db.booking)
        if self.name == "payments":
            return dict(self.db.payment)
        if self.name == "vendors":
            return {"id": "vendor_1", "user_id": "vendor_user_1"}
        return None

    async def find_one_and_update(self, query, update, projection=None, return_document=None, session=None):
        self.db.booking.update(update.get("$set", {}))
        self.db.booking["version"] += update.get("$inc", {}).get("version", 0)
        return dict(self.db.booking)

    async def update_one(self, query, update, session=None):
        if self.name == "vendor_ledger":
            self.db.vendor_ledger_doc["total_earned_paise"] += update["$inc"]["total_earned_paise"]
            self.db.vendor_ledger_doc["pending_payout_paise"] += update["$inc"]["pending_payout_paise"]
        if self.name == "payments":
            self.db.payment.update(update.get("$set", {}))
        return SimpleNamespace(modified_count=1)

    async def update_many(self, query, update, session=None):
        for lock in self.db.resource_lock_docs:
            if lock["id"] in query["id"]["$in"]:
                lock.update(update["$set"])
        return SimpleNamespace(modified_count=len(self.db.resource_lock_docs))

    async def insert_one(self, doc, session=None):
        self.db.inserts.append((self.name, doc))
        return SimpleNamespace(inserted_id=doc.get("id"))


class FakeDB:
    def __init__(self):
        self.client = FakeClient()
        self.inserts = []
        self.booking = {
            "id": "book_1",
            "user_id": "user_1",
            "vendor_id": "vendor_1",
            "status": "PAYMENT_RECEIVED",
            "version": 1,
            "payment_id": "pay_1",
            "vendor_net_paise": 7000,
            "amount_gross_paise": 10000,
            "resource_lock_ids": ["lock_1", "lock_2"],
            "items": [],
            "meta": {},
        }
        self.payment = {
            "id": "pay_1",
            "amount": 10000,
            "razorpay_payment_id": "rzp_pay_1",
            "status": "CONFIRMED",
        }
        self.vendor_ledger_doc = {
            "vendor_id": "vendor_1",
            "total_earned_paise": 20000,
            "pending_payout_paise": 15000,
        }
        self.resource_lock_docs = [
            {"id": "lock_1", "status": "ACTIVE"},
            {"id": "lock_2", "status": "ACTIVE"},
        ]

    def __getattr__(self, name):
        return FakeCollection(self, name)

    def __getitem__(self, name):
        return FakeCollection(self, name)


class FakeRefundApi:
    def refund(self, payment_id, payload):
        return {"id": "rfnd_1", "payment_id": payment_id, "payload": payload}


async def _cancel(db, refund_api):
    request = SimpleNamespace(
        state=SimpleNamespace(request_id="req_1"),
        app=SimpleNamespace(
            state=SimpleNamespace(
                db=db,
                razorpay_client=SimpleNamespace(payment=refund_api),
            )
        ),
    )
    return await inspect.unwrap(cancel_booking)(
        "book_1",
        BookingCancelRequest(reason="Customer cancelled", expected_version=1),
        request,
        {"id": "user_1", "role": "customer"},
    )


async def test_cancel_reverses_ledger():
    db = FakeDB()
    refund_api = FakeRefundApi()

    await _cancel(db, refund_api)

    assert db.vendor_ledger_doc["total_earned_paise"] == 13000
    assert db.vendor_ledger_doc["pending_payout_paise"] == 8000


async def test_cancel_releases_locks():
    db = FakeDB()
    refund_api = FakeRefundApi()

    await _cancel(db, refund_api)

    assert {lock["status"] for lock in db.resource_lock_docs} == {"RELEASED"}


async def test_cancel_refunds_razorpay():
    db = FakeDB()
    refund_api = FakeRefundApi()

    with patch.object(refund_api, "refund", wraps=refund_api.refund) as refund:
        await _cancel(db, refund_api)

    refund.assert_called_once()
    assert refund.call_args.args[0] == "rzp_pay_1"
