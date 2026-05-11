from fastapi import APIRouter, Query

from app.schemas.common import OutfitPart
from app.schemas.outfit import OutfitItem
from app.services import outfit as outfit_service

router = APIRouter()


@router.get("/outfit", response_model=list[OutfitItem])
async def get_outfit(
    part: OutfitPart = Query(...),
    minPrice: int = Query(..., ge=0),
    maxPrice: int = Query(..., le=500_000),
) -> list[OutfitItem]:
    return await outfit_service.get_outfits(part, minPrice, maxPrice)
