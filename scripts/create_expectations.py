# scripts/create_expectations.py  • GE 0.18.15
# flake8: noqa: E501
import polars as pl
import great_expectations as gx
from pathlib import Path

CURATED_SAMPLE = "s3://finlakehouse-curated-mmestres91/market/spy_transformed.parquet"

SUITE_NAME = "curated_market_suite"
DATASOURCE_NAME = "local_pandas"
ASSET_NAME = "spy_sample"


def main() -> None:
    # 1 ── Load data
    df = pl.read_parquet(CURATED_SAMPLE).to_pandas()

    # 2 ── Context & datasource
    context = gx.get_context()
    datasource = context.datasources.get(DATASOURCE_NAME) or context.sources.add_pandas(
        name=DATASOURCE_NAME
    )

    # ── Get existing asset or create if missing ───────────────────────────────
    try:
        asset = datasource.get_asset(ASSET_NAME)
    except gx.exceptions.DataContextError:  # asset not yet registered
        asset = datasource.add_dataframe_asset(name=ASSET_NAME)

    # 4 ── Ensure suite exists (overwrite allowed)
    context.add_expectation_suite(expectation_suite_name=SUITE_NAME)

    # 5 ── Build batch request & validator
    batch_request = asset.build_batch_request(dataframe=df)
    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=SUITE_NAME,
    )

    # 6 ── Expectations
    validator.expect_column_to_exist("datetime")
    validator.expect_column_values_to_not_be_null("datetime")
    validator.expect_column_values_to_be_unique("datetime")

    validator.expect_column_to_exist("close")
    validator.expect_column_values_to_not_be_null("close")
    validator.expect_column_values_to_be_between("close", min_value=0, strict_min=True)

    validator.expect_table_row_count_to_be_between(min_value=1, max_value=10_000)

    # 7 ── Save / overwrite suite
    validator.save_expectation_suite(discard_failed_expectations=False)

    suite_path = Path(context.root_directory) / "expectations" / f"{SUITE_NAME}.json"
    print(f"✅ Expectation suite saved → {suite_path}")


if __name__ == "__main__":
    main()
