import asyncio
import base64

from fastapi import HTTPException, status

from app.clients import gemini
from app.config import settings
from app.prompts import load
from app.schemas.fitting import FittingRequest, FittingResponse


async def fit(req: FittingRequest) -> FittingResponse:
    template = load("fitting_default")
    system, user = template.render()

    # Both images are re-encoded to JPEG inside the client, so GIF/WebP product
    # images (Naver serves these despite .jpg URLs) are accepted here.
    images = [req.user_image, req.outfit_image]

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
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="이미지 합성에 실패했습니다 (모델이 이미지를 반환하지 않음).",
        ) from e
    except (OSError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid or undecodable image",
        ) from e

    return FittingResponse(image=base64.b64encode(result.data).decode("ascii"))
