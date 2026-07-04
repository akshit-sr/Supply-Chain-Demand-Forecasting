from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.data import build_panel, list_series
from app.ml.forecaster import forecaster
from app.services.inventory import optimize
from app.services.stockout import predict as predict_stockout


def suggest(series_id: str, on_hand: float, lead_time: int, service_level: float,
            order_cost: float, holding_cost: float | None = None,
            forecast: "np.ndarray | None" = None) -> dict:
    # Compute the forecast once and share it between inventory + stock-out.
    inv = optimize(series_id, lead_time, service_level, order_cost, holding_cost,
                   forecast=forecast)
    so = predict_stockout(series_id, on_hand, lead_time, forecast=forecast)

    rop = inv["reorder_point"]
    order_up_to = inv["order_up_to_level"]
    eoq = inv["economic_order_qty"]

    should_reorder = on_hand <= rop
    # Quantity: top up to order-up-to level, but never below EOQ when ordering.
    raw_qty = max(order_up_to - on_hand, 0.0)
    order_qty = max(raw_qty, eoq) if should_reorder else 0.0

    # Recommend ordering `lead_time` days before projected stock-out.
    from app.core.data import get_last_date
    last_date = get_last_date()
    if so["days_until_stockout"] is not None:
        order_in_days = max(so["days_until_stockout"] - lead_time, 0)
        recommended_date = (last_date + pd.Timedelta(days=order_in_days)).strftime("%Y-%m-%d")
    else:
        order_in_days = None
        recommended_date = None

    if so["risk_level"] in ("critical", "high") or (should_reorder and on_hand <= rop * 0.5):
        urgency = "urgent"
    elif should_reorder:
        urgency = "soon"
    else:
        urgency = "ok"

    return {
        "series_id": series_id,
        "model": inv["model"],
        "product_name": inv.get("product_name", ""),
        "brand": inv.get("brand", ""),
        "department": inv.get("department", ""),
        "location": inv.get("location", ""),
        "unit_price": inv.get("unit_price", 0),
        "on_hand": round(on_hand, 2),
        "reorder_point": rop,
        "should_reorder": should_reorder,
        "recommended_order_qty": round(order_qty, 2),
        "order_up_to_level": order_up_to,
        "economic_order_qty": eoq,
        "recommended_order_date": recommended_date,
        "order_in_days": order_in_days,
        "urgency": urgency,
        "stockout_probability": so["stockout_probability"],
        "risk_level": so["risk_level"],
        "projected_stockout_date": so["projected_stockout_date"],
    }


def suggest_all(lead_time: int, service_level: float, order_cost: float,
                holding_cost: float | None = None, on_hand_days: float = 10.0,
                limit: int | None = None) -> list[dict]:
    """Generate reorder suggestions across all series.

    `on_hand_days` simulates current inventory as N days of average demand (since the
    dataset has no live stock levels). Results are ranked by urgency / stock-out risk.
    """
    out = []
    series = list_series()
    if limit:
        series = series[:limit]

    # Forecast every series in one batched pass (a single accelerator rollout for the
    # LSTM) instead of recomputing a recursive forecast per inventory/stock-out call.
    horizon = max(28, lead_time)
    sids = [s["series_id"] for s in series]
    forecasts = forecaster.forecast_arrays_batch(sids, horizon)

    for s in series:
        sid = s["series_id"]
        on_hand = s["avg_daily_demand"] * on_hand_days
        try:
            rec = suggest(sid, on_hand, lead_time, service_level, order_cost,
                          holding_cost, forecast=forecasts.get(sid))
        except Exception:
            continue
        # product fields already attached by suggest(); keep list metadata in sync
        rec["product_name"] = s["product_name"]
        rec["brand"] = s["brand"]
        rec["department"] = s["department"]
        rec["location"] = s["location"]
        out.append(rec)

    urgency_rank = {"urgent": 0, "soon": 1, "ok": 2}
    out.sort(key=lambda r: (urgency_rank.get(r["urgency"], 3), -r["stockout_probability"]))
    return out
