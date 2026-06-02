import asyncio
import base64

from fastapi import HTTPException, status

from app.clients import gemini
from app.config import settings
from app.prompts import load
from app.schemas.fitting import FittingRequest, FittingResponse


def _detect_mime(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="unsupported image format (expected png/jpeg/webp)",
    )


def _mime_of(b64: str) -> str:
    try:
        return _detect_mime(base64.b64decode(b64, validate=False)[:32])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid base64 image",
        ) from e


async def fit(req: FittingRequest) -> FittingResponse:
    template = load("fitting_default")
    system, user = template.render()

    images = [(req.user_image, _mime_of(req.user_image))] + [
        (o, _mime_of(o)) for o in req.outfit_images
    ]

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                gemini.compose_images,
                system_prompt=system,
                user_prompt=user,
                images=images,
            ),
            timeout=settings.fitting_timeout_seconds,
        )
    except asyncio.TimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="fitting generation timed out",
        ) from e

    return FittingResponse(image=base64.b64encode(result.data).decode("ascii"))
