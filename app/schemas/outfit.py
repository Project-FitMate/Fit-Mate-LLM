from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import MimeType, OutfitPart

# 각 옷은 0~500,000원. 전체 예산 상한은 선택한 부위 수만큼 비례한다.
MAX_PRICE_PER_PART = 500_000


class RecommendRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    parts: list[OutfitPart] = Field(min_length=1)
    min_price: int = Field(alias="minPrice", ge=0)
    max_price: int = Field(alias="maxPrice", ge=0)
    user_image: str = Field(alias="userImage")
    user_image_mime_type: MimeType | None = Field(default=None, alias="userImageMimeType")
    # Optional user-provided keyword (product name/style). When present the
    # query generator prioritises it on top of the image-based analysis.
    keyword: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def _check_budget(self) -> "RecommendRequest":
        if self.max_price > MAX_PRICE_PER_PART * len(self.parts):
            raise ValueError("maxPrice exceeds budget for selected parts")
        return self


class OutfitItem(BaseModel):
    part: OutfitPart
    image: str
    brand: str
    name: str
    price: int
    link: str
