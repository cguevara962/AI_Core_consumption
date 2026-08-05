"""
Material Consumption Prediction - Training Script
SAP AI Core | Training Pipeline
Downloads training CSV directly from S3 (bypasses Argo input artifact mounting).
"""
import os, json, sys, traceback, io
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_absolute_percentage_error
import joblib
import boto3

MODEL_DIR   = os.environ.get('MODEL_DIR',   '/app/model')
S3_BUCKET   = os.environ.get('S3_BUCKET',   'hcp-c096a718-bfa7-4194-858b-01b0ed9a3609')
S3_KEY      = os.environ.get('S3_KEY',      'consumption-ai/data/consumption.csv')
S3_ENDPOINT = os.environ.get('S3_ENDPOINT', 'https://s3.amazonaws.com')
S3_REGION   = os.environ.get('S3_REGION',   'us-east-1')
N_EST       = int(os.environ.get('N_ESTIMATORS', '200'))
MAX_DEPTH   = int(os.environ.get('MAX_DEPTH',    '8'))
TEST_SIZE   = float(os.environ.get('TEST_SIZE',  '0.2'))

try:
    os.makedirs(MODEL_DIR, exist_ok=True)
    print(f"MODEL_DIR={MODEL_DIR} ready", flush=True)

    print(f"Downloading s3://{S3_BUCKET}/{S3_KEY} ...", flush=True)
    s3 = boto3.client('s3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        region_name=S3_REGION)
    obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()), parse_dates=['date'])
    print(f"Loaded {len(df)} rows", flush=True)

    df = df.rename(columns={
        'material_ID': 'material_id',
        'isHoliday':   'is_holiday',
        'isWeekend':   'is_weekend',
        'isPayday':    'is_payday',
    })

    df = df.sort_values(['material_id', 'date']).reset_index(drop=True)
    df['day_of_week']  = df['date'].dt.dayofweek
    df['month']        = df['date'].dt.month
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
    df['day_of_month'] = df['date'].dt.day

    for lag in [7, 14, 28]:
        df[f'lag_{lag}d'] = df.groupby('material_id')['quantity'].shift(lag)

    df['rolling_4w_avg'] = (
        df.groupby(['material_id', 'day_of_week'])['quantity']
        .transform(lambda x: x.shift(1).rolling(4, min_periods=1).mean())
    )
    df = df.dropna(subset=['lag_7d', 'lag_14d', 'lag_28d', 'rolling_4w_avg'])
    print(f"After feature eng: {len(df)} rows", flush=True)

    le = LabelEncoder()
    df['material_encoded'] = le.fit_transform(df['material_id'])

    FEATURES = [
        'material_encoded', 'day_of_week', 'month', 'week_of_year',
        'day_of_month', 'is_holiday', 'is_weekend', 'is_payday',
        'lag_7d', 'lag_14d', 'lag_28d', 'rolling_4w_avg'
    ]
    X, y = df[FEATURES], df['quantity']
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=42, shuffle=False)

    print(f"Training RandomForest n_estimators={N_EST} max_depth={MAX_DEPTH} ...", flush=True)
    model = RandomForestRegressor(
        n_estimators=N_EST, max_depth=MAX_DEPTH, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae  = mean_absolute_error(y_test, y_pred)
    mape = mean_absolute_percentage_error(y_test, y_pred) * 100
    r2   = r2_score(y_test, y_pred)
    print(f"  MAE={mae:.4f}  MAPE={mape:.2f}%  R²={r2:.4f}", flush=True)

    joblib.dump(model, os.path.join(MODEL_DIR, 'model.pkl'))
    joblib.dump(le,    os.path.join(MODEL_DIR, 'label_encoder.pkl'))
    with open(os.path.join(MODEL_DIR, 'metadata.json'), 'w') as f:
        json.dump({
            'mae': round(mae, 4), 'mape': round(mape, 2), 'r2': round(r2, 4),
            'features': FEATURES, 'n_estimators': N_EST, 'max_depth': MAX_DEPTH,
            'materials': list(le.classes_),
            'train_rows': len(X_train), 'test_rows': len(X_test)
        }, f, indent=2)
    print(f"Model saved to {MODEL_DIR}", flush=True)

except Exception:
    traceback.print_exc(file=sys.stdout)
    sys.stdout.flush()
    sys.exit(1)
