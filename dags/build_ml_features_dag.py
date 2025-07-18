# dags/build_ml_features_dag.py
# flake8: noqa: E501

from airflow.decorators import dag, task
from datetime import datetime, timedelta
import pandas as pd

from features.features_v1 import (
    compute_momentum,
    compute_ema,
    compute_atr,
    compute_rsi,
    compute_macd,
    compute_time_features,
)

import great_expectations as gx

DAG_ID = "build_ml_features"
CURATED_PATH = "s3://finlakehouse-curated-mmestres91/market/spy_transformed.parquet"
FEATURES_PATH = (
    "s3://finlakehouse-features-mmestres91/market/spy/{run_date}/features.parquet"
)
CHECKPOINT_NAME = "features_ckpt"  # define this in your GX checkpoints/


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
    tags=["features", "ml"],
)
def build_ml_features():

    @task
    def extract_curated(run_date: str) -> pd.DataFrame:
        df = pd.read_parquet(CURATED_PATH)
        return df

    @task
    def transform_features(df: pd.DataFrame) -> pd.DataFrame:
        df = compute_momentum(df)
        df = compute_ema(df)
        df = compute_atr(df)
        df = compute_rsi(df)
        df = compute_macd(df)
        df = compute_time_features(df)
        return df

    @task
    def validate_features(df: pd.DataFrame, run_date: str):
        ctx = gx.get_context()  # relies on GREAT_EXPECTATIONS_HOME
        datasource_name = "local_pandas"
        asset_name = "spy_sample"

        # 1️⃣  get the DataFrameAsset object that was registered by create_expectations.py
        asset = ctx.datasources[datasource_name].get_asset(asset_name)

        batch_request = asset.build_batch_request(
            dataframe=df,
        )
        # get or create a validator against your features expectation suite
        validator = ctx.get_validator(
            batch_request=batch_request,
            expectation_suite_name="features_suite",
        )

        # DQ rules
        # 1) no nulls in momentum & EMA
        for col in df.filter(like="mom_").columns:
            validator.expect_column_values_to_not_be_null(col)
        for col in ["ema_9", "ema_20"]:
            validator.expect_column_values_to_not_be_null(col)
        # 2) ATR > 0
        validator.expect_column_values_to_be_between(
            "atr_14d", min_value=0, strict_min=True
        )
        # 3) RSI in [0,100]
        validator.expect_column_values_to_be_between(
            "rsi_14d", min_value=0, max_value=100
        )
        # 4) MACD line exists
        validator.expect_column_values_to_not_be_null("macd_line")
        # 5) time features not null
        validator.expect_column_values_to_not_be_null("day_of_week")

        result = validator.validate()
        ctx.build_data_docs()  # push HTML to your data_docs site
        if not result["success"]:
            raise ValueError("❌ Feature DQ checks failed")

    @task
    def load_features(df: pd.DataFrame, run_date: str) -> str:
        out = FEATURES_PATH.format(run_date=run_date)
        df.to_parquet(out, index=False)
        return out

    run_dt = "{{ ds }}"
    curated = extract_curated(run_dt)
    features = transform_features(curated)
    valid = validate_features(features, run_dt)
    path = load_features(features, run_dt)

    valid >> path


build_ml_features_dag = build_ml_features()
