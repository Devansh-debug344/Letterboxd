"""Thin async wrapper around Cloudinary for server-side media uploads.

Uploads happen directly from the API: upload_image sends the raw bytes to
Cloudinary and returns the hosted metadata. No local file is ever stored.
"""
from __future__ import annotations

import cloudinary
import cloudinary.api
import cloudinary.uploader

from app.config import setting

cloudinary.config(
    cloud_name=setting.CLOUDINARY_CLOUD_NAME,
    api_key=setting.CLOUDINARY_API_KEY,
    api_secret=setting.CLOUDINARY_API_SECRET if setting.CLOUDINARY_API_SECRET else None,
    secure=True,
)

_FOLDER = setting.CLOUDINARY_FOLDER.rstrip("/")


def cloudinary_configured() -> bool:
    return bool(setting.CLOUDINARY_CLOUD_NAME and setting.CLOUDINARY_API_KEY and setting.CLOUDINARY_API_SECRET)


def upload_image(
    data: bytes,
    *,
    folder: str = "",
    public_id: str | None = None,
    resource_type: str = "image",
) -> dict:
    """Upload raw bytes to Cloudinary and return the asset metadata.

    Returns at least ``public_id``, ``secure_url``, ``url``, ``format``,
    ``width`` and ``height``.
    """
    params: dict = {"folder": f"{_FOLDER}/{folder}".rstrip("/"), "resource_type": resource_type, "overwrite": True}
    if public_id:
        params["public_id"] = public_id
    return cloudinary.uploader.upload(data, **params)

#security ticket to directly upload to cloudinary from the browser 
def generate_upload_signature(*, timestamp_s: int | None = None, folder: str | None = None, **extra: str) -> dict:
    """Build the params + signature for a direct client-side upload to Cloudinary."""
    import time

    import cloudinary.utils

    params = extra.copy()
    folder = folder or ""
    if folder:
        params["folder"] = f"{_FOLDER}/{folder}".rstrip("/")
    params.setdefault("timestamp", timestamp_s or int(time.time()))
    signature = cloudinary.utils.api_sign_request(params, setting.CLOUDINARY_API_SECRET or "")
    return {"params": params, "signature": signature, "api_key": setting.CLOUDINARY_API_KEY, "cloud_name": setting.CLOUDINARY_CLOUD_NAME}


def delete_image(public_id: str) -> dict:
    """Delete a previously uploaded asset by its public id."""
    return cloudinary.api.delete_resources([public_id])