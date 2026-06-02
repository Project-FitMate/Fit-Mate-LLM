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

    async def _for_part(part: OutfitPart) -> list[OutfitItem]:
        system, user = template.render(
            part=part.value,
            part_label=_PART_LABEL_KO[part],
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
            images=[req.user_image],
        )

        # Gemini occasionally returns an empty/whitespace query (e.g. no person
        # in the photo). An empty query makes Naver reject the request with 400,
        # which we'd surface as a 502. Fall back to a part-based query so
        # recommendation still works.
        query = (query or "").strip() or _PART_LABEL_KO[part]

        shop_items = await naver.search_shop(query)

        items: list[OutfitItem] = []
        for it in shop_items:
            if it.price < req.min_price or it.price > req.max_price:
                continue
            items.append(
                OutfitItem(
                    part=part,
                    image=it.image_url,
                    brand=it.brand or it.mall_name,
                    name=it.title,
                    price=it.price,
                    link=it.product_url,
                )
            )
        print(
            f"[outfit] query={query!r} part={part.value} "
            f"price_range=[{req.min_price},{req.max_price}] "
            f"shop_items={len(shop_items)} filtered={len(items)}",
            flush=True,
        )
        return items

    per_part = await asyncio.gather(*(_for_part(part) for part in req.parts))

    results: list[OutfitItem] = []
    seen: set[str] = set()
    for items in per_part:
        for item in items:
            if item.link in seen:
                continue
            seen.add(item.link)
            results.append(item)
    return results
