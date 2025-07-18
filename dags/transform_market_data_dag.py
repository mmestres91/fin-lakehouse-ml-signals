# flake8: noqa: E501
from airflow import DAG  # type: ignore[attr-defined]
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import boto3
import ast
from typing import Union
import io
import polars as pl
import ta  # ta adds indicators using pandas; we’ll convert polars <-> pandas


def _flatten(col: Union[str, tuple]) -> str:
    """
    ('Close', 'SPY')           → 'close'
    "('Close', 'SPY')"         → 'close'
    'Datetime' / 'datetime'    → 'datetime'
    """
    # Case 1 ─ actual tuple
    if isinstance(col, tuple):
        return str(col[0]).lower()

    # Case 2 ─ stringified tuple "(... , ...)"
    if isinstance(col, str) and col.startswith("(") and col.endswith(")"):
        try:
            tup = ast.literal_eval(col)
            if isinstance(tup, tuple):
                return str(tup[0]).lower()
        except Exception:
            pass  # fall through if literal_eval fails

    # Fallback ─ plain string
    return col.lower()


def transform_yfinance_data():
    # 1. Read from S3
    s3 = boto3.client("s3")
    bucket = "finlakehouse-raw-mmestres91"
    key = "market_data/yfinance/SPY/year=2025/data.parquet"  # Adjust key if needed

    raw_obj = s3.get_object(Bucket=bucket, Key=key)
    df: pl.DataFrame = pl.read_parquet(raw_obj["Body"])

    # 2. FLATTEN MULTI-INDEX HEADER
    df = df.rename({c: _flatten(c) for c in df.columns})
    print("Flattened columns:", df.columns)

    # Optional cleanup
    df = df.drop_nulls()

    # 3. INDICATORS (needs pandas)
    pdf = df.to_pandas()

    close = pdf["close"]
    pdf["rsi"] = ta.momentum.RSIIndicator(close).rsi()
    pdf["ema_20"] = ta.trend.EMAIndicator(close, window=20).ema_indicator()

    # Back to Polars for smaller parquet
    df_final = pl.from_pandas(pdf)

    # 4. Write back to curated S3
    out_buffer = io.BytesIO()
    df_final.write_parquet(out_buffer)
    out_buffer.seek(0)

    s3.put_object(
        Bucket="finlakehouse-curated-mmestres91",
        Key="market/spy_transformed.parquet",
        Body=out_buffer,
    )


default_args = {
    "owner": "mark",
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "transform_market_data",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
) as dag:

    transform_task = PythonOperator(
        task_id="transform_market_data", python_callable=transform_yfinance_data
    )
