from datetime import datetime, timezone
from typing import Any, Dict, Optional

from models import AuditLog


async def log_audit_event(
    db,
    action_type: str,
    performed_by: str,
    entity_type: str,
    entity_id: str,
    old_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    performed_by_id: Optional[str] = None,
) -> None:
    try:
        log = AuditLog(
            action_type=action_type,
            performed_by=performed_by,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value or {},
            new_value=new_value or {},
            performed_by_id=performed_by_id,
            timestamp=datetime.now(timezone.utc),
        ).model_dump()
        log["timestamp"] = log["timestamp"].isoformat()
        await db.audit_logs.insert_one(log)
    except Exception:
        # Never break main flow on audit logging failures
        pass
