from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from app.auth.oauth import get_current_user
from app.schemas.login import DataToken
from app.services.cloudinary_service import cloudinary_configured, generate_upload_signature, upload_image
from app.services.rate_limiter import rate_limiter

router = APIRouter(prefix="/media", tags=["Media"])

MAX_FILE_BYTES = 5 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _require_configured() -> None:
    if not cloudinary_configured():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Media uploads are not configured.")


@router.post("/upload")
async def upload_media(
    current_user: DataToken = Depends(get_current_user),
    file: UploadFile = File(...),
    request: Request = None,
):
    _require_configured()
    await rate_limiter.enforce(request, "media:upload", user_id=current_user.id, max_attempts=20, window_seconds=60)

    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG, WebP and GIF images are allowed.",
        )

    data = await file.read(MAX_FILE_BYTES + 1)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file is too large (max 5 MB).",
        )

    public_id = f"user_{current_user.id}/media/{uuid4().hex}"
    try:
        result = upload_image(data, folder="uploads", public_id=public_id, resource_type="image")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Media upload failed.") from exc

    return {
        "public_id": result.get("public_id"),
        "secure_url": result.get("secure_url"),
        "url": result.get("url"),
        "format": result.get("format"),
        "width": result.get("width"),
        "height": result.get("height"),
        "bytes": result.get("bytes"),
    }


@router.get("/upload-signature")
async def get_upload_signature(
    current_user: DataToken = Depends(get_current_user),
    request: Request = None,
):
    """Signed parameters for a direct browser-to-Cloudinary upload."""
    _require_configured()
    await rate_limiter.enforce(request, "media:signature", user_id=current_user.id, max_attempts=60, window_seconds=60)

    return generate_upload_signature(
        folder="uploads",
        public_id=f"user_{current_user.id}/media/{uuid4().hex}",
        resource_type="image",
    )