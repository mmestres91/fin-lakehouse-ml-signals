# Use the official Apache Airflow image as base
FROM apache/airflow:2.8.1

# Install required Python packages
RUN pip install --no-cache-dir \
    yfinance \
    boto3 \
    pandas
