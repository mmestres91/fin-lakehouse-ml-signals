# tests/test_features_v1_duckdb.py
# flake8: noqa: E501
# Run with:  poetry run pytest -q tests/test_features_v1_duckdb.py

import polars as pl
import duckdb
import pytest
from datetime import date, timedelta

# --- bring in your feature builders ---------------------------------
from features.features_v1 import (
    compute_momentum,
    compute_ema,
    compute_atr,
    compute_rsi,
    compute_macd,
    compute_time_features,
)


# ════════════════════════════════════════════════════════════════════
# Synthetic raw‑price fixture
# ════════════════════════════════════════════════════════════════════
@pytest.fixture(scope="session")
def feature_df() -> pl.DataFrame:
    """
    Build a 1‑year daily OHLCV DataFrame and run v1 feature pipeline.
    """
    n = 252  # ~1 trading year
    start = date(2024, 1, 2)

    dates = [start + timedelta(days=i) for i in range(n)]
    close = [100 + i * 0.5 for i in range(n)]  # simple up‑trend
    high = [c * 1.01 for c in close]
    low = [c * 0.99 for c in close]
    open_ = close  # open==close for dummy
    volume = [1_000_000 + i * 1000 for i in range(n)]  # monotonically increasing

    df = pl.DataFrame(
        {
            "datetime": dates,
            "close": close,
            "high": high,
            "low": low,
            "open": open_,
            "volume": volume,
        }
    )

    # --- compute all v1 features (Polars versions) ------------------
    df = (
        df.pipe(compute_momentum)
        .pipe(compute_ema)
        .pipe(compute_atr)
        .pipe(compute_rsi)
        .pipe(compute_macd)
        .pipe(compute_time_features)
    )
    return df


@pytest.fixture(scope="session")
def lf(feature_df) -> pl.LazyFrame:  # noqa: D401
    """Expose the synthetic feature table as LazyFrame for expression tests."""
    return feature_df.lazy()


@pytest.fixture(scope="session")
def con(feature_df):
    """Register the feature table as DuckDB view named 'features'."""
    con = duckdb.connect(database=":memory:", read_only=False)
    con.register("features", feature_df.to_pandas())  # DuckDB likes pandas/Arrow
    return con


# ════════════════════════════════════════════════════════════════════
# Polars‑native tests
# ════════════════════════════════════════════════════════════════════
# tests/test_features_v1_duckdb.py
def test_no_nulls_in_momentum(lf: pl.LazyFrame):
    mom_cols = [c for c in lf.columns if c.startswith("mom_")]
    if not mom_cols:
        pytest.skip("No mom_* columns present")

    # work out the largest window (e.g. 20 from mom_20d)
    max_lag = max(int(c.split("_")[1][:-1]) for c in mom_cols)

    # drop the first `max_lag` rows, *then* assert no nulls
    nulls = (
        lf.slice(max_lag)  # skip look‑back rows
        .select([pl.col(c).is_null().any().alias(c) for c in mom_cols])
        .collect()
        .to_dict(as_series=False)
    )
    nulls = {k: v[0] for k, v in nulls.items()}
    assert not any(nulls.values()), f"Momentum cols contain nulls: {nulls}"


def test_atr_positive(lf):
    assert (
        lf.filter(pl.col("atr_14d") <= 0).select(pl.count()).collect()[0, 0] == 0
    ), "Found non‑positive ATR values"


def test_rsi_bounds(lf):
    out_of_range = (
        lf.filter((pl.col("rsi_14d") < 0) | (pl.col("rsi_14d") > 100))
        .select(pl.count())
        .collect()[0, 0]
    )
    assert out_of_range == 0, "RSI out of [0, 100] bounds"


# ════════════════════════════════════════════════════════════════════
# DuckDB SQL style (optional)
# ════════════════════════════════════════════════════════════════════
def test_row_count(con):
    rows = con.execute("SELECT COUNT(*) FROM features").fetchone()[0]
    assert rows == 252, f"Unexpected row count: {rows}"
