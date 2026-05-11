from fastapi import APIRouter, Depends

from app.core.auth import require_api_key
from app.schemas.recommend import RecommendRequest, RecommendResponse
from app.services import recommender

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest) -> RecommendResponse:
    return await recommender.recommend(req)
