"""
Generates synthetic consumption history CSV for testing.
Output: data/consumption.csv
"""
import csv, random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

MATERIALS = {
    'MAT-001': {'base': 200, 'seasonal': True,  'unit': 'KG'},
    'MAT-002': {'base': 80,  'seasonal': False, 'unit': 'L'},
    'MAT-003': {'base': 350, 'seasonal': True,  'unit': 'UN'},
    'MAT-004': {'base': 50,  'seasonal': False, 'unit': 'KG'},
    'MAT-005': {'base': 120, 'seasonal': True,  'unit': 'M'},
}

HOLIDAYS = {
    date(2022, 1, 1), date(2022, 4, 15), date(2022, 5, 1),
    date(2022, 12, 25), date(2022, 12, 26),
    date(2023, 1, 1), date(2023, 4, 7),  date(2023, 5, 1),
    date(2023, 12, 25), date(2023, 12, 26),
    date(2024, 1, 1), date(2024, 3, 29), date(2024, 5, 1),
    date(2024, 12, 25),
}

def qty(mat_id, d):
    cfg = MATERIALS[mat_id]
    base = cfg['base']
    # Seasonal boost for some materials (Q4 high)
    seasonal = 1.3 if (cfg['seasonal'] and d.month in [10,11,12]) else 1.0
    # Weekday factor
    wday = 1.0 if d.weekday() < 5 else 0.25
    # Holiday factor
    holiday = 0.05 if d in HOLIDAYS else 1.0
    # Payday boost
    payday = 1.4 if d.day in (1, 15) else 1.0
    noise = random.uniform(0.85, 1.15)
    return round(base * seasonal * wday * holiday * payday * noise, 2)

out = Path('data')
out.mkdir(exist_ok=True)

start = date(2022, 1, 1)
end   = date(2024, 12, 31)
rows  = []
d = start
while d <= end:
    for mid, cfg in MATERIALS.items():
        rows.append({
            'material_id': mid,
            'unit'       : cfg['unit'],
            'date'       : d.isoformat(),
            'quantity'   : qty(mid, d),
            'is_holiday' : int(d in HOLIDAYS),
            'is_weekend' : int(d.weekday() >= 5),
            'is_payday'  : int(d.day in (1, 15)),
        })
    d += timedelta(days=1)

with open('data/consumption.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} rows -> data/consumption.csv")
