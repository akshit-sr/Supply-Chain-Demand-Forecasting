from __future__ import annotations

import functools
import numpy as np
import pandas as pd

DATA_DIR = "data"
ITEMS_FILE = f"{DATA_DIR}/items.csv"
STORES_FILE = f"{DATA_DIR}/stores.csv"
TRAIN_FILE = f"{DATA_DIR}/train_top1000.csv"

def series_id(sku: int | str, location: str | int) -> str:
    return f"{sku}@{location}"

def split_series_id(sid: str) -> tuple[str, str]:
    sku, _, loc = sid.partition("@")
    return sku, loc

@functools.lru_cache(maxsize=1)
def load_items() -> pd.DataFrame:
    df = pd.read_csv(ITEMS_FILE)
    df["item_nbr"] = df["item_nbr"].astype(str)
    
    # Simulate Prices based on family
    np.random.seed(42)
    families = df["family"].unique()
    baseline = {f: round(np.random.uniform(1.5, 25.0), 2) for f in families}
    df["price_retail"] = df["family"].map(baseline)
    
    # Add some variation per item
    df["price_retail"] = df["price_retail"] + np.random.uniform(-0.5, 2.0, len(df))
    df["price_retail"] = df["price_retail"].round(2).clip(lower=0.5)
    
    df["price_current"] = df["price_retail"]
    
    df = df.rename(columns={
        "family": "department",
        "class": "category"
    })
    df["brand"] = "Favorita"
    df["product_name"] = "Item " + df["item_nbr"]
    df["sku"] = df["item_nbr"]
    df["lot_size"] = 1.0
    return df

@functools.lru_cache(maxsize=1)
def load_stores() -> pd.DataFrame:
    df = pd.read_csv(STORES_FILE)
    df["store_nbr"] = df["store_nbr"].astype(str)
    df = df.rename(columns={"store_nbr": "location"})
    return df

@functools.lru_cache(maxsize=1)
def build_panel() -> pd.DataFrame:
    train = pd.read_csv(TRAIN_FILE)
    train["item_nbr"] = train["item_nbr"].astype(str)
    train["store_nbr"] = train["store_nbr"].astype(str)
    
    train = train.rename(columns={
        "unit_sales": "target",
        "store_nbr": "location",
        "item_nbr": "sku"
    })
    
    train["series_id"] = train["sku"] + "@" + train["location"]
    train["date"] = pd.to_datetime(train["date"])
    
    train["target"] = train["target"].clip(lower=0)
    
    np.random.seed(42)
    promo_discount = np.random.uniform(0.1, 0.3, len(train))
    train["onpromotion"] = train["onpromotion"].fillna(False).astype(bool)
    train["discount_pct"] = np.where(train["onpromotion"], promo_discount * 100, 0.0)
    
    delay_chance = np.random.uniform(0, 1, len(train))
    train["supplier_delay_days"] = np.where(delay_chance < 0.05, np.random.randint(1, 15, len(train)), 0)
    
    return train.sort_values(["series_id", "date"]).reset_index(drop=True)

@functools.lru_cache(maxsize=1)
def _series_lookup() -> dict[str, dict]:
    panel = build_panel()
    unique_series = panel[["series_id", "sku", "location"]].drop_duplicates()
    items = load_items()
    stores = load_stores()
    
    merged = unique_series.merge(items, on="sku", how="left")
    merged = merged.merge(stores, on="location", how="left")
    return {r["series_id"]: r.to_dict() for _, r in merged.iterrows()}

@functools.lru_cache(maxsize=1)
def get_last_date() -> pd.Timestamp:
    return build_panel()["date"].max()

def product_meta(sid: str) -> dict:
    info = _series_lookup().get(sid)
    if info is None:
        raise KeyError(f"Unknown series_id: {sid!r}")
    return info

@functools.lru_cache(maxsize=1)
def list_series() -> list[dict]:
    panel = build_panel()
    lookup = _series_lookup()
    out = []
    for sid, g in panel.groupby("series_id", sort=False):
        info = lookup.get(sid, {})
        out.append(
            {
                "series_id": sid,
                "sku": info.get("sku", ""),
                "product_name": info.get("product_name", ""),
                "brand": info.get("brand", ""),
                "department": info.get("department", ""),
                "category": info.get("category", ""),
                "location": info.get("location", ""),
                "price_current": round(float(info.get("price_current", 0)), 2),
                "price_retail": round(float(info.get("price_retail", 0)), 2),
                "lot_size": float(info.get("lot_size", 1)),
                "avg_daily_demand": round(float(g["target"].mean()), 2),
                "total_demand": int(g["target"].sum()),
            }
        )
    return out

@functools.lru_cache(maxsize=1)
def _grouped_series_frames() -> dict[str, pd.DataFrame]:
    panel = build_panel()
    return {sid: g.reset_index(drop=True) for sid, g in panel.groupby("series_id", sort=False)}

def get_series_frame(sid: str) -> pd.DataFrame:
    frames = _grouped_series_frames()
    if sid not in frames:
        raise KeyError(f"Unknown series_id: {sid!r}")
    return frames[sid]

def list_products(
    search: str | None = None,
    department: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    items = load_items()
    if department:
        items = items[items["department"] == department]
    if search:
        s = search.lower()
        mask = items["product_name"].str.lower().str.contains(s, na=False)
        items = items[mask]
        
    total = len(items)
    page = items.iloc[offset : offset + limit]
    results = []
    for _, r in page.iterrows():
        results.append({
            "sku": r["sku"],
            "product_name": r["product_name"],
            "brand": r["brand"],
            "department": r["department"],
            "category": str(r["category"]),
            "price_current": round(float(r["price_current"]), 2),
            "price_retail": round(float(r["price_retail"]), 2),
            "discount_pct": 0.0,
            "lot_size": float(r["lot_size"]),
        })
    return {"total": total, "offset": offset, "limit": limit, "items": results}

def list_departments() -> list[str]:
    return sorted(load_items()["department"].dropna().unique().tolist())
