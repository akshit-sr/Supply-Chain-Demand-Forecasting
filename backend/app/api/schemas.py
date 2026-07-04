from __future__ import annotations

from pydantic import BaseModel, Field

from app.config import settings


class ForecastRequest(BaseModel):
    series_id: str
    horizon: int = Field(default=settings.default_horizon, ge=1, le=settings.max_horizon)


class InventoryRequest(BaseModel):
    series_id: str
    lead_time_days: int = Field(default=settings.default_lead_time_days, ge=1, le=180)
    service_level: float = Field(default=settings.default_service_level, ge=0.5, le=0.999)
    order_cost: float = Field(default=settings.default_order_cost, ge=0)
    # If omitted, holding cost is derived from the product's unit price.
    holding_cost: float | None = Field(default=None, gt=0)


class StockoutRequest(BaseModel):
    series_id: str
    on_hand: float = Field(ge=0)
    lead_time_days: int = Field(default=settings.default_lead_time_days, ge=1, le=180)


class ReorderRequest(BaseModel):
    series_id: str
    on_hand: float = Field(ge=0)
    lead_time_days: int = Field(default=settings.default_lead_time_days, ge=1, le=180)
    service_level: float = Field(default=settings.default_service_level, ge=0.5, le=0.999)
    order_cost: float = Field(default=settings.default_order_cost, ge=0)
    # If omitted, holding cost is derived from the product's unit price.
    holding_cost: float | None = Field(default=None, gt=0)


class ReorderAllRequest(BaseModel):
    lead_time_days: int = Field(default=settings.default_lead_time_days, ge=1, le=180)
    service_level: float = Field(default=settings.default_service_level, ge=0.5, le=0.999)
    order_cost: float = Field(default=settings.default_order_cost, ge=0)
    # If omitted, holding cost is derived from the product's unit price.
    holding_cost: float | None = Field(default=None, gt=0)
    on_hand_days: float = Field(default=10.0, ge=0, le=120)
    limit: int | None = Field(default=None, ge=1, le=200)


class PlaceOrderRequest(BaseModel):
    series_id: str
    order_qty: float = Field(gt=0)
