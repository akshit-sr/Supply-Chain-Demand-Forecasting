from __future__ import annotations

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
# Tree models
# --------------------------------------------------------------------------- #
class XGBModel:
    name = "XGBoost"

    def __init__(self):
        from xgboost import XGBRegressor

        self.model = XGBRegressor(
            n_estimators=600,
            learning_rate=0.05,
            max_depth=8,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=5,
            reg_lambda=1.0,
            tree_method="hist",
            n_jobs=-1,
            random_state=42,
        )

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        self.model.fit(X, y)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.clip(self.model.predict(X), 0, None)


class LGBMModel:
    name = "LightGBM"

    def __init__(self):
        from lightgbm import LGBMRegressor

        self.model = LGBMRegressor(
            n_estimators=800,
            learning_rate=0.05,
            num_leaves=64,
            max_depth=-1,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_samples=20,
            reg_lambda=1.0,
            n_jobs=-1,
            random_state=42,
            verbose=-1,
        )

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        self.model.fit(X, y)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.clip(self.model.predict(X), 0, None)


# --------------------------------------------------------------------------- #
# LSTM (PyTorch, XPU-aware)
# --------------------------------------------------------------------------- #
def get_device():
    import torch

    if hasattr(torch, "xpu") and torch.xpu.is_available():
        return torch.device("xpu")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


LSTM_LOOKBACK = 28


class LSTMForecaster:
    """Global LSTM: input = last `lookback` demand values (log1p-scaled) + series embedding.
    Predicts the next day's demand. Recursive rollout produces multi-step forecasts."""

    name = "LSTM"

    def __init__(self, n_series: int, lookback: int = LSTM_LOOKBACK,
                 hidden: int = 64, emb_dim: int = 16, epochs: int = 8, batch_size: int = 512):
        self.n_series = n_series
        self.lookback = lookback
        self.hidden = hidden
        self.emb_dim = emb_dim
        self.epochs = epochs
        self.batch_size = batch_size
        self.device = get_device()
        self.net = None

    def _build_net(self):
        import torch.nn as nn

        class Net(nn.Module):
            def __init__(self, n_series, hidden, emb_dim):
                super().__init__()
                self.emb = nn.Embedding(n_series, emb_dim)
                self.lstm = nn.LSTM(input_size=1, hidden_size=hidden, num_layers=2,
                                    batch_first=True, dropout=0.1)
                self.head = nn.Sequential(
                    nn.Linear(hidden + emb_dim, 64), nn.ReLU(), nn.Linear(64, 1)
                )

            def forward(self, seq, sid):
                out, _ = self.lstm(seq)              # (B, L, H)
                last = out[:, -1, :]                 # (B, H)
                e = self.emb(sid)                    # (B, E)
                return self.head(torch.cat([last, e], dim=1)).squeeze(-1)

        import torch  # noqa: F401 (used above)
        return Net(self.n_series, self.hidden, self.emb_dim).to(self.device)

    def _make_windows(self, panel_codes: dict[str, int], series_arrays: dict[str, np.ndarray]):
        """Build sliding windows from each series' log1p demand array."""
        Xseq, Xsid, Y = [], [], []
        for sid, arr in series_arrays.items():
            code = panel_codes[sid]
            log = np.log1p(arr)
            for i in range(self.lookback, len(log)):
                Xseq.append(log[i - self.lookback:i])
                Xsid.append(code)
                Y.append(log[i])
        return (np.array(Xseq, dtype="float32")[..., None],
                np.array(Xsid, dtype="int64"),
                np.array(Y, dtype="float32"))

    def fit(self, panel_codes: dict[str, int], series_arrays: dict[str, np.ndarray]):
        import torch
        from torch.utils.data import DataLoader, TensorDataset

        Xseq, Xsid, Y = self._make_windows(panel_codes, series_arrays)
        ds = TensorDataset(torch.from_numpy(Xseq), torch.from_numpy(Xsid), torch.from_numpy(Y))
        dl = DataLoader(ds, batch_size=self.batch_size, shuffle=True)

        self.net = self._build_net()
        opt = torch.optim.Adam(self.net.parameters(), lr=1e-3)
        loss_fn = torch.nn.SmoothL1Loss()

        self.net.train()
        for epoch in range(self.epochs):
            total = 0.0
            for seq, sid, y in dl:
                seq, sid, y = seq.to(self.device), sid.to(self.device), y.to(self.device)
                opt.zero_grad()
                pred = self.net(seq, sid)
                loss = loss_fn(pred, y)
                loss.backward()
                opt.step()
                total += loss.item() * len(y)
            print(f"    [LSTM] epoch {epoch + 1}/{self.epochs} loss={total / len(ds):.4f}")
        return self

    def predict_window(self, window_log: np.ndarray, series_code: int) -> float:
        """Predict next-day demand (original scale) from a log1p lookback window."""
        import torch

        self.net.eval()
        with torch.no_grad():
            seq = torch.from_numpy(window_log.astype("float32")[None, :, None]).to(self.device)
            sid = torch.tensor([series_code], dtype=torch.long, device=self.device)
            pred_log = self.net(seq, sid).item()
        return float(max(0.0, np.expm1(pred_log)))

    def predict_batch(self, windows_log: np.ndarray, series_codes: np.ndarray,
                      horizon: int) -> np.ndarray:
        """Recursively forecast `horizon` steps for many series at once.

        windows_log : (N, lookback) log1p demand windows
        series_codes: (N,) integer series codes
        returns     : (N, horizon) forecasts on the original scale
        """
        import torch

        self.net.eval()
        n = windows_log.shape[0]
        window = torch.from_numpy(windows_log.astype("float32")).to(self.device)  # (N, L)
        sid = torch.tensor(series_codes, dtype=torch.long, device=self.device)
        out = np.empty((n, horizon), dtype="float32")
        with torch.no_grad():
            for h in range(horizon):
                seq = window.unsqueeze(-1)                      # (N, L, 1)
                pred_log = self.net(seq, sid)                   # (N,)
                pred = torch.clamp(torch.expm1(pred_log), min=0.0)
                out[:, h] = pred.detach().cpu().numpy()
                # slide window: drop oldest, append new (in log space)
                window = torch.cat([window[:, 1:], torch.log1p(pred).unsqueeze(1)], dim=1)
        return out
