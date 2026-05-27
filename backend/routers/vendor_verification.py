from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from datetime import datetime, timezone

from auth import get_current_user, require_role
from models import UserRole
from cloud_storage import upload_file, is_configured
from services.audit_logger import log_audit_event

router = APIRouter(prefix="/api/vendor/verification", tags=["vendor-verification"])


@router.post("/upload")
async def upload_verification_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role([UserRole.VENDOR]))
):
    db = request.app.state.db
    vendor_doc = await db.vendors.find_one({"user_id": current_user["sub"]}, {"_id": 0})
    if not vendor_doc:
        raise HTTPException(status_code=404, detail="Vendor not found")

    if not is_configured():
        raise HTTPException(status_code=400, detail="Cloud storage not configured")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    filename = file.filename or "document"
    content_type = file.content_type or "application/octet-stream"
    url = await upload_file(content, filename=filename, folder="shadiro/verification", resource_type="raw")
    if not url:
        raise HTTPException(status_code=500, detail="Upload failed")

    doc = {
        "id": f"ver_{vendor_doc['id']}_{len(vendor_doc.get('verification_documents', []))}",
        "url": url,
        "filename": filename,
        "content_type": content_type,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
    }

    await db.vendors.update_one(
        {"id": vendor_doc["id"]},
        {"$push": {"verification_documents": doc}, "$set": {"verification_status": "pending"}}
    )
    await log_audit_event(
        db,
        action_type="vendor_bank_verification_change",
        performed_by="vendor",
        performed_by_id=current_user.get("sub"),
        entity_type="vendor",
        entity_id=vendor_doc["id"],
        old_value={"verification_status": vendor_doc.get("verification_status")},
        new_value={"verification_status": "pending"},
    )

    return doc
