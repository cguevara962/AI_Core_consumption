"""
Material Consumption Prediction - Training Script
SAP AI Core | Training Pipeline

Features used:
  - material_encoded   : label-encoded material ID
  - day_of_week        : 0=Monday ... 6=Sunday
  - month              : 1-12
  - week_of_year       : 1-53
  - day_of_month       : 1-31
  - is_holiday         : 0/1
  - is_weekend         : 0/1
  - is_payday          : 0/1
  - lag_7d             : consumption 7 days ago (same material)
  - lag_14d            : consumption 14 days ago
  - lag_28d            : consumption 28 days ago
  - rolling_4w_avg     : rolling avg of same weekday over last 4 weeks
"""
import os, json
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_absolute_percentage_error
import joblib

DATA_PATH  = os.environ.get('DATA_PATH',  '/app/data/consumption.csv')
MODEL_DIR  = os.environ.get('MODEL_DIR',  '/app/model')
N_EST      = int(os.environ.get('N_ESTIMATORS', '200'))
MAX_DEPTH  = int(os.environ.get('MAX_DEPTH',    '8'))
TEST_SIZE  = float(os.environ.get('TEST_SIZE',  '0.2'))

print(f"Loading data from {DATA_PATH} ...")
df = pd.read_csv(DATA_PATH, parse_dates=['date'])

# ── Feature engineering ──────────────────────────────────────────────────────
df = df.sort_values(['material_id', 'date']).reset_index(drop=True)
df['day_of_week']  = df['date'].dt.dayofweek
df['month']        = df['date'].dt.month
df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
df['day_of_month'] = df['date'].dt.day

# Lag features
for lag in [7, 14, 28]:
    df[f'lag_{lag}d'] = df.groupby('material_id')['quantity'].shift(lag)

# Rolling 4-week average of the same weekday
df['rolling_4w_avg'] = (
    df.groupby(['material_id', 'day_of_week'])['quantity']
    .transform(lambda x: x.shift(1).rolling(4, min_periods=1).mean())
)

df = df.dropna(subset=['lag_7d', 'lag_14d', 'lag_28d', 'rolling_4w_avg'])

# ── Encode material ───────────────────────────────────────────────────────────
le = LabelEncoder()
df['material_encoded'] = le.fit_transform(df['material_id'])

FEATURES = [
    'material_encoded', 'day_of_week', 'month', 'week_of_year',
    'day_of_month', 'is_holiday', 'is_weekend', 'is_payday',
    'lag_7d', 'lag_14d', 'lag_28d', 'rolling_4w_avg'
]
TARGET = 'quantity'

X, y = df[FEATURES], df[TARGET]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=42, shuffle=False
)

# ── Train ─────────────────────────────────────────────────────────────────────
print(f"Training RandomForest  n_estimators={N_EST}  max_depth={MAX_DEPTH} ...")
model = RandomForestRegressor(
    n_estimators=N_EST, max_depth=MAX_DEPTH,
    random_state=42, n_jobs=-1
)
model.fit(X_train, y_train)

# ── Evaluate ──────────────────────────────────────────────────────────────────
y_pred = model.predict(X_test)
mae    = mean_absolute_error(y_test, y_pred)
mape   = mean_absolute_percentage_error(y_test, y_pred) * 100
r2     = r2_score(y_test, y_pred)
print(f"  MAE : {mae:.4f}")
print(f"  MAPE: {mape:.2f}%")
print(f"  R²  : {r2:.4f}")

# ── Save ──────────────────────────────────────────────────────────────────────
os.makedirs(MODEL_DIR, exist_ok=True)
joblib.dump(model, os.path.join(MODEL_DIR, 'model.pkl'))
joblib.dump(le,    os.path.join(MODEL_DIR, 'label_encoder.pkl'))

metadata = {
    'mae': round(mae, 4), 'mape': round(mape, 2), 'r2': round(r2, 4),
    'features': FEATURES, 'n_estimators': N_EST, 'max_depth': MAX_DEPTH,
    'materials': le.classes_.tolist(),
    'train_rows': len(X_train), 'test_rows': len(X_test)
}
with open(os.path.join(MODEL_DIR, 'metadata.json'), 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"Model saved to {MODEL_DIR}")
