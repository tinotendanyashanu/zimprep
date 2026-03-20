"""
OCR service using Google Cloud Vision for handwriting extraction.
Falls back to Claude Vision if GCV credentials are not configured.
"""

import json
import base64
import os
from core.config import settings


async def extract_handwriting(image_bytes: bytes) -> str:
    """
    Extract handwritten text from image bytes.
    Uses Google Cloud Vision if credentials are set, otherwise Claude Vision.
    """
    if settings.google_application_credentials:
        return await _gcv_extract(image_bytes)
    else:
        return await _claude_vision_extract(image_bytes)


async def _gcv_extract(image_bytes: bytes) -> str:
    """Extract text using Google Cloud Vision API."""
    from google.cloud import vision as gvision
    from google.oauth2 import service_account

    creds_raw = settings.google_application_credentials.strip()

    try:
        # Try parsing as JSON string first
        creds_info = json.loads(creds_raw)
        credentials = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        client = gvision.ImageAnnotatorClient(credentials=credentials)
    except (json.JSONDecodeError, ValueError):
        # It's a file path
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_raw
        client = gvision.ImageAnnotatorClient()

    image = gvision.Image(content=image_bytes)
    response = client.document_text_detection(image=image)

    if response.error.message:
        raise RuntimeError(f"Google Cloud Vision error: {response.error.message}")

    return response.full_text_annotation.text or ""


async def _claude_vision_extract(image_bytes: bytes) -> str:
    """Fallback: extract handwriting using Claude Vision (Anthropic)."""
    import anthropic as ant

    if not settings.anthropic_api_key:
        raise RuntimeError(
            "Neither GOOGLE_APPLICATION_CREDENTIALS nor ANTHROPIC_API_KEY is set. "
            "Cannot perform OCR."
        )

    client = ant.Anthropic(api_key=settings.anthropic_api_key)
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Please transcribe ALL handwritten text in this image exactly as written. "
                            "Include every word, number, and symbol. "
                            "Return ONLY the transcribed text — no commentary, no formatting."
                        ),
                    },
                ],
            }
        ],
    )

    return response.content[0].text.strip()
