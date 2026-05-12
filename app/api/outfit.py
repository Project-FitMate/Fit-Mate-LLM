from fastapi import APIRouter

from app.schemas.outfit import OutfitItem, RecommendRequest
from app.services import outfit as outfit_service

router = APIRouter()


@router.post("/outfit", response_model=list[OutfitItem])
async def post_outfit(req: RecommendRequest) -> list[OutfitItem]:
    return await outfit_service.get_outfits(req)
