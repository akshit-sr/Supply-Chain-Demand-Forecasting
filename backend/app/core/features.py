from __future__ import annotations

import numpy as np
import pandas as pd

LAGS = [1, 2, 3, 7, 14, 28]
ROLL_WINDOWS = [7, 14, 28]
EWMA_SPANS = [7, 28]

# Columns the model consumes (categoricals encoded separately below).
CALENDAR_FEATURES = [
    "dow",
    "dom",
    "month",
    "weekofyear",
    "is_weekend",
    "is_month_start",
    "is_month_end",
]


def add_calendar(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    d = df[date_col].dt
    df["dow"] = d.dayofweek
    df["dom"] = d.day
    df["month"] = d.month
    df["weekofyear"] = d.isocalendar().week.astype(int)
    df["is_weekend"] = (d.dayofweek >= 5).astype(int)
    df["is_month_start"] = d.is_month_start.astype(int)
    df["is_month_end"] = d.is_month_end.astype(int)
    return df


def add_lag_features(df: pd.DataFrame, target: str = "target") -> pd.DataFrame:
    """Add lag / rolling / ewma features. Assumes `df` is a single series sorted by date."""
    s = df[target]
    for lag in LAGS:
        df[f"lag_{lag}"] = s.shift(lag)
    for w in ROLL_WINDOWS:
        shifted = s.shift(1)  # only use past values
        df[f"roll_mean_{w}"] = shifted.rolling(w, min_periods=1).mean()
        df[f"roll_std_{w}"] = shifted.rolling(w, min_periods=2).std()
        df[f"roll_max_{w}"] = shifted.rolling(w, min_periods=1).max()
    for span in EWMA_SPANS:
        df[f"ewma_{span}"] = s.shift(1).ewm(span=span, adjust=False).mean()
    return df


def feature_columns() -> list[str]:
    cols: list[str] = []
    cols += [f"lag_{l}" for l in LAGS]
    for w in ROLL_WINDOWS:
        cols += [f"roll_mean_{w}", f"roll_std_{w}", f"roll_max_{w}"]
    cols += [f"ewma_{span}" for span in EWMA_SPANS]
    cols += CALENDAR_FEATURES
    cols += ["series_code"]  # ordinal-encoded series id
    return cols


def build_training_matrix(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Build the full feature matrix across all series.

    Returns the feature frame (with `target`, `series_id`, `date`) and the mapping
    series_id -> integer code used as a categorical feature.
    """
    series_ids = sorted(panel["series_id"].unique())
    series_code = {sid: i for i, sid in enumerate(series_ids)}

    parts = []
    for sid, g in panel.groupby("series_id", sort=False):
        g = g.sort_values("date").copy()
        g = add_calendar(g)
        g = add_lag_features(g)
        g["series_code"] = series_code[sid]
        parts.append(g)

    feat = pd.concat(parts, ignore_index=True)
    feat = feat.dropna(subset=[f"lag_{max(LAGS)}"]).reset_index(drop=True)
    feat = feat.fillna(0.0)
    return feat, series_code


def build_history_for_inference(series_frame: pd.DataFrame, series_code: int) -> pd.DataFrame:
    """Prepare a single-series history frame (calendar + lag features) for recursive
    forecasting. Returns the frame with all engineered columns; the caller appends
    future rows and recomputes features step by step."""
    g = series_frame.sort_values("date").copy()
    g = add_calendar(g)
    g = add_lag_features(g)
    g["series_code"] = series_code
    return g.fillna(0.0)
