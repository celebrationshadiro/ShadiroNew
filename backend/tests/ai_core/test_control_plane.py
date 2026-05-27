from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from ai_core.control_plane import ControlPlane


class _Collection:
    def __init__(self):
        self.docs = {}

    async def find_one_and_update(self, query, update, upsert=False, return_document=None):
        key = query.get("_id")
        doc = self.docs.get(key, {"_id": key, "count": 0})
        doc["count"] = int(doc.get("count", 0)) + int(update.get("$inc", {}).get("count", 0))
        doc.update(update.get("$set", {}))
        self.docs[key] = doc
        return doc

    async def insert_one(self, doc):
        self.docs[doc["_id"]] = doc
        return SimpleNamespace(inserted_id=doc["_id"])

    async def find_one(self, query):
        return self.docs.get(query.get("_id"))


class _DB:
    def __init__(self):
        self.ai_rate_limits = _Collection()
        self.ai_control_config = _Collection()
        self.ai_rollback_logs = _Collection()


@pytest.mark.anyio
async def test_api_key_and_rate_limit_guard():
    db = _DB()
    config = SimpleNamespace(ai_api_key="k1", ai_rate_limit_per_minute=2, ai_rate_limit_ttl_seconds=120)
    cp = ControlPlane(db, config)
    req = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))

    await cp.guard_request(req, "k1")
    await cp.guard_request(req, "k1")
    with pytest.raises(Exception):
        await cp.guard_request(req, "k1")


@pytest.mark.anyio
async def test_rollback_log_write():
    db = _DB()
    cp = ControlPlane(db, SimpleNamespace(ai_api_key="k1", ai_rate_limit_per_minute=2, ai_rate_limit_ttl_seconds=120))
    await cp.rollback_log(model_type="risk", target_version=3, actor="admin")
    assert len(db.ai_rollback_logs.docs) == 1
