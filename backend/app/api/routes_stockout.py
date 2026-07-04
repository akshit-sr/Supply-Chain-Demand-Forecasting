from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import StockoutRequest
from app.services.stockout import predict

router = APIRouter(prefix="/api", tags=["stockout"])


@router.post("/stockout")
def post_stockout(req: StockoutRequest):
    try:
        return predict(req.series_id, req.on_hand, req.lead_time_days)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
