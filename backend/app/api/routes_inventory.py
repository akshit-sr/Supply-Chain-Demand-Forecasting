from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import InventoryRequest
from app.services.inventory import optimize

router = APIRouter(prefix="/api", tags=["inventory"])


@router.post("/inventory")
def post_inventory(req: InventoryRequest):
    try:
        return optimize(
            req.series_id, req.lead_time_days, req.service_level,
            req.order_cost, req.holding_cost,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
