import asyncio

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


async def get_outfits(req: RecommendRequest) -> list[OutfitItem]:
    if req.min_price > req.max_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="minPrice must be <= maxPrice",
        )

    template = load("query_default")
    system, user = template.render(
        part=req.part.value,
        part_label=_PART_LABEL_KO[req.part],
    )
    # google-genai's generate_content is sync and manages its own httpx Client;
    # calling it directly from FastAPI's async loop closes that client mid-flight.
    # Mirror fitter.py and run it in a worker thread. The image is re-encoded to
    # JPEG inside the client, so any decodable format is accepted here.
    try:
        query = await asyncio.to_thread(
            gemini.generate_text,
            system_prompt=system,
            user_prompt=user,
            images=[req.user_image],
        )
    except (OSError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid or undecodable user image",
        ) from e

    # Gemini occasionally returns an empty/whitespace query (e.g. no person in
    # the photo). An empty query makes Naver reject the request with 400, which
    # we'd surface as a 502. Fall back to a part-based query so recommendation
    # still works.
    query = (query or "").strip()
    if not query:
        query = _PART_LABEL_KO[req.part]

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
    print(
        f"[outfit] query={query!r} part={req.part.value} "
        f"price_range=[{req.min_price},{req.max_price}] "
        f"shop_items={len(shop_items)} filtered={len(results)}",
        flush=True,
    )
    return results
