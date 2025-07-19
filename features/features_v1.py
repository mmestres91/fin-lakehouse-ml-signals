# features/features_v1.py
# flake8: noqa: E501

import polars as pl


# ──────────────────────────────────────────────────────────────────────
# Momentum
# ──────────────────────────────────────────────────────────────────────
def compute_momentum(df: pl.DataFrame, windows=(5, 10, 20)) -> pl.DataFrame:
    """
    Add mom_{N}d = (close / close.shift(N)) - 1  for each N in `windows`.
    """
    return df.with_columns(
        [
            (pl.col("close") / pl.col("close").shift(w) - 1).alias(f"mom_{w}d")
            for w in windows
        ]
    )


# ──────────────────────────────────────────────────────────────────────
# EMA
# ──────────────────────────────────────────────────────────────────────
def compute_ema(
    df: pl.DataFrame, span_short: int = 9, span_long: int = 20
) -> pl.DataFrame:
    """
    Add two Exponential Moving Averages on close: ema_{span_short}, ema_{span_long}
    """
    return df.with_columns(
        pl.col("close").ewm_mean(alpha=2 / (span_short + 1)).alias(f"ema_{span_short}")
    ).with_columns(
        pl.col("close").ewm_mean(alpha=2 / (span_long + 1)).alias(f"ema_{span_long}")
    )


# ──────────────────────────────────────────────────────────────────────
# ATR
# ──────────────────────────────────────────────────────────────────────
def compute_atr(df: pl.DataFrame, window: int = 14) -> pl.DataFrame:
    """
    Average True Range over `window` days (in Polars).

    Adds a new column `atr_{window}d`.
    """
    hl = (pl.col("high") - pl.col("low")).alias("hl")  # high‑low
    hp = (pl.col("high") - pl.col("close").shift(1)).abs().alias("hp")  # high‑prevClose
    lp = (pl.col("low") - pl.col("close").shift(1)).abs().alias("lp")  # low‑prevClose

    return (
        df.with_columns(  # 1️⃣  True‑range per row
            pl.max_horizontal(hl, hp, lp).alias("tr")
        )
        .with_columns(  # 2️⃣  Rolling mean of TR
            pl.col("tr").rolling_mean(window).alias(f"atr_{window}d")
        )
        .drop("tr")  # optional: clean helper col
    )


# ──────────────────────────────────────────────────────────────────────
# RSI
# ──────────────────────────────────────────────────────────────────────
def compute_rsi(df: pl.DataFrame, window: int = 14) -> pl.DataFrame:
    """
    Add column  rsi_<window>d  (e.g. rsi_14d) to *df*.
    Assumes a 'close' column of float dtype.
    """

    # 1️⃣  Δ close
    delta_expr = pl.col("close").diff()

    # 2️⃣  positive & negative deltas
    gain_expr = pl.when(delta_expr > 0).then(delta_expr).otherwise(0.0)
    loss_expr = pl.when(delta_expr < 0).then(-delta_expr).otherwise(0.0)

    # 3️⃣  rolling averages (simple mean ‑ Wilder’s smoothing)
    avg_gain = gain_expr.rolling_mean(window)
    avg_loss = loss_expr.rolling_mean(window)

    # 4️⃣  RSI formula
    rsi_expr = 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)))

    return (
        df.with_columns(
            [
                rsi_expr.alias(f"rsi_{window}d"),
            ]
        )
        # .drop([...])   # no temp columns were materialised, so nothing to drop
    )


# ──────────────────────────────────────────────────────────────────────
# MACD
# ──────────────────────────────────────────────────────────────────────
def compute_macd(
    df: pl.DataFrame,
    span_short: int = 12,
    span_long: int = 26,
    span_signal: int = 9,
) -> pl.DataFrame:
    """
    Add columns  macd_line, macd_signal, macd_hist  to *df*.

    * EMA smoothing uses the classic alpha = 2 / (N + 1) formulation.
    * No temporary Pandas objects – everything stays in Polars expressions.
    """
    alpha_s = 2 / (span_short + 1)
    alpha_l = 2 / (span_long + 1)
    alpha_sig = 2 / (span_signal + 1)

    return (
        df.with_columns(  # step‑wise so we can reference newly created cols
            [
                pl.col("close").ewm_mean(alpha=alpha_s).alias("_ema_short"),
                pl.col("close").ewm_mean(alpha=alpha_l).alias("_ema_long"),
            ]
        )
        .with_columns((pl.col("_ema_short") - pl.col("_ema_long")).alias("macd_line"))
        .with_columns(
            # signal line is EMA of the just‑computed macd_line
            pl.col("macd_line")
            .ewm_mean(alpha=alpha_sig)
            .alias("macd_signal")
        )
        .with_columns((pl.col("macd_line") - pl.col("macd_signal")).alias("macd_hist"))
        .drop(["_ema_short", "_ema_long"])  # clean‑up helpers
    )


# ──────────────────────────────────────────────────────────────────────
# Time‑based features
# ──────────────────────────────────────────────────────────────────────
def compute_time_features(df: pl.DataFrame) -> pl.DataFrame:
    """
    Add calendar features:

    • day_of_week  (0=Mon … 6=Sun)
    • month        (1‑12)
    • is_month_end (1 if last calendar day, else 0)

    Assumes a `datetime` column of dtype *Datetime*.
    """
    if "date" not in df.columns:
        df = df.with_columns(pl.col("datetime").cast(pl.Date).alias("date"))

    return df.sort("date").with_columns(  # make sure rows are in chronological order
        [
            pl.col("date").dt.weekday().alias("day_of_week"),
            pl.col("date").dt.month().alias("month"),
            # month‑end when month ≠ month of next row
            (pl.col("date").dt.month() != pl.col("date").shift(-1).dt.month())
            .fill_null(True)  # the very last row is month‑end
            .cast(pl.Int8)
            .alias("is_month_end"),
        ]
    )
