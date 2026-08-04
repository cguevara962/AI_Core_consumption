# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

A full-stack **material consumption prediction** system:
- **Python ML pipeline** (RandomForest via scikit-learn) trained and deployed on **SAP AI Core** (Argo Workflows for training, KServe for serving)
- **SAP CAP (Node.js)** backend exposing an OData V4 service
- Two **SAP Fiori Elements** frontend apps (auto-generated List Reports)

## Common Commands

### CAP Application (run from `cap-app/`)

```bash
cp .env.example .env      # then fill in AI Core credentials
npm install
npm run dev               # cds watch — hot-reload on :4004
npm run build             # cds build --production
npm run deploy            # cds deploy --to sqlite
```

### Python ML (run from repo root)

```bash
# Generate synthetic training data
python src/generate_sample_data.py        # writes src/data/consumption.csv

# Train locally
DATA_PATH=data/consumption.csv MODEL_DIR=./model python src/train.py

# Run inference server locally (listens on :9001)
STORAGE_URI=./model python src/serve.py
```

### Docker Builds

```bash
docker build -f Dockerfile.train -t <REGISTRY>/consumption-train:latest .
docker build -f Dockerfile.serve -t <REGISTRY>/consumption-serve:latest .
```

### Manual Testing (no automated test suite)

```bash
# Test inference server directly
curl -X POST http://localhost:9001/v2/models/consumption-model/infer \
  -H 'Content-Type: application/json' \
  -d '{"inputs":[{"data":[{"material_id":"MAT-001","date":"2026-08-04","is_holiday":false,"is_weekend":false,"is_payday":true,"lag_7d":120.5,"lag_14d":115.0,"lag_28d":130.2,"rolling_4w_avg":121.9}]}]}'

# Trigger prediction refresh from CAP layer
curl -X POST http://localhost:4004/consumption/refreshPredictions
```

## Architecture

### End-to-End Data Flow

1. `src/generate_sample_data.py` creates 3 years of synthetic daily consumption for 5 materials (MAT-001 to MAT-005).
2. That CSV is uploaded to an S3-compatible object store and registered as an AI Core artifact.
3. The Argo WorkflowTemplate (`.aicore/training-pipeline.yaml`) runs `train.py` in Docker on SAP AI Core, writing `model.pkl`, `label_encoder.pkl`, and `metadata.json` to the `trained-model` artifact.
4. The ServingTemplate (`.aicore/serving-template.yaml`) deploys `serve.py` via KServe, mounting the model artifact at `STORAGE_URI`.
5. When the `refreshPredictions` OData action is triggered, `cap-app/srv/consumption-service.js`:
   - Reads all materials and 35 days of history from SQLite
   - Computes lag features (lag_7d, lag_14d, lag_28d, rolling_4w_avg) locally in JS
   - Calls `aicore-client.js`, which fetches an OAuth2 token from BTP then POSTs to the AI Core deployment URL
   - Upserts returned predictions into `MaterialPredictions`

### Feature Engineering Split

Calendar features (`day_of_week`, `month`, `is_weekend`, `is_payday`, etc.) are computed in **both** `src/utils.py` (Python, for training) and inline in `cap-app/srv/consumption-service.js` (JS, for inference prep). If you modify feature logic, both sides must stay in sync.

Lag features are computed with pandas `groupby.shift` in Python during training, and by querying `ConsumptionHistory` and doing date lookups in JS during serving.

### Key Files

| File | Role |
|---|---|
| `cap-app/db/schema.cds` | CDS data model: `Materials`, `ConsumptionHistory`, `MaterialPredictions` |
| `cap-app/srv/consumption-service.cds` | OData V4 service + `refreshPredictions` action definition |
| `cap-app/srv/consumption-service.js` | Action handler: lag feature computation + AI Core call + DB upsert |
| `cap-app/srv/aicore-client.js` | OAuth2 `client_credentials` flow + Axios POST to inference endpoint |
| `src/train.py` | RandomForest training; reads `DATA_PATH`, writes to `MODEL_DIR` |
| `src/serve.py` | Flask inference server; KServe V2 inference protocol on `:9001` |
| `src/utils.py` | Shared calendar utilities used by both train and serve |

### Environment Variables

Defined in `cap-app/.env.example`:

| Variable | Purpose |
|---|---|
| `AICORE_URL` | Base AI Core API URL |
| `AICORE_TOKEN_URL` | OAuth2 token endpoint |
| `AICORE_CLIENT_ID` / `AICORE_CLIENT_SECRET` | OAuth2 credentials |
| `AICORE_RESOURCE_GROUP` | Resource group (default: `default`) |
| `AICORE_DEPLOYMENT_URL` | Full URL for the active inference deployment |

Python training also accepts `N_ESTIMATORS` (default 200), `MAX_DEPTH` (default 8), `TEST_SIZE` (default 0.2).

### Database

SQLite in dev (`db.sqlite`), HANA-compatible for production via `@sap/hana-client`. CDS `lean_draft` mode is enabled. Schema is defined entirely in `cap-app/db/schema.cds`.
