# tests/test_features_v1_duckdb.py
# flake8: noqa: E501

import pytest
import pandas as pd
import duckdb
from features.features_v1 import (
    compute_time_features,
    compute_momentum,
    compute_ema,
    compute_atr,
    compute_rsi,
    compute_macd,
)


@pytest.fixture
def sample_df():
    # 10 days of made‑up OHLC data
    dates = pd.date_range("2025-01-01", periods=10, freq="D")
    data = {
        "datetime": dates,
        "open": [100 + i for i in range(10)],
        "high": [101 + i for i in range(10)],
        "low": [99 + i for i in range(10)],
        "close": [100 + i for i in range(10)],
    }
    return pd.DataFrame(data)


@pytest.fixture
def transformed_df(sample_df):
    df = sample_df.copy()
    df = compute_time_features(df)
    df = compute_momentum(df, windows=[3, 5])
    df = compute_ema(df, span_short=3, span_long=5)
    df = compute_atr(df, window=3)
    df = compute_rsi(df, window=3)
    df = compute_macd(df, span_short=3, span_long=5, span_signal=3)
    return df


def test_row_count(transformed_df):
    # should preserve number of rows
    con = duckdb.connect()
    con.register("df", transformed_df)
    n = con.execute("SELECT count(*) FROM df").fetchone()[0]
    assert n == 10


def test_time_features_not_null(transformed_df):
    con = duckdb.connect()
    con.register("df", transformed_df)
    # day_of_week and month should never be null
    res = con.execute(
        """
        SELECT count(*)
        FROM df
        WHERE day_of_week IS NULL OR month IS NULL
    """
    ).fetchone()[0]
    assert res == 0


def test_momentum_initial_nulls(transformed_df):
    con = duckdb.connect()
    con.register("df", transformed_df)
    # for mom_3d, first 3 rows should be null
    nulls = con.execute("SELECT count(*) FROM df WHERE mom_3d IS NULL").fetchone()[0]
    assert nulls == 3


def test_atr_positive(transformed_df):
    con = duckdb.connect()
    con.register("df", transformed_df)
    # ATR should be > 0 for rows after window
    count_bad = con.execute(
        """
      SELECT count(*)
      FROM df
      WHERE atr_3d <= 0 AND atr_3d IS NOT NULL
    """
    ).fetchone()[0]
    assert count_bad == 0


def test_rsi_bounds(transformed_df):
    con = duckdb.connect()
    con.register("df", transformed_df)
    # RSI should be between 0 and 100, ignoring nulls
    count_bad = con.execute(
        """
      SELECT count(*)
      FROM df
      WHERE (rsi_3d < 0 OR rsi_3d > 100)
    """
    ).fetchone()[0]
    assert count_bad == 0


def test_macd_components_present(transformed_df):
    con = duckdb.connect()
    con.register("df", transformed_df)
    # macd_line, macd_signal, macd_hist should exist (not all-null)
    for col in ("macd_line", "macd_signal", "macd_hist"):
        total_nulls = con.execute(
            f"""
          SELECT count(*) FROM df WHERE {col} IS NULL
        """
        ).fetchone()[0]
        assert total_nulls < 10  # at least some non‑nulls
