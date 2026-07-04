from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
DATA_FILE = DATA_DIR / "WMT_Grocery_202209.csv"

# Generated model artifacts
MODEL_FILE = ARTIFACTS_DIR / "model.joblib"        # winning tree model (xgb/lgbm)
LSTM_FILE = ARTIFACTS_DIR / "model_lstm.pt"        # lstm weights (if it wins)
FEATURE_META_FILE = ARTIFACTS_DIR / "feature_meta.json"
METRICS_FILE = ARTIFACTS_DIR / "metrics.json"
CATALOG_FILE = ARTIFACTS_DIR / "catalog.parquet"   # cleaned product catalog cache

# Forecast target = simulated daily units sold for a product at a location.
TARGET = "units"

# How much daily history to simulate per product-location series (days).
HISTORY_DAYS = 540

# The catalog has ~30k products; training ML on every product x location is
# infeasible. We model demand for the top-N most relevant products (popular,
# everyday items) across all shipping locations. The full catalog is still
# browsable via the Products endpoint.
MODELED_PRODUCTS = 60        # number of distinct SKUs to model
MODELED_LOCATIONS = 6        # number of shipping locations per modeled SKU


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SCDF_", extra="ignore")

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5180",
        "http://localhost:4173",
        "http://localhost",
    ]

    # Default business assumptions (overridable per request)
    default_lead_time_days: int = 7
    default_service_level: float = 0.95
    default_order_cost: float = 50.0        # fixed cost per purchase order ($)
    # Holding cost defaults to a fraction of unit price (set per product in services).
    default_holding_cost_rate: float = 0.25  # 25% of unit cost / year

    max_horizon: int = 90
    default_horizon: int = 28


settings = Settings()
