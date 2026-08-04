# Material Consumption Prediction — SAP AI Core + CAP

## Project Structure

```
material-consumption-ai/
├── .aicore/
│   ├── training-pipeline.yaml   # Argo Workflow — trains the model
│   └── serving-template.yaml    # KServe — deploys the inference server
├── src/
│   ├── train.py                 # Training script (RandomForest + lag features)
│   ├── serve.py                 # Flask inference server (KServe compatible)
│   ├── utils.py                 # Shared date/feature utilities
│   └── generate_sample_data.py  # Generates synthetic training data
├── Dockerfile.train             # Docker image for training
├── Dockerfile.serve             # Docker image for serving
├── requirements-train.txt
├── requirements-serve.txt
├── cap-app/
│   ├── db/
│   │   ├── schema.cds           # Data model (Materials, ConsumptionHistory, Predictions)
│   │   └── data/                # Initial CSV data (2 years synthetic history)
│   ├── srv/
│   │   ├── consumption-service.cds   # OData V4 service definition
│   │   ├── consumption-service.js    # Service implementation + refreshPredictions
│   │   └── aicore-client.js          # AI Core inference client
│   ├── app/
│   │   ├── consumption-history/      # Fiori Elements List Report — historical data
│   │   └── predictions/              # Fiori Elements List Report — today's predictions
│   └── .env.example             # Environment variables template
└── notebooks/
    └── 01_setup_aicore.ipynb    # Step-by-step AI Core setup notebook
```

## Quick Start

### Step 1 — Build & push Docker images
```bash
docker build -f Dockerfile.train -t <YOUR_DOCKER_REGISTRY>/consumption-train:latest .
docker build -f Dockerfile.serve -t <YOUR_DOCKER_REGISTRY>/consumption-serve:latest .
docker push <YOUR_DOCKER_REGISTRY>/consumption-train:latest
docker push <YOUR_DOCKER_REGISTRY>/consumption-serve:latest
```

### Step 2 — Upload training data to Object Store
```bash
# Generate data locally first:
cd src && python generate_sample_data.py
# Then upload data/consumption.csv to your S3 / Object Store bucket.
```

### Step 3 — Register templates in AI Core
Replace `<YOUR_DOCKER_REGISTRY>` in `.aicore/*.yaml`, commit and push to your Git repo,
then follow `notebooks/01_setup_aicore.ipynb`.

### Step 4 — Run the CAP application
```bash
cd cap-app
cp .env.example .env   # fill in AI Core credentials
npm install
npm run dev
```

Open the List Report apps:
- `http://localhost:4004/consumption-history/` — Historical consumption behaviour
- `http://localhost:4004/predictions/`          — Today's AI Core predictions

To generate today's predictions, call the OData action:
```
POST http://localhost:4004/consumption/refreshPredictions
```

## Model Features
| Feature | Description |
|---|---|
| material_encoded | Label-encoded material ID |
| day_of_week | 0 = Monday … 6 = Sunday |
| month | 1–12 |
| week_of_year | 1–53 |
| day_of_month | 1–31 |
| is_holiday | Public holiday flag (0/1) |
| is_weekend | Saturday or Sunday flag (0/1) |
| is_payday | 1st or 15th of month (0/1) |
| lag_7d | Consumption 7 days ago (same material) |
| lag_14d | Consumption 14 days ago |
| lag_28d | Consumption 28 days ago |
| rolling_4w_avg | Avg of same weekday over last 4 weeks |

## Customization
- **Holidays**: Update `HOLIDAYS` in `src/train.py` and `src/generate_sample_data.py`.
- **Payday schedule**: Update `PAYDAY_DAYS` in `src/utils.py`.
- **Model algorithm**: Replace `RandomForestRegressor` in `train.py` with XGBoost, LightGBM, etc.
- **Materials**: The model handles any number of materials — just load them into the `Materials` entity.
