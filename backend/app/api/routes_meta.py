from __future__ import annotations

import json

import numpy as np
from fastapi import APIRouter

from app.config import METRICS_FILE
from app.core.data import (
    build_panel,
    list_departments,
    list_products,
    list_series,
)

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/meta/series")
def get_series():
    """All modeled product-location series with demand + catalog summary."""
    return list_series()


@router.get("/products")
def get_products(
    search: str | None = None,
    department: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """Browse the full product catalog (paginated, searchable, filterable)."""
    return list_products(search=search, department=department, limit=limit, offset=offset)


@router.get("/meta/departments")
def get_departments():
    return list_departments()


@router.get("/kpis")
def get_kpis():
    """Top-level dashboard KPIs (catalog scale + modeled demand + model accuracy)."""
    panel = build_panel()
    series = list_series()
    catalog = list_products(limit=1)  # just need the total count

    last_date = panel["date"].max()
    last_30 = panel[panel["date"] > last_date - np.timedelta64(30, "D")]
    prev_30 = panel[
        (panel["date"] <= last_date - np.timedelta64(30, "D"))
        & (panel["date"] > last_date - np.timedelta64(60, "D"))
    ]
    cur = float(last_30["target"].sum())
    prev = float(prev_30["target"].sum())
    growth = ((cur - prev) / prev * 100.0) if prev else 0.0

    n_departments = len({s["department"] for s in series})
    n_locations = len({s["location"] for s in series})
    inventory_value = sum(s["price_current"] * s["total_demand"] for s in series)

    model_wape = None
    model_name = None
    model_skill = None
    if METRICS_FILE.exists():
        m = json.loads(METRICS_FILE.read_text())
        model_name = m.get("winner")
        results = m.get("results", {})
        model_wape = results.get(model_name, {}).get("WAPE")
        base_wape = results.get("SeasonalNaive", {}).get("WAPE")
        if model_wape is not None and base_wape:
            model_skill = round((1 - model_wape / base_wape) * 100, 1)

    return {
        "total_products_catalog": catalog["total"],
        "modeled_series": len(series),
        "modeled_departments": n_departments,
        "modeled_locations": n_locations,
        "total_demand_modeled": int(panel["target"].sum()),
        "demand_last_30d": round(cur, 0),
        "demand_growth_30d_pct": round(growth, 1),
        "avg_daily_demand": round(float(panel.groupby("date")["target"].sum().mean()), 1),
        "inventory_throughput_value": round(inventory_value, 0),
        "data_start": panel["date"].min().strftime("%Y-%m-%d"),
        "data_end": last_date.strftime("%Y-%m-%d"),
        "model": model_name,
        "model_wape": model_wape,
        "model_skill_pct": model_skill,
    }


@router.get("/model/metrics")
def get_model_metrics():
    """The full bake-off comparison (XGBoost vs LightGBM vs LSTM vs baseline)."""
    if not METRICS_FILE.exists():
        return {"error": "Model not trained yet. Run: python -m app.ml.train"}
    return json.loads(METRICS_FILE.read_text())


@router.get("/trend")
def get_trend(days: int = 180):
    """Aggregate daily demand trend across all modeled series."""
    panel = build_panel()
    daily = panel.groupby("date")["target"].sum().reset_index()
    daily = daily.tail(days)
    return [
        {"date": d.strftime("%Y-%m-%d"), "demand": round(float(v), 0)}
        for d, v in zip(daily["date"], daily["target"])
    ]
