# flake8: noqa: E501
import io
from datetime import datetime, timedelta

import boto3
import logging
import polars as pl
import yfinance as yf
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowFailException

from airflow import DAG  # type: ignore[attr-defined]


def fetch_and_upload_parquet_to_s3(**context):
    symbol = "SPY"
    max_retries = 5

    for attempt in range(1, max_retries + 1):
        try:
            logging.info("Fetching %s (attempt %s/%s)", symbol, attempt, max_retries)
            df = yf.download(
                tickers=symbol,
                threads=False,  # avoids hidden thread errors
                progress=False,
                auto_adjust=True,
                interval="1d",
                period="max",
            )

            if df.empty:
                raise ValueError("Yahoo returned 0 rows")

            # ---- write Parquet in-memory ----
            pl_df = pl.from_pandas(df.reset_index())
            buf = io.BytesIO()
            pl_df.write_parquet(buf, compression="snappy")
            buf.seek(0)

            s3 = boto3.client("s3")
            key = f"raw/{symbol.lower()}_{context['ds']}.parquet"
            s3.upload_fileobj(buf, "finlakehouse-raw-mmestres91", key)
            logging.info(
                "✅ uploaded %s rows → s3://finlakehouse-raw…/%s", len(df), key
            )
            return key  # exit ⬅︎ success

        except Exception as e:
            # Anything else is unrecoverable for this run
            raise AirflowFailException(f"Ingest failed: {e}") from e

    # exhausted retries
    raise AirflowFailException("Exceeded retries – still rate-limited")


default_args = {
    "owner": "mark",
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "spy_yfinance_parquet_ingestion",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
) as dag:

    fetch_upload_task = PythonOperator(
        task_id="fetch_and_upload_parquet_to_s3",
        python_callable=fetch_and_upload_parquet_to_s3,
    )
