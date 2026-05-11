from pydantic import BaseModel, Field

from app.schemas.common import MimeType


class FittingRequest(BaseModel):
    user_image: str  # base64
    item_images: list[str] = Field(min_length=1)  # base64
    mime_type: MimeType
    prompt_template: str | None = None


class FittingResponse(BaseModel):
    result_image: str  # base64
    mime_type: str
