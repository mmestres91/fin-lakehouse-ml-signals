# dags/curated_market_dq_dag.py  ▸ Airflow 2.6+ (TaskFlow API)
# flake8: noqa: E501
from __future__ import annotations
from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.models import Variable

import great_expectations as gx

import polars as pl
import boto3
from pathlib import Path
import shutil
import subprocess


###############################################################################
#  DAG-level constants (edit as needed)
###############################################################################
DAG_ID = "curated_market_dq"
S3_PARQUET_TEMPLATE = (
    "s3://finlakehouse-curated-mmestres91/market/spy_transformed.parquet"
)
CHECKPOINT_NAME = "curated_market_ckpt"
# GE_PROJECT_ROOT = "/opt/airflow/gx"  # inside the container
DATA_DOCS_BUCKET = "finlakehouse-logs-mmestres91"  # S3 bucket for HTML
DATA_DOCS_PREFIX = "curated_market_ge"  # folder in that bucket
AWS_CONN_ID = "aws_default"  # Airflow Conn (if using S3Hook)


###############################################################################
#  DAG definition
###############################################################################
@dag(
    dag_id=DAG_ID,
    schedule="@daily",
    start_date=datetime(2025, 7, 15),
    catchup=False,
    default_args={
        "owner": "data-platform",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        # "email_on_failure": True,
        # "email": ["data-ops@example.com"],
    },
    tags=["dq", "great_expectations"],
)
def curated_market_dq():

    # ─────────────────────────────────────────────────────────────────────────
    # 1️⃣  Load Parquet -> pandas
    # ─────────────────────────────────────────────────────────────────────────
    @task
    def load_dataframe(path: str):
        """Fetch Parquet (local or S3) and return a pandas DF."""
        df = pl.read_parquet(path).to_pandas()
        return df  # XCom handles serialization

    # ─────────────────────────────────────────────────────────────────────────
    # 2️⃣  Run Great Expectations checkpoint
    # ─────────────────────────────────────────────────────────────────────────
    @task()
    def validate_dataframe(df, run_date: str):
        ctx = gx.get_context()

        datasource_name = "local_pandas"
        asset_name = "spy_sample"

        # 1️⃣  get the DataFrameAsset object that was registered by create_expectations.py
        asset = ctx.datasources[datasource_name].get_asset(asset_name)

        # 2️⃣  build a proper DataFrameBatchRequest
        batch_request = asset.build_batch_request(
            dataframe=df,  # inline dataframe
            # batch_identifiers={"run_date": run_date},   # any identifiers/tags you like
        )

        # 3️⃣  run the checkpoint
        result = ctx.run_checkpoint(
            checkpoint_name="curated_market_ckpt",
            batch_request=batch_request,
            run_name=run_date,
        )
        if not result["success"]:
            raise ValueError("❌ GE validation failed")

    # ─────────────────────────────────────────────────────────────────────────
    # 3️⃣  Ship HTML site up to S3 (optional but nice)
    # ─────────────────────────────────────────────────────────────────────────
    @task
    def publish_docs(local_site_path: str, run_date: str):
        """
        Sync generated Data Docs HTML to S3
        so analysts can browse results at
        https://{bucket}.s3.amazonaws.com/{prefix}/{run_date}/index.html
        """
        s3 = boto3.client("s3")
        dest_prefix = f"{DATA_DOCS_PREFIX}/{run_date}/"

        for html_file in Path(local_site_path).rglob("*"):
            if html_file.is_file():
                rel = html_file.relative_to(local_site_path)
                s3_key = f"{dest_prefix}{rel.as_posix()}"
                s3.upload_file(str(html_file), DATA_DOCS_BUCKET, s3_key)

        # clean up workspace
        shutil.rmtree(local_site_path)
        return f"s3://{DATA_DOCS_BUCKET}/{dest_prefix}index.html"

    # ─────────────────────────────────────────────────────────────────────────
    # 4️⃣  Wire the tasks
    # ─────────────────────────────────────────────────────────────────────────
    run_dt = "{{ ds }}"  # Airflow template: 2025-07-15
    parquet = S3_PARQUET_TEMPLATE  # could template path too

    df = load_dataframe(parquet)
    docs_dir = validate_dataframe(df, run_dt)
    docs_url = publish_docs(docs_dir, run_dt)


curated_market_dq_dag = curated_market_dq()
