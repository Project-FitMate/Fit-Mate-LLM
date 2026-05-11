from fastapi import APIRouter, Depends

from app.core.auth import require_api_key
from app.schemas.fitting import FittingRequest, FittingResponse
from app.services import fitter

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/fitting", response_model=FittingResponse)
async def fitting(req: FittingRequest) -> FittingResponse:
    return await fitter.fit(req)
