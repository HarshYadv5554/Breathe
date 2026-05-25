"""
Utility portal CSV parser (monthly interval / demand export style).

Facilities teams typically download CSV from PG&E, Con Edison, or similar portals.
Billing periods rarely align to calendar months — we preserve period_start/end.
"""
from decimal import Decimal

from .common import (
    normalize_row_keys,
    normalize_unit,
    parse_date_flexible,
    parse_decimal,
    read_csv_rows,
    row_hash,
)

UTILITY_FIELD_ALIASES = {
    "account": ["account", "account_number", "service_account"],
    "meter": ["meter", "meter_number", "meter_id"],
    "site": ["site", "service_address", "facility", "location_name"],
    "period_start": ["period_start", "bill_period_start", "start_date", "from_date"],
    "period_end": ["period_end", "bill_period_end", "end_date", "to_date"],
    "usage": ["usage", "consumption", "total_kwh", "energy_kwh", "quantity"],
    "unit": ["unit", "uom", "usage_unit"],
    "charges": ["total_charges", "amount_due", "bill_total"],
    "tariff": ["rate_schedule", "tariff", "rate_plan"],
}


def _pick(row: dict, field: str) -> str:
    for alias in UTILITY_FIELD_ALIASES.get(field, [field]):
        if alias in row and row[alias]:
            return str(row[alias]).strip()
    return ""


def parse_utility_csv(content: str, **_kwargs) -> list[dict]:
    rows = read_csv_rows(content)
    results = []

    for i, raw in enumerate(rows, start=2):
        row = normalize_row_keys(raw)
        errors = []

        p_start = parse_date_flexible(_pick(row, "period_start"))
        p_end = parse_date_flexible(_pick(row, "period_end"))

        if not p_start or not p_end:
            errors.append("Missing billing period dates")

        usage = parse_decimal(_pick(row, "usage"))
        unit_raw = _pick(row, "unit") or "kWh"
        qty_norm, unit_norm, unit_flags = normalize_unit(usage, unit_raw.lower().replace("kwh", "kwh"))

        flags = list(unit_flags)

        # Flag when billing period doesn't span a clean calendar month
        if p_start and p_end:
            if p_start.day != 1 or (p_end - p_start).days < 27 or (p_end - p_start).days > 35:
                flags.append("billing_period_gap")
            activity_date = p_end.date()
        else:
            activity_date = None

        if usage and usage > Decimal("10000000"):
            flags.append("high_quantity")

        results.append(
            {
                "row_number": i,
                "raw_payload": raw,
                "parse_errors": errors,
                "normalized": {
                    "scope": "2",
                    "category": "purchased_electricity",
                    "subcategory": _pick(row, "tariff") or "grid_electricity",
                    "activity_date": activity_date.isoformat() if activity_date else None,
                    "period_start": p_start.date().isoformat() if p_start else None,
                    "period_end": p_end.date().isoformat() if p_end else None,
                    "site_name": _pick(row, "site"),
                    "plant_code": "",
                    "vendor_or_carrier": _pick(row, "account"),
                    "description": f"Meter {_pick(row, 'meter')} — {_pick(row, 'tariff')}",
                    "quantity_raw": str(usage) if usage is not None else None,
                    "unit_raw": unit_raw,
                    "quantity_normalized": str(qty_norm) if qty_norm is not None else "0",
                    "unit_normalized": unit_norm or "kwh",
                    "source_reference": _pick(row, "meter"),
                    "source_row_hash": row_hash(row),
                    "suspicion_flags": flags,
                },
            }
        )

    return results
