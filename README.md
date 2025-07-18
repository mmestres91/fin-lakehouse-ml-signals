# fin-lakehouse-ml-signals

[![CI](https://github.com/mmestres91/fin-lakehouse-ml-signals/actions/workflows/ci.yml/badge.svg)](https://github.com/mmestres91/fin-lakehouse-ml-signals/actions/workflows/ci.yml)

A reproducible data‑quality and ML‑feature pipeline for equities‑market signals built on:

* **Python 3.11** (managed by \[Poetry])
* **Polars → Pandas** for fast columnar transforms
* **Great Expectations 0.18** (Fluent API) for data‑quality rules
* **Apache Airflow 2.6+** for daily orchestration
* **Terraform ≥ 1.8** (+ AWS provider 5.x) to provision encrypted S3 buckets, logging targets, and KMS keys
* **AWS S3** as storage for raw, curated, and feature data

---

## 🚀 Completed work

1. **Raw data ingestion**
   - `spy_yfinance_parquet_ingestion` DAG: pulls SPY prices (via yfinance) and writes Parquet to the **raw S3 bucket**
2. **Data transformation**
   - `transform_market_data_dag`: Polars transforms raw Parquet → curated schema, outputs to **curated S3 bucket**
3. **Data-quality checks**
   - Great Expectations Fluent config in `gx/`
   - `create_expectations.py` + `create_checkpoint.py` helpers
   - `curated_market_dq_dag`: daily @00:00 UTC, runs checkpoint **curated\_market\_ckpt**, syncs HTML Data Docs to S3
   - Current rules: `datetime` exists/not-null/unique; `close` exists/not-null/>0; row count 1–10 000
4. **Infrastructure as code**
   - Terraform modules under `infra/` for S3 buckets (raw, curated, features, logs) and KMS keys
   - CI hook (`.github/workflows/precommit.yml`) enforces `terraform fmt` and linting
5. **Local & CI validation**
   - `scripts/validate_curated.py` for CLI/CI check against any Parquet path
   - Pre-commit & GitHub Actions integrate linting, type checks, and DQ validation on PRs
6. **Feature engineering & testing**
   - `features/features_v1.py`: calculates core signals (momentum variants, EMA 9/20, ATR, RSI, MACD, time features)
   - `tests/test_features_v1_duckdb.py`: DuckDB-based PyTest suite to validate feature outputs
   - `poetry run pytest` runs feature tests alongside other CI checks

---

## Repository layout

```text
fin-lakehouse-ml-signals/
├── dags/                         # Airflow TaskFlow DAGs
│   ├── spy_yfinance_parquet_ingestion.py  # raw ingest to S3
│   ├── transform_market_data_dag.py       # Polars transform → curated Parquet
│   └── curated_market_dq_dag.py           # Great Expectations validation
├── features/                     # Feature engineering code
│   └── features_v1.py            # initial feature calculations (momentum, ATR, RSI, MACD, time features)
├── infra/                        # Terraform modules & configs
│   ├── main.tf                   # root module (buckets, KMS)
│   ├── variables.tf              # shared inputs
│   ├── terraform.tfvars.example  # sample values
│   └── modules/
│       └── s3_bucket/            # reusable S3 + logging + encryption sub-module
├── gx/                           # Great Expectations project
│   ├── great_expectations.yml
│   ├── expectations/
│   └── checkpoints/
├── scripts/                      # one-off helpers & CLI
│   ├── create_expectations.py
│   ├── create_checkpoint.py
│   └── validate_curated.py
├── tests/                        # pytest tests (DuckDB & feature checks)
│   └── test_features_v1_duckdb.py
├── .github/workflows/            # CI pipelines
├── pyproject.toml                # Poetry deps + config
└── README.md                     # this file
```

---

## Architecture overview

```mermaid
flowchart LR
    %% === Left: Current ===
    subgraph Current["`**Current**`"]
        direction TB
        A[fa:fa-cloud-download-alt<br/>Vendor API]
        B@{ shape: cyl, label: "Raw S3 Bucket" }
        C@{ shape: cyl, label: "Curated S3 Bucket" }
        D@{ shape: doc, label: "Data Docs\ns3://ge-docs" }
    end

    %% === Right: Future ===
    subgraph Future["`**Future**`"]
        direction TB
        E@{ shape: lin-rect, label: "`Feature Build DAG`\n(`build_ml_features`)" }
        F@{ shape: cyl, label: "Feature Store" }
        G@{ shape: lin-rect, label: "`Train ML Models DAG`\n(`train_ml_models`)" }
        H@{ shape: docs, label: "Model Artifacts\nS3 / MLflow" }
        I@{ icon: "fa:rocket", form: "circle", label: "Prediction API\nFastAPI + Lambda" }
        J([BI / Dashboarding])
    end

    %% === Data and Process Flows ===
    A -- "raw_market_ingest_dag" --> B
    B -- "transform_market_data_dag" --> C
    C -- "curated_market_dq_dag\n(Great Expectations)" --> D
    C ==> E
    E -- "Partitioned Parquet\nor Feast/DuckDB" --> F
    F ==> G
    G --> H
    H --> I
    C --> J

    %% === Styling and Links ===
    style Future fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2.5px
    style Current fill:#e3f2fd,stroke:#1565c0,stroke-width:2.5px

    classDef dag fill:#fffde7,stroke:#fbc02d,stroke-width:1.5px
    class E,G dag

    classDef model fill:#f1f8e9,stroke:#388e3c,stroke-width:1.5px
    class H model

    classDef store fill:#ede7f6,stroke:#8e24aa,stroke-width:1.5px
    class F store

    %% Invisible link to keep ordering: Current left, Future right
    Current ~~~ Future

    %% Tooltips (examples)
    click B "Raw S3 landing zone" "This is the raw S3 bucket for initial ingests"
    click C "Curated data S3" "Validated/transformed data"
    click D "GE Docs" "Great Expectations output docs stored in S3"
    click F "Feature Store" "Storage for ML-ready features"
    click H "Model Artifacts" "Trained model versions, stored in S3/MLflow"
    click I "Prediction API" "Real-time predictions via FastAPI & Lambda"
```

---

## Quick‑start (local)

```bash
# clone & install
git clone git@github.com:mmestres91/fin-lakehouse-ml-signals.git
cd fin-lakehouse-ml-signals
poetry install

# provision infra (raw/curated/features/log buckets + KMS)
cd infra
terraform init && terraform apply
cd ..

# build or update GE artifacts
eventuate=2025-07-17
poetry run python scripts/create_expectations.py
poetry run python scripts/create_checkpoint.py

# run validation locally
echo "2025-07-17" | xargs -I{} poetry run python scripts/validate_curated.py --path s3://finlakehouse-curated-mmestres91/market/spy_transformed.parquet --run_date {}

# run feature tests
poetry run pytest
```

If expectations fail the script exits non‑zero, making it CI‑friendly.

---

## Airflow integration

1. **`raw_market_ingest_dag.py`**
   *Hourly* (configurable) – pulls fresh raw market data from the vendor API and lands it in the **raw S3 bucket** (`s3://finlakehouse-raw-…`).

2. **`transform_market_data_dag.py`**
   *Triggered after ingest completes* – reads raw Parquet, executes Polars transformations, and writes curated output to `s3://finlakehouse-curated-mmestres91/market/`, partitioned by run date.

3. **`curated_market_dq_dag.py`**
   *Daily @ 00:00 UTC* – validates the latest curated Parquet with Great Expectations and syncs **HTML Data Docs** to `s3://finlakehouse-ge-docs/curated_market/<run_date>/`.

4. **Failure behaviour**
   Any task that encounters schema/API errors or failed expectations marks its DAG run **failed**, cascading to dependent DAGs.

5. **Local dev**

```bash
astro dev start                  # or docker compose up airflow-init
# manually trigger ingest → transform → dq
docker exec <scheduler> airflow dags trigger raw_market_ingest_dag
```

---

## Continuous‑integration hooks

| Stage                      | Check                                                              |
| -------------------------- | ------------------------------------------------------------------ |
| **pre‑commit**             | `black`, `flake8`, `terraform_fmt`, etc.                           |
| **GitHub Actions (TBD)**   | `scripts/validate_curated.py` against a sample data file.          |
| **Prod DAG trigger (TBD)** | Workflow that calls the Airflow REST API after a successful merge. |

---

## Current data‑quality rules

| Column     | Expectation                        |
| ---------- | ---------------------------------- |
| `datetime` | exists, **not‑null**, **unique**   |
| `close`    | exists, not‑null, **> 0**          |
| **Table**  | row‑count between `1` and `10 000` |

---

## 🔮 Future Epic: Feature Store & ML Signal Engineering (TBD)

Goal – create reusable features from the curated dataset for ML models.

* **Extract key features**: price momentum, volatility regime, news sentiment (if applicable).
* **Store features** in Parquet (S3) *or* optionally via **Feast** or **DuckDB**.
* **Airflow DAG**: `build_ml_features` will compute & publish features.
* **Versioning strategy** – daily snapshot partitioning (`yyyy‑mm‑dd/`).

---

## 🧠 Future Epic: ML Training + Evaluation Pipelines (TBD)

Goal – automate model training on the engineered features.

* **Airflow DAG**: `train_ml_models`

  * Pulls feature data.
  * Trains XGBoost, LSTM, or other models.
  * Logs metrics & stores the model artifact.
* **Model registry** – store artifacts in S3 or **MLflow**.
* **Metric logging** – Weights & Biases integration or plain CSV.

---

## ⚡ Optional Epics (TBD)

### 🔗 Integration & API access

* Expose real‑time predictions via FastAPI + AWS Lambda or ECS Fargate.
* IAM/token‑based security.

### 📊 Dashboarding

* Connect curated S3 data to a BI tool (Superset, Metabase, etc.) for exploratory analytics.

---

## Contributing

1. **Fork & branch** from `main`.
2. Run `pre‑commit install` to enable local hooks.
3. Submit a PR – CI lints and DQ validation must pass.

---

## License

MIT License © 2025 Mark Mestres
