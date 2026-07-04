from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import ForecastRequest
from app.ml.forecaster import forecaster

router = APIRouter(prefix="/api", tags=["forecast"])


@router.post("/forecast")
def post_forecast(req: ForecastRequest):
    try:
        return forecaster.forecast(req.series_id, req.horizon)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/forecast/{series_id}")
def get_forecast(series_id: str, horizon: int = 28):
    return post_forecast(ForecastRequest(series_id=series_id, horizon=horizon))
