from __future__ import annotations

import json
import threading

import numpy as np
import pandas as pd

from app.config import FEATURE_META_FILE, LSTM_FILE, MODEL_FILE
from app.core.data import get_series_frame
from app.core.features import add_calendar, add_lag_features
from app.ml.models import LSTMForecaster

_Z_90 = 1.6449  # z-score for 90% interval (two-sided -> +/- 1.6449 sigma per side ~ 90%)


class Forecaster:
    """Singleton-ish wrapper. Lazy-loads the model on first use."""

    def __init__(self):
        self._lock = threading.Lock()
        self._loaded = False
        self.meta: dict = {}
        self.winner: str = ""
        self.tree_model = None
        self.lstm: LSTMForecaster | None = None

    # ------------------------------------------------------------------ #
    def load(self):
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            if not FEATURE_META_FILE.exists():
                raise RuntimeError(
                    "No trained model found. Run: uv run python -m app.ml.train"
                )
            self.meta = json.loads(FEATURE_META_FILE.read_text())
            self.winner = self.meta["winner"]

            if self.winner in ("XGBoost", "LightGBM"):
                import joblib

                inner = joblib.load(MODEL_FILE)
                self.tree_model = inner
            else:
                import torch

                n_series = len(self.meta["series_code"])
                self.lstm = LSTMForecaster(
                    n_series=n_series,
                    hidden=self.meta.get("lstm_hidden", 64),
                    emb_dim=self.meta.get("lstm_emb_dim", 16),
                )
                self.lstm.net = self.lstm._build_net()
                self.lstm.net.load_state_dict(
                    torch.load(LSTM_FILE, map_location=self.lstm.device)
                )
                self.lstm.net.eval()
            self._loaded = True

    @property
    def residual_std(self) -> float:
        return float(self.meta.get("residual_std", 0.0))

    # ------------------------------------------------------------------ #
    def forecast(self, series_id: str, horizon: int) -> dict:
        """Return forecast dict: dates, mean, lower, upper, plus recent history."""
        self.load()
        frame = get_series_frame(series_id)
        code = self.meta["series_code"].get(series_id)
        if code is None:
            raise KeyError(f"Series not in trained model: {series_id}")

        if self.winner in ("XGBoost", "LightGBM"):
            preds = self._tree_forecast(frame, code, horizon)
        else:
            preds = self._lstm_forecast(frame, code, horizon)

        last_date = frame["date"].iloc[-1]
        future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon, freq="D")

        # Prediction interval widens with sqrt(step) — uncertainty compounds.
        sd = self.residual_std
        steps = np.arange(1, horizon + 1)
        band = _Z_90 * sd * np.sqrt(steps)
        lower = np.clip(preds - band, 0, None)
        upper = preds + band

        hist_tail = frame.tail(90)
        return {
            "series_id": series_id,
            "model": self.winner,
            "horizon": horizon,
            "history": [
                {"date": d.strftime("%Y-%m-%d"), "actual": round(float(v), 2)}
                for d, v in zip(hist_tail["date"], hist_tail["target"])
            ],
            "forecast": [
                {
                    "date": d.strftime("%Y-%m-%d"),
                    "mean": round(float(m), 2),
                    "lower": round(float(lo), 2),
                    "upper": round(float(hi), 2),
                }
                for d, m, lo, hi in zip(future_dates, preds, lower, upper)
            ],
        }

    def forecast_array(self, series_id: str, horizon: int) -> np.ndarray:
        """Just the mean forecast vector (used by inventory/stockout/reorder)."""
        self.load()
        frame = get_series_frame(series_id)
        code = self.meta["series_code"].get(series_id)
        if code is None:
            raise KeyError(f"Series not in trained model: {series_id}")
        if self.winner in ("XGBoost", "LightGBM"):
            return self._tree_forecast(frame, code, horizon)
        return self._lstm_forecast(frame, code, horizon)

    def forecast_arrays_batch(self, series_ids: list[str], horizon: int) -> dict[str, np.ndarray]:
        """Forecast many series efficiently.

        For the LSTM winner this runs a single batched recursive rollout on the
        accelerator instead of one Python loop per series, which is dramatically
        faster for the all-series reorder view.
        """
        self.load()
        codes = self.meta["series_code"]
        valid = [sid for sid in series_ids if sid in codes]

        if self.winner not in ("XGBoost", "LightGBM"):
            lookback = self.lstm.lookback
            windows = np.empty((len(valid), lookback), dtype="float32")
            code_arr = np.empty(len(valid), dtype="int64")
            for i, sid in enumerate(valid):
                demand = get_series_frame(sid).sort_values("date")["target"].values
                windows[i] = np.log1p(demand[-lookback:])
                code_arr[i] = codes[sid]
            preds = self.lstm.predict_batch(windows, code_arr, horizon)
            return {sid: preds[i] for i, sid in enumerate(valid)}

        # Tree models are fast enough per-call; reuse the single-series path.
        return {sid: self.forecast_array(sid, horizon) for sid in valid}

    # ------------------------------------------------------------------ #
    def _tree_forecast(self, frame: pd.DataFrame, code: int, horizon: int) -> np.ndarray:
        feat_cols = self.meta["feature_columns"]
        hist = frame[["date", "target"]].sort_values("date").copy()
        preds = []
        for _ in range(horizon):
            next_date = hist["date"].iloc[-1] + pd.Timedelta(days=1)
            hist = pd.concat(
                [hist, pd.DataFrame({"date": [next_date], "target": [np.nan]})],
                ignore_index=True,
            )
            tmp = add_calendar(hist.copy())
            tmp = add_lag_features(tmp)
            tmp["series_code"] = code
            row = tmp.iloc[[-1]][feat_cols].fillna(0.0)
            yhat = float(np.clip(self.tree_model.predict(row)[0], 0, None))
            preds.append(yhat)
            hist.loc[hist.index[-1], "target"] = yhat
        return np.array(preds)

    def _lstm_forecast(self, frame: pd.DataFrame, code: int, horizon: int) -> np.ndarray:
        demand = frame.sort_values("date")["target"].values
        lookback = self.lstm.lookback
        window = list(np.log1p(demand[-lookback:]))
        preds = []
        for _ in range(horizon):
            yhat = self.lstm.predict_window(np.array(window[-lookback:]), code)
            preds.append(yhat)
            window.append(np.log1p(yhat))
        return np.array(preds)


forecaster = Forecaster()
