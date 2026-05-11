from app.clients import gemini, naver
from app.prompts import load
from app.schemas.recommend import (
    RecommendItem,
    RecommendRequest,
    RecommendResponse,
)


async def recommend(req: RecommendRequest) -> RecommendResponse:
    template_name = req.prompt_template or "query_default"
    template = load(template_name)

    price_min, price_max = req.selections.price_range or (0, 0)
    system, user = template.render(
        categories=", ".join(c.value for c in req.selections.categories) or "(미지정)",
        price_min=price_min,
        price_max=price_max,
        style_keywords=", ".join(req.selections.style_keywords) or "(미지정)",
    )

    query = gemini.generate_text(
        system_prompt=system,
        user_prompt=user,
        images=[(req.user_image, req.mime_type.value)],
    )

    shop_items = await naver.search_shop(query)
    items = [
        RecommendItem(
            title=it.title,
            image_url=it.image_url,
            product_url=it.product_url,
            price=it.price,
            mall_name=it.mall_name,
            category=it.category,
        )
        for it in shop_items
    ]
    return RecommendResponse(query=query, items=items)
