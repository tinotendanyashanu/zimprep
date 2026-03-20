"""
OCR route — accepts an uploaded image, runs Google Cloud Vision handwriting extraction,
uploads the image to Supabase Storage, and returns the image URL + extracted text.
"""

from __future__ import annotations

import uuid
import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from supabase import create_client

from core.config import settings
from services.ocr_service import extract_handwriting

log = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 1 * 1024 * 1024  # 1 MB (client should compress before sending)


class OCRResponse(BaseModel):
    image_url: str
    extracted_text: str


def _get_sb():
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@router.post("/ocr", response_model=OCRResponse)
async def ocr_image(
    file: UploadFile = File(...),
    question_id: str = Form(...),
):
    """
    1. Validate image size / type.
    2. Upload to Supabase Storage (answer-images bucket).
    3. Run Google Cloud Vision document-text-detection.
    4. Return { image_url, extracted_text }.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Use JPEG, PNG, or WEBP.",
        )

    image_bytes = await file.read()

    if len(image_bytes) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Image too large ({len(image_bytes)} bytes). Client must compress to < 1 MB.",
        )

    # Upload to Supabase Storage
    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
    storage_path = f"answers/{question_id}/{uuid.uuid4().hex[:8]}.{ext}"
    image_url = ""

    if settings.supabase_url and settings.supabase_service_role_key:
        try:
            sb = _get_sb()
            sb.storage.from_("answer-images").upload(
                storage_path,
                image_bytes,
                {"content-type": file.content_type or "image/jpeg"},
            )
            image_url = (
                f"{settings.supabase_url}/storage/v1/object/public/answer-images/{storage_path}"
            )
        except Exception as exc:
            log.warning("Supabase upload failed (non-fatal): %s", exc)

    # Run OCR
    try:
        extracted_text = await extract_handwriting(image_bytes)
    except Exception as exc:
        log.exception("OCR failed")
        raise HTTPException(status_code=502, detail=f"OCR failed: {exc}")

    return OCRResponse(image_url=image_url, extracted_text=extracted_text)
