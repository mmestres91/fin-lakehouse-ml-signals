# scripts/validate_curated.py  • final form
import argparse
import polars as pl
import great_expectations as gx
from datetime import date

DS = "local_pandas"
ASSET = "spy_sample"
CKPT = "curated_market_ckpt"


def main(path: str, run_date: str) -> None:
    df = pl.read_parquet(path).to_pandas()

    ctx = gx.get_context()
    asset = ctx.datasources[DS].get_asset(ASSET)
    batch_request = asset.build_batch_request(dataframe=df)

    result = ctx.run_checkpoint(
        checkpoint_name=CKPT,
        batch_request=batch_request,
        run_name=run_date,  # optional tag
    )

    if not result["success"]:
        raise SystemExit("❌ DQ validation FAILED")
    print("✅ DQ validation PASSED")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    ap.add_argument("--run-date", default=str(date.today()))
    args = ap.parse_args()
    main(args.path, args.run_date)
