# scripts/create_checkpoint.py  • GE 0.18.15
# flake8: noqa: E501
import polars as pl
import great_expectations as gx
from pathlib import Path

DATASOURCE_NAME = "local_pandas"
ASSET_NAME = "spy_sample"
SUITE_NAME = "curated_market_suite"
CHECKPOINT_NAME = "curated_market_ckpt"


def main() -> None:
    ctx = gx.get_context()

    # ── Datasource ──
    ds = ctx.datasources.get(DATASOURCE_NAME) or ctx.sources.add_pandas(
        name=DATASOURCE_NAME
    )

    # ── Asset ──
    try:
        asset = ds.get_asset(ASSET_NAME)
    except gx.exceptions.DataContextError:
        asset = ds.add_dataframe_asset(name=ASSET_NAME)

    # ── Placeholder batch_request ──
    placeholder_df = pl.DataFrame({"_init": [0]}).to_pandas()
    batch_request = asset.build_batch_request(dataframe=placeholder_df)

    # ── Register / update checkpoint ──
    ctx.add_or_update_checkpoint(
        name=CHECKPOINT_NAME,
        batch_request=batch_request,
        expectation_suite_name=SUITE_NAME,
        action_list=[
            {  # stores validation JSON in GX store
                "name": "store_validation_result",
                "action": {"class_name": "StoreValidationResultAction"},
            },
            {  # builds/updates Data Docs HTML (optional; comment out if not used)
                "name": "update_data_docs",
                "action": {"class_name": "UpdateDataDocsAction"},
            },
        ],
    )

    ckpt_path = Path(ctx.root_directory) / "checkpoints" / f"{CHECKPOINT_NAME}.yml"
    print(f"✅ Checkpoint saved → {ckpt_path}")


if __name__ == "__main__":
    main()
