from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm

from app.config import settings
from app.core.data import product_meta
from app.ml.forecaster import forecaster


def _forecast_stats(series_id: str, lead_time: int, horizon: int,
                    forecast: np.ndarray | None = None) -> tuple[np.ndarray, float, float]:
    """Return (forecast vector, mean daily demand, daily std) over the horizon.

    Pass `forecast` to reuse an already-computed forecast (avoids recomputing it for
    the same series across inventory + stock-out, e.g. in the all-series reorder view).
    """
    horizon = max(horizon, lead_time)
    fc = forecast if forecast is not None else forecaster.forecast_array(series_id, horizon)
    mean_daily = float(np.mean(fc))
    # Daily demand variability: combine forecast variation with model residual std.
    fc_std = float(np.std(fc))
    resid_std = forecaster.residual_std
    daily_std = float(math.sqrt(fc_std ** 2 + resid_std ** 2))
    return fc, mean_daily, daily_std


def optimize(series_id: str, lead_time: int, service_level: float,
             order_cost: float, holding_cost: float | None = None, horizon: int = 28,
             forecast: np.ndarray | None = None) -> dict:
    fc, mean_daily, daily_std = _forecast_stats(series_id, lead_time, horizon, forecast)

    meta = product_meta(series_id)
    unit_price = max(float(meta.get("price_current", 1.0)), 0.01)
    # Default holding cost = 25%/yr of the item's unit price (typical grocery carrying cost).
    if holding_cost is None or holding_cost <= 0:
        holding_cost = unit_price * settings.default_holding_cost_rate

    z = float(norm.ppf(min(max(service_level, 0.5), 0.9999)))
    demand_over_lead = mean_daily * lead_time
    safety_stock = z * daily_std * math.sqrt(lead_time)
    reorder_point = demand_over_lead + safety_stock

    annual_demand = mean_daily * 365.0
    if holding_cost <= 0:
        eoq = 0.0
    else:
        eoq = math.sqrt(2.0 * annual_demand * order_cost / holding_cost)

    # Order-up-to (target) level for a periodic review of `lead_time` days.
    order_up_to = mean_daily * (2 * lead_time) + safety_stock

    # Expected annual cost at EOQ (ordering + holding of cycle + safety stock).
    if eoq > 0:
        orders_per_year = annual_demand / eoq
        annual_ordering_cost = orders_per_year * order_cost
        annual_holding_cost = (eoq / 2.0 + safety_stock) * holding_cost
    else:
        annual_ordering_cost = annual_holding_cost = 0.0

    return {
        "series_id": series_id,
        "model": forecaster.winner,
        "product_name": meta.get("product_name", ""),
        "brand": meta.get("brand", ""),
        "department": meta.get("department", ""),
        "location": meta.get("location", ""),
        "unit_price": round(unit_price, 2),
        "lot_size": float(meta.get("lot_size", 1)),
        "inputs": {
            "lead_time_days": lead_time,
            "service_level": round(service_level, 4),
            "order_cost": order_cost,
            "holding_cost": round(holding_cost, 4),
            "z_score": round(z, 4),
        },
        "mean_daily_demand": round(mean_daily, 2),
        "daily_demand_std": round(daily_std, 2),
        "annual_demand": round(annual_demand, 1),
        "demand_over_lead_time": round(demand_over_lead, 2),
        "safety_stock": round(safety_stock, 2),
        "reorder_point": round(reorder_point, 2),
        "economic_order_qty": round(eoq, 2),
        "order_up_to_level": round(order_up_to, 2),
        "estimated_annual_ordering_cost": round(annual_ordering_cost, 2),
        "estimated_annual_holding_cost": round(annual_holding_cost, 2),
        "estimated_total_annual_cost": round(annual_ordering_cost + annual_holding_cost, 2),
    }
