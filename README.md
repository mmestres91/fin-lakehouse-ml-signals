# fin-lakehouse-ml-signals

[![CI](https://github.com/mmestres91/fin-lakehouse-ml-signals/actions/workflows/ci.yml/badge.svg)](https://github.com/mmestres91/fin-lakehouse-ml-signals/actions/workflows/ci.yml)

A reproducible data‑quality and ML‑feature pipeline for equities‑market signals built on:

* **Python 3.11** (managed by \[Poetry])
* **Polars → Pandas** for fast columnar transforms
* **Great Expectations 0.18** (Fluent API) for data‑quality rules
* **Apache Airflow 2.6+** for daily orchestration
* **Terraform ≥ 1.8** (+ AWS provider 5.x) to provision encrypted S3 buckets, logging targets, and KMS keys
* **AWS S3** as the curated storage & documentation bucket

---

## Repository layout

```text
fin-lakehouse-ml-signals/
├── dags/                         # Airflow DAGs (TaskFlow style)
│   ├── raw_market_ingest_dag.py      # pulls hourly/daily raw market data from vendor API
│   ├── transform_market_data_dag.py  # Polars → curated Parquet transformation
│   └── curated_market_dq_dag.py      # Great Expectations validation
├── infra/                        # IaC — Terraform modules & env configs
│   ├── main.tf                   # root module (buckets, KMS, etc.)
│   ├── variables.tf              # shared variables
│   ├── terraform.tfvars.example  # sample values
│   └── modules/
│       └── bucket_curated/       # reusable S3/KMS sub‑module
│           ├── main.tf
│           └── variables.tf
├── great_expectations/           # GE project (auto‑generated)
│   ├── expectations/
│   │   └── curated_market_suite.json
│   └── checkpoints/
│       └── curated_market_ckpt.yml
├── scripts/
│   ├── create_expectations.py    # one‑off helper to build the suite
│   ├── create_checkpoint.py      # one‑off helper to register checkpoint
│   └── validate_curated.py       # CLI/CI runner for the checkpoint
├── .github/workflows/            # CI pipelines
│   ├── precommit.yml             # lint, type‑check, Terraform fmt
│   ├── dq_validation.yml         # run GE validation on PRs
│   └── trigger_airflow.yml       # launch prod DAG after merge
├── pyproject.toml                # Poetry deps + tool config
└── README.md                     # ← you are here
```

---

## Quick‑start (local)

```bash
# clone & install
git clone git@github.com:mmestres91/fin-lakehouse-ml-signals.git
cd fin-lakehouse-ml-signals
poetry install

# create or update GE artifacts
poetry run python scripts/create_expectations.py
poetry run python scripts/create_checkpoint.py

# validate the current curated Parquet
poetry run python scripts/validate_curated.py \
  --path s3://finlakehouse-curated-mmestres91/market/spy_transformed.parquet
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
