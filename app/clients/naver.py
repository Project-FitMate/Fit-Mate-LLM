import re
from dataclasses import dataclass

import httpx
from fastapi import HTTPException, status

from app.config import settings

_SHOP_URL = "https://openapi.naver.com/v1/search/shop.json"
_TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class ShopItem:
    title: str
    image_url: str
    product_url: str
    price: int
    mall_name: str
    category: str
    brand: str


def _strip(text: str) -> str:
    return _TAG_RE.sub("", text or "")


async def search_shop(query: str, display: int | None = None) -> list[ShopItem]:
    headers = {
        "X-Naver-Client-Id": settings.naver_client_id,
        "X-Naver-Client-Secret": settings.naver_client_secret,
    }
    params = {"query": query, "display": display or settings.naver_search_display}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(_SHOP_URL, headers=headers, params=params)

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"naver search failed: {resp.status_code}",
        )

    items = []
    for raw in resp.json().get("items", []):
        try:
            price = int(raw.get("lprice") or 0)
        except (TypeError, ValueError):
            price = 0
        items.append(
            ShopItem(
                title=_strip(raw.get("title", "")),
                image_url=raw.get("image", ""),
                product_url=raw.get("link", ""),
                price=price,
                mall_name=raw.get("mallName", ""),
                category=raw.get("category1", ""),
                brand=_strip(raw.get("brand") or raw.get("maker") or ""),
            )
        )
    return items
