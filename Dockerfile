##############################
# 1️⃣  Base image
##############################
FROM apache/airflow:2.8.1-python3.8

##############################
# 2️⃣  Runtime constraints
##############################
ARG AIRFLOW_VERSION=2.8.1
ARG PYTHON_VERSION=3.8
ARG CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"


##############################
# 4️⃣  Install extra packages
##############################
# Everything is installed in *one* shot under the Airflow constraints,
# so redis is pinned to 4.x automatically.
RUN pip install --no-cache-dir --constraint ${CONSTRAINT_URL} \
        yfinance \
        boto3 \
        pandas \
        polars \
        ta \
        "great-expectations==0.18.15"

##############################
# 5️⃣  Copy project code incl. GE
##############################
COPY --chown=airflow:0 gx /opt/airflow/gx
COPY --chown=airflow:0 dags /opt/airflow/dags
COPY --chown=airflow:0 scripts /opt/airflow/scripts
ENV PYTHONPATH=/opt/airflow \
    GREAT_EXPECTATIONS_HOME=/opt/airflow/gx \
    AWS_DEFAULT_REGION=us-east-1   
COPY ./features /opt/airflow/features
ENV PYTHONPATH="/opt/airflow:${PYTHONPATH}"

##############################
# Switch to airflow user
##############################
USER airflow

##############################
# 6️⃣  Health‑check
##############################
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8080/health || exit 1
