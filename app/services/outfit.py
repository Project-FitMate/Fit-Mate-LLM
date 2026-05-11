from app.clients import gemini, naver
from app.prompts import load
from app.schemas.common import OutfitPart
from app.schemas.outfit import OutfitItem

_PART_LABEL_KO = {
    OutfitPart.FULL: "전신 코디",
    OutfitPart.TOP: "상의",
    OutfitPart.BOTTOM: "하의",
    OutfitPart.OUTER: "아우터",
    OutfitPart.DRESS: "원피스",
    OutfitPart.SHOES: "신발",
    OutfitPart.HAT: "모자",
}


async def get_outfits(part: OutfitPart, min_price: int, max_price: int) -> list[OutfitItem]:
    template = load("query_default")
    system, user = template.render(
        part=part.value,
        part_label=_PART_LABEL_KO[part],
        min_price=min_price,
        max_price=max_price,
    )
    query = gemini.generate_text(system_prompt=system, user_prompt=user)

    shop_items = await naver.search_shop(query)

    results: list[OutfitItem] = []
    for it in shop_items:
        if it.price < min_price or it.price > max_price:
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
