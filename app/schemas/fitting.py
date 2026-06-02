from pydantic import BaseModel, ConfigDict, Field


class FittingRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_image: str = Field(alias="userImage")
    outfit_images: list[str] = Field(alias="outfitImages", min_length=1)


class FittingResponse(BaseModel):
    image: str
