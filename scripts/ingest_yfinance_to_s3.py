import io
from datetime import datetime

import boto3
import yfinance as yf


def fetch_and_upload(symbol: str, bucket: str, key_prefix: str):
    print(f"Downloading {symbol} data...")
    df = yf.download(symbol, period="1y", interval="1d")
    df.reset_index(inplace=True)

    buffer = io.BytesIO()
    df.to_parquet(buffer, engine="pyarrow", index=False)
    buffer.seek(0)

    s3 = boto3.client("s3")
    key = f"{key_prefix}/{symbol}/year={datetime.now().year}/data.parquet"

    print(f"Uploading to s3://{bucket}/{key} ...")
    s3.upload_fileobj(buffer, bucket, key)
    print("✅ Upload complete.")


if __name__ == "__main__":
    fetch_and_upload(
        symbol="SPY",
        bucket="finlakehouse-raw-mmestres91",
        key_prefix="market_data/yfinance",
    )
