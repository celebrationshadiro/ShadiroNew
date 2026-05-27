"""Cloud media storage - Cloudinary integration for vendor images."""
import os
import logging
from typing import Optional, List
import base64

logger = logging.getLogger(__name__)

CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "")

_cloudinary = None


def _get_cloudinary():
    global _cloudinary
    if _cloudinary is None and CLOUDINARY_CLOUD_NAME:
        try:
            import cloudinary
            import cloudinary.uploader
            cloudinary.config(
                cloud_name=CLOUDINARY_CLOUD_NAME,
                api_key=CLOUDINARY_API_KEY,
                api_secret=CLOUDINARY_API_SECRET,
            )
            _cloudinary = cloudinary
        except ImportError:
            logger.warning("cloudinary package not installed. Run: pip install cloudinary")
            return None
    return _cloudinary


async def upload_image(
    file_content: bytes,
    folder: str = "shadiro",
    public_id_prefix: Optional[str] = None,
    transformation: Optional[dict] = None,
) -> Optional[str]:
    """Upload image to Cloudinary and return secure URL."""
    cloud = _get_cloudinary()
    if not cloud:
        return None

    try:
        import cloudinary.uploader
        import uuid

        public_id = f"{folder}/{public_id_prefix or str(uuid.uuid4())}"
        result = cloudinary.uploader.upload(
            file_content,
            folder=folder,
            public_id=public_id[:100],
            overwrite=True,
            transformation=transformation or [{"quality": "auto", "fetch_format": "auto"}],
        )
        return result.get("secure_url")
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {str(e)}")
        return None


async def upload_file(
    file_content: bytes,
    filename: str,
    folder: str = "shadiro",
    public_id_prefix: Optional[str] = None,
    resource_type: str = "raw",
) -> Optional[str]:
    """Upload arbitrary file (pdf, doc, etc.) to Cloudinary and return secure URL."""
    cloud = _get_cloudinary()
    if not cloud:
        return None

    try:
        import cloudinary.uploader
        import uuid

        public_id = f"{folder}/{public_id_prefix or str(uuid.uuid4())}"
        result = cloudinary.uploader.upload(
            file_content,
            folder=folder,
            public_id=public_id[:100],
            resource_type=resource_type,
            filename_override=filename,
            overwrite=True,
        )
        return result.get("secure_url")
    except Exception as e:
        logger.error(f"Cloudinary file upload failed: {str(e)}")
        return None


async def upload_base64_image(
    base64_data: str,
    folder: str = "shadiro",
    public_id_prefix: Optional[str] = None,
) -> Optional[str]:
    """Upload base64-encoded image to Cloudinary."""
    try:
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]
        file_content = base64.b64decode(base64_data)
        return await upload_image(file_content, folder=folder, public_id_prefix=public_id_prefix)
    except Exception as e:
        logger.error(f"Base64 decode failed: {str(e)}")
        return None


def delete_image(public_id: str) -> bool:
    """Delete image from Cloudinary by public_id."""
    cloud = _get_cloudinary()
    if not cloud:
        return False

    try:
        import cloudinary.uploader
        cloudinary.uploader.destroy(public_id)
        return True
    except Exception as e:
        logger.error(f"Cloudinary delete failed: {str(e)}")
        return False


def is_configured() -> bool:
    """Check if Cloudinary is configured."""
    return bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET)
