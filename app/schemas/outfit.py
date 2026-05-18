from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import MimeType, OutfitPart


class RecommendRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    part: OutfitPart
    min_price: int = Field(alias="minPrice", ge=0)
    max_price: int = Field(alias="maxPrice", le=500_000)
    user_image: str = Field(alias="userImage")
    user_image_mime_type: MimeType | None = Field(default=None, alias="userImageMimeType")


class OutfitItem(BaseModel):
    image: str
    brand: str
    name: str
    price: int
    link: str
