import asyncio
import base64

from fastapi import HTTPException, status

from app.clients import gemini, naver
from app.prompts import load
from app.schemas.common import OutfitPart
from app.schemas.outfit import OutfitItem, RecommendRequest

_PART_LABEL_KO = {
    OutfitPart.FULL: "전신 코디",
    OutfitPart.TOP: "상의",
    OutfitPart.BOTTOM: "하의",
    OutfitPart.OUTER: "아우터",
    OutfitPart.DRESS: "원피스",
    OutfitPart.SHOES: "신발",
    OutfitPart.HAT: "모자",
}


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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid base64 image",
        ) from e


async def get_outfits(req: RecommendRequest) -> list[OutfitItem]:
    if req.min_price > req.max_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="minPrice must be <= maxPrice",
        )

    mime = req.user_image_mime_type.value if req.user_image_mime_type else _mime_of(req.user_image)

    template = load("query_default")
    system, user = template.render(
        part=req.part.value,
        part_label=_PART_LABEL_KO[req.part],
        min_price=req.min_price,
        max_price=req.max_price,
    )
    # google-genai's generate_content is sync and manages its own httpx Client;
    # calling it directly from FastAPI's async loop closes that client mid-flight.
    # Mirror fitter.py and run it in a worker thread.
    query = await asyncio.to_thread(
        gemini.generate_text,
        system_prompt=system,
        user_prompt=user,
        images=[(req.user_image, mime)],
    )

    shop_items = await naver.search_shop(query)

    results: list[OutfitItem] = []
    for it in shop_items:
        if it.price < req.min_price or it.price > req.max_price:
            continue
        results.append(
            OutfitItem(
                image=it.image_url,
                brand=it.brand or it.mall_name,
                name=it.title,
                price=it.price,
                link=it.product_url,
            )
        )
    return results
