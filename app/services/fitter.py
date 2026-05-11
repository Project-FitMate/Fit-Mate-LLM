import asyncio
import base64

from fastapi import HTTPException, status

from app.clients import gemini
from app.config import settings
from app.prompts import load
from app.schemas.fitting import FittingRequest, FittingResponse


async def fit(req: FittingRequest) -> FittingResponse:
    template_name = req.prompt_template or "fitting_default"
    template = load(template_name)
    system, user = template.render()

    images = [(req.user_image, req.mime_type.value)]
    images.extend((img, req.mime_type.value) for img in req.item_images)

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

    return FittingResponse(
        result_image=base64.b64encode(result.data).decode("ascii"),
        mime_type=result.mime_type,
    )
