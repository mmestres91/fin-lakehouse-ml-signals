# 1️⃣ Base image (already non-root-friendly)
FROM apache/airflow:2.8.1

# 2️⃣ Switch to airflow user
USER airflow

RUN pip install --no-cache-dir \
        yfinance \
        boto3 \
        pandas \
        polars \
        ta \
        great-expectations==0.18.15

# 3️⃣ Health-check for best-practice
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8080/health || exit 1


