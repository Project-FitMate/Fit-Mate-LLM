from fastapi import APIRouter

from app.schemas.fitting import FittingRequest, FittingResponse
from app.services import fitter

router = APIRouter()


@router.post("/fitting", response_model=FittingResponse)
async def fitting(req: FittingRequest) -> FittingResponse:
    return await fitter.fit(req)
