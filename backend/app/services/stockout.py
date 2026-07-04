
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import norm

from app.core.data import get_last_date, product_meta
from app.ml.forecaster import forecaster


def _risk_level(prob: float) -> str:
    if prob >= 0.5:
        return "critical"
    if prob >= 0.2:
        return "high"
    if prob >= 0.05:
        return "medium"
    return "low"


def predict(series_id: str, on_hand: float, lead_time: int, horizon: int = 28,
            forecast: np.ndarray | None = None) -> dict:
    horizon = max(horizon, lead_time)
    fc = forecast if forecast is not None else forecaster.forecast_array(series_id, horizon)
    resid_std = forecaster.residual_std

    mu_lt = float(np.sum(fc[:lead_time]))
    daily_std = float(math.sqrt(np.var(fc[:lead_time]) + resid_std ** 2))
    sigma_lt = daily_std * math.sqrt(lead_time)

    if sigma_lt > 0:
        prob_stockout = float(1.0 - norm.cdf(on_hand, loc=mu_lt, scale=sigma_lt))
    else:
        prob_stockout = 1.0 if on_hand < mu_lt else 0.0
    prob_stockout = min(max(prob_stockout, 0.0), 1.0)

    # Projected depletion: walk the cumulative forecast until it exceeds on_hand.
    cum = np.cumsum(fc)
    last_date = get_last_date()
    stockout_day = None
    for i, c in enumerate(cum):
        if c >= on_hand:
            stockout_day = i + 1
            break

    projected_date = None
    days_until = None
    if stockout_day is not None:
        projected_date = (last_date + pd.Timedelta(days=stockout_day)).strftime("%Y-%m-%d")
        days_until = stockout_day

    meta = product_meta(series_id)
    return {
        "series_id": series_id,
        "model": forecaster.winner,
        "product_name": meta.get("product_name", ""),
        "brand": meta.get("brand", ""),
        "location": meta.get("location", ""),
        "on_hand": round(on_hand, 2),
        "lead_time_days": lead_time,
        "expected_demand_over_lead_time": round(mu_lt, 2),
        "demand_std_over_lead_time": round(sigma_lt, 2),
        "stockout_probability": round(prob_stockout, 4),
        "risk_level": _risk_level(prob_stockout),
        "projected_stockout_date": projected_date,
        "days_until_stockout": days_until,
        "covered_by_current_stock": stockout_day is None,
    }
