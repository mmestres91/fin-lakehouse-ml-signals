# features_v1.py
# flake8: noqa: E501

import pandas as pd


def compute_momentum(df: pd.DataFrame, windows=[5, 10, 20]) -> pd.DataFrame:
    """Add mom_{N}d = (close/close.shift(N)) - 1 for each N."""
    for w in windows:
        df[f"mom_{w}d"] = df["close"] / df["close"].shift(w) - 1
    return df


def compute_ema(df: pd.DataFrame, span_short=9, span_long=20) -> pd.DataFrame:
    """Add two EMAs on close."""
    df[f"ema_{span_short}"] = df["close"].ewm(span=span_short, adjust=False).mean()
    df[f"ema_{span_long}"] = df["close"].ewm(span=span_long, adjust=False).mean()
    return df


def compute_atr(df: pd.DataFrame, window=14) -> pd.DataFrame:
    """Average True Range over `window` days."""
    high_low = df["high"] - df["low"]
    high_prev = (df["high"] - df["close"].shift(1)).abs()
    low_prev = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([high_low, high_prev, low_prev], axis=1).max(axis=1)
    df[f"atr_{window}d"] = tr.rolling(window).mean()
    return df


def compute_rsi(df: pd.DataFrame, window=14) -> pd.DataFrame:
    """Classic 14‑day RSI."""
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()
    rs = avg_gain / avg_loss
    df[f"rsi_{window}d"] = 100 - (100 / (1 + rs))
    return df


def compute_macd(
    df: pd.DataFrame, span_short=12, span_long=26, span_signal=9
) -> pd.DataFrame:
    """MACD line, signal, and histogram."""
    ema_s = df["close"].ewm(span=span_short, adjust=False).mean()
    ema_l = df["close"].ewm(span=span_long, adjust=False).mean()
    df["macd_line"] = ema_s - ema_l
    df["macd_signal"] = df["macd_line"].ewm(span=span_signal, adjust=False).mean()
    df["macd_hist"] = df["macd_line"] - df["macd_signal"]
    return df


def compute_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract simple calendar features from datetime."""
    df["date"] = pd.to_datetime(df["datetime"])
    df["day_of_week"] = df["date"].dt.weekday
    df["month"] = df["date"].dt.month
    df["is_month_end"] = df["date"].dt.is_month_end.astype(int)
    return df
