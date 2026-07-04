from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import PlaceOrderRequest, ReorderAllRequest, ReorderRequest
from app.services.reorder import suggest, suggest_all

router = APIRouter(prefix="/api", tags=["reorder"])


@router.post("/reorder")
def post_reorder(req: ReorderRequest):
    try:
        return suggest(
            req.series_id, req.on_hand, req.lead_time_days,
            req.service_level, req.order_cost, req.holding_cost,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/reorder/all")
def post_reorder_all(req: ReorderAllRequest):
    """Ranked reorder suggestions across all series (for the Reorder dashboard table)."""
    try:
        return suggest_all(
            req.lead_time_days, req.service_level, req.order_cost,
            req.holding_cost, req.on_hand_days, req.limit,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/reorder/place")
def post_place_order(req: PlaceOrderRequest):
    """Simulate placing a reorder."""
    import time
    # Simulate processing delay
    time.sleep(0.5)
    return {"status": "success", "message": f"Order placed for {req.order_qty} units of {req.series_id}."}
