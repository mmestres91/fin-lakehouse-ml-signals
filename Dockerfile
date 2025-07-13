# Use the official Apache Airflow image as base
FROM apache/airflow:2.8.1

# Install required Python packages
RUN pip install --no-cache-dir \
    yfinance \
    boto3 \
    pandas

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8080/health || exit 1

# Create a non-root user and switch to it
RUN useradd --create-home --shell /bin/bash airflowuser
USER airflowuser