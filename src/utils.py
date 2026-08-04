"""Shared utilities for train.py and serve.py."""
from datetime import date

PAYDAY_DAYS = {1, 15}   # Adjust to your company's payroll schedule

def is_weekend(d: date) -> bool:
    return d.weekday() >= 5

def is_payday(d: date) -> bool:
    return d.day in PAYDAY_DAYS

def day_features(d: date) -> dict:
    return {
        'day_of_week' : d.weekday(),
        'month'       : d.month,
        'week_of_year': d.isocalendar()[1],
        'day_of_month': d.day,
        'is_weekend'  : int(is_weekend(d)),
        'is_payday'   : int(is_payday(d)),
    }
