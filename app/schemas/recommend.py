from pydantic import BaseModel, Field

from app.schemas.common import Category, MimeType


class Selections(BaseModel):
    categories: list[Category] = Field(default_factory=list)
    price_range: tuple[int, int] | None = None  # (min, max)
    style_keywords: list[str] = Field(default_factory=list)


class RecommendRequest(BaseModel):
    user_image: str  # base64
    mime_type: MimeType
    selections: Selections
    prompt_template: str | None = None


class RecommendItem(BaseModel):
    title: str
    image_url: str
    product_url: str
    price: int
    mall_name: str
    category: str


class RecommendResponse(BaseModel):
    query: str
    items: list[RecommendItem]
