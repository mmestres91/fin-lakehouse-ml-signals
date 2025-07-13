import io
from datetime import datetime, timedelta

import boto3
import yfinance as yf
from airflow.operators.python import PythonOperator

from airflow import DAG  # type: ignore[attr-defined]


def fetch_and_upload_parquet_to_s3():
    # Fetch SPY data
    df = yf.download("SPY", period="1d", interval="5m")

    # Convert DataFrame to Parquet in memory
    buffer = io.BytesIO()
    df.to_parquet(buffer, engine="pyarrow", index=True)
    buffer.seek(0)

    # Upload to S3
    s3 = boto3.client("s3")
    s3.upload_fileobj(
        buffer, "finlakehouse-raw-mmestres91", "ingestion/spy_intraday.parquet"
    )


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
