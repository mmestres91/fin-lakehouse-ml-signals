# dags/build_ml_features_dag.py
# flake8: noqa: E501

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import tempfile

import boto3
import polars as pl
from airflow.decorators import dag, task

# your feature‑calc helpers (now accept/return Polars DFs)
from features.features_v1 import (
    compute_momentum,
    compute_ema,
    compute_atr,
    compute_rsi,
    compute_macd,
    compute_time_features,
)

import great_expectations as gx

# --------------------------------------------------------------------------- #
DAG_ID = "build_ml_features"
S3 = boto3.client("s3")
CURATED_S3 = "finlakehouse-curated-mmestres91"
CURATED_KEY = "market/spy_transformed.parquet"
FEATURES_S3_TMPL = (
    "s3://finlakehouse-features-mmestres91/market/spy/{run_date}/features.parquet"
)
CHECKPOINT_NAME = "feature_checkpoint"  # gx/checkpoints/feature_checkpoint.yml
AWS_PROFILE = None  # or use instance‑/task‑role creds
# --------------------------------------------------------------------------- #


@dag(
    dag_id=DAG_ID,
    schedule="@daily",
    start_date=datetime(2025, 7, 1),
    catchup=False,
    default_args={
        "owner": "data-platform",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["features", "ml", "great_expectations"],
)
def build_ml_features():
    session = boto3.Session(profile_name=AWS_PROFILE)  # re‑usable for every task

    # ─────────────────────────────────────────────────────────────────────────
    # 1️⃣  Extract curated Parquet from S3  → Polars DF
    # ─────────────────────────────────────────────────────────────────────────
    @task
    def extract_curated(run_date: str) -> str:  # ⬅ returns PATH
        # 1️⃣ download to tmp
        tmp = Path(tempfile.gettempdir(), "curated.parquet")
        S3.download_file(CURATED_S3, CURATED_KEY, str(tmp))
        return str(tmp)

    # ─────────────────────────────────────────────────────────────────────────
    # 2️⃣  Transform → compute v1 features (Polars in / Polars out)
    # ─────────────────────────────────────────────────────────────────────────
    @task
    def transform_features(path: str) -> str:
        df = pl.read_parquet(path)
        df = (
            df.pipe(compute_ema)
            .pipe(compute_momentum)
            .pipe(compute_atr)
            .pipe(compute_rsi)
            .pipe(compute_macd)
            .pipe(compute_time_features)
        )
        out = Path(tempfile.gettempdir(), "features.parquet")
        df.write_parquet(out)
        return str(out)

    # ─────────────────────────────────────────────────────────────────────────
    # 3️⃣  Validate with Great Expectations (convert Polars → Pandas for GX)
    # ─────────────────────────────────────────────────────────────────────────
    @task
    def validate_features(feature_path: str, run_date: str):
        ctx = gx.get_context()  # GREAT_EXPECTATIONS_HOME already set in image
        pandas_df = pl.read_parquet(feature_path).to_pandas()
        asset = ctx.datasources["local_pandas"].get_asset("features_v1")
        batch_request = asset.build_batch_request(dataframe=pandas_df)

        result = ctx.run_checkpoint(
            checkpoint_name="feature_checkpoint",
            batch_request=batch_request,
            run_name=run_date,
        )
        # ctx.build_data_docs(site_name="local_site")

        if not result["success"]:
            raise ValueError("❌ Feature DQ checks failed")

    # ─────────────────────────────────────────────────────────────────────────
    # 4️⃣  Load to S3 as Parquet (Polars write + boto3 upload)
    # ─────────────────────────────────────────────────────────────────────────
    @task
    def load_features(feature_path: str, run_date: str) -> str:
        s3_key = f"market/spy/{run_date}/features.parquet"
        S3.upload_file(feature_path, "finlakehouse-features-mmestres91", s3_key)
        return f"s3://finlakehouse-features-mmestres91/{s3_key}"

    # ─────────────────────────────────────────────────────────────────────────
    # 5️⃣  Task wiring
    # ─────────────────────────────────────────────────────────────────────────
    run_dt = "{{ ds }}"
    curated_path = extract_curated(run_dt)
    features_path = transform_features(curated_path)
    validate_features(features_path, run_dt)
    load_features(features_path, run_dt)


ml_feature_dag = build_ml_features()
