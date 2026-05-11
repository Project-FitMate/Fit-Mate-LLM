from pydantic import BaseModel, ConfigDict, Field


class FittingRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_image: str = Field(alias="userImage")
    outfit_image: str = Field(alias="outfitImage")


class FittingResponse(BaseModel):
    image: str
