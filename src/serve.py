"""
Material Consumption Prediction - Serving Script
SAP AI Core | KServe compatible endpoint

Endpoint: POST /v2/models/consumption-model/infer
Health:   GET  /health

Request body:
{
  "inputs": [{
    "data": [
      {
        "material_id"   : "MAT-001",
        "date"          : "2026-08-04",
        "is_holiday"    : false,
        "is_weekend"    : false,
        "is_payday"     : true,
        "lag_7d"        : 120.5,
        "lag_14d"       : 115.0,
        "lag_28d"       : 130.2,
        "rolling_4w_avg": 121.9
      }
    ]
  }]
}
"""
import os, json, joblib
import pandas as pd
from flask import Flask, request, jsonify

MODEL_DIR = os.environ.get('STORAGE_URI', '/app/model')

app    = Flask(__name__)
model  = None
le     = None
meta   = None

def load_model():
    global model, le, meta
    model = joblib.load(f'{MODEL_DIR}/model.pkl')
    le    = joblib.load(f'{MODEL_DIR}/label_encoder.pkl')
    with open(f'{MODEL_DIR}/metadata.json') as f:
        meta = json.load(f)
    print(f"Model loaded — materials: {meta['materials']}")

def build_row(inst):
    d = pd.Timestamp(inst.get('date', str(pd.Timestamp.today().date())))
    mat = inst['material_id']
    if mat not in le.classes_:
        raise ValueError(f"Unknown material_id '{mat}'. Known: {list(le.classes_)}")
    return {
        'material_encoded': int(le.transform([mat])[0]),
        'day_of_week'     : int(d.dayofweek),
        'month'           : int(d.month),
        'week_of_year'    : int(d.isocalendar()[1]),
        'day_of_month'    : int(d.day),
        'is_holiday'      : int(bool(inst.get('is_holiday', False))),
        'is_weekend'      : int(bool(inst.get('is_weekend', False))),
        'is_payday'       : int(bool(inst.get('is_payday', False))),
        'lag_7d'          : float(inst.get('lag_7d', 0)),
        'lag_14d'         : float(inst.get('lag_14d', 0)),
        'lag_28d'         : float(inst.get('lag_28d', 0)),
        'rolling_4w_avg'  : float(inst.get('rolling_4w_avg', 0)),
    }

@app.route('/v2/models/consumption-model/infer', methods=['POST'])
def infer():
    body      = request.get_json(force=True)
    instances = body.get('inputs', [{}])[0].get('data', [])
    results   = []
    for inst in instances:
        try:
            row  = build_row(inst)
            df   = pd.DataFrame([row])[meta['features']]
            pred = float(model.predict(df)[0])
            results.append({
                'material_id'       : inst['material_id'],
                'date'              : inst.get('date'),
                'predicted_quantity': round(max(pred, 0), 3)
            })
        except Exception as e:
            results.append({'material_id': inst.get('material_id', '?'), 'error': str(e)})
    return jsonify({'outputs': [{'data': results}]})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model_loaded': model is not None})

if __name__ == '__main__':
    load_model()
    app.run(host='0.0.0.0', port=9001)
