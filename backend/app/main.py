from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    routes_forecast,
    routes_inventory,
    routes_meta,
    routes_reorder,
    routes_stockout,
)
from app.config import FEATURE_META_FILE, settings

app = FastAPI(
    title="Supply Chain Demand Forecasting Platform",
    description=(
        "Demand forecasting, inventory optimization, stock-out prediction, and "
        "dynamic reorder suggestions powered by a benchmarked ML model "
        "(XGBoost vs LightGBM vs LSTM)."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"http://localhost(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_meta.router)
app.include_router(routes_forecast.router)
app.include_router(routes_inventory.router)
app.include_router(routes_stockout.router)
app.include_router(routes_reorder.router)


@app.get("/health", tags=["meta"])
def health():
    return {
        "status": "ok",
        "model_trained": FEATURE_META_FILE.exists(),
    }


@app.get("/", tags=["meta"])
def root():
    return {
        "name": "Supply Chain Demand Forecasting Platform",
        "docs": "/docs",
        "health": "/health",
    }
