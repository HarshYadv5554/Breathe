"""
Corporate travel export parser (Concur-style expense report CSV).

Concur exposes trip data via Expense Reports and Trip modules; CSV exports include
expense types, airport codes, and not always distances.
"""
from decimal import Decimal

from .common import (
    normalize_row_keys,
    parse_date_flexible,
    parse_decimal,
    read_csv_rows,
    row_hash,
)

# Approximate airport distances (km) for demo — production would use a distance table/API
AIRPORT_DISTANCE_KM = {
    ("JFK", "LHR"): 5540,
    ("LHR", "JFK"): 5540,
    ("SFO", "ORD"): 2960,
    ("ORD", "SFO"): 2960,
    ("DEL", "BOM"): 1150,
    ("BOM", "DEL"): 1150,
    ("LAX", "SEA"): 1540,
    ("SEA", "LAX"): 1540,
}

TRAVEL_FIELD_ALIASES = {
    "report_id": ["report_id", "expense_report_id", "report_key"],
    "employee": ["employee", "employee_name", "traveler"],
    "transaction_date": ["transaction_date", "posted_date", "expense_date"],
    "expense_type": ["expense_type", "category", "expense_category"],
    "vendor": ["vendor", "merchant", "supplier"],
    "amount": ["amount", "posted_amount", "transaction_amount"],
    "currency": ["currency", "posted_currency"],
    "origin": ["origin", "from_location", "departure_city", "origin_airport_code"],
    "destination": ["destination", "to_location", "arrival_city", "destination_airport_code"],
    "distance": ["distance", "mileage", "distance_mi", "distance_km"],
    "distance_unit": ["distance_unit", "mileage_unit"],
}


def _pick(row: dict, field: str) -> str:
    for alias in TRAVEL_FIELD_ALIASES.get(field, [field]):
        if alias in row and row[alias]:
            return str(row[alias]).strip()
    return ""


def _travel_subcategory(expense_type: str) -> str:
    et = expense_type.lower()
    if "air" in et or "flight" in et:
        return "air"
    if "hotel" in et or "lodging" in et:
        return "hotel"
    if "rail" in et or "train" in et:
        return "rail"
    if "car" in et or "ground" in et or "mileage" in et:
        return "ground"
    return "other"


def _infer_distance_km(origin: str, destination: str, distance_raw, distance_unit: str):
    flags = []
    if distance_raw is not None:
        unit = (distance_unit or "mi").lower()
        if unit in ("km", "kilometers"):
            return distance_raw, "km", flags
        if unit in ("mi", "miles", ""):
            return distance_raw * Decimal("1.60934"), "km", flags

    o = origin.upper()[:3] if origin else ""
    d = destination.upper()[:3] if destination else ""
    if len(o) == 3 and len(d) == 3:
        key = (o, d)
        if key in AIRPORT_DISTANCE_KM:
            flags.append("missing_distance")
            return Decimal(str(AIRPORT_DISTANCE_KM[key])), "km", flags
        flags.append("missing_distance")
        return Decimal("500"), "km", flags  # conservative placeholder

    return None, "", ["missing_distance"]


def parse_travel_csv(content: str, **_kwargs) -> list[dict]:
    rows = read_csv_rows(content)
    results = []

    for i, raw in enumerate(rows, start=2):
        row = normalize_row_keys(raw)
        errors = []

        txn_date = parse_date_flexible(_pick(row, "transaction_date"))
        expense_type = _pick(row, "expense_type")
        subcategory = _travel_subcategory(expense_type)

        distance_raw = parse_decimal(_pick(row, "distance"))
        origin = _pick(row, "origin")
        destination = _pick(row, "destination")
        qty_norm, unit_norm, dist_flags = _infer_distance_km(
            origin, destination, distance_raw, _pick(row, "distance_unit")
        )

        amount = parse_decimal(_pick(row, "amount"))
        flags = list(dist_flags)

        if subcategory == "air" and not qty_norm:
            flags.append("missing_distance")

        if subcategory in ("hotel", "other") and amount:
            qty_norm = amount
            unit_norm = (_pick(row, "currency") or "usd").lower() + "_spend"
            flags = []

        results.append(
            {
                "row_number": i,
                "raw_payload": raw,
                "parse_errors": errors,
                "normalized": {
                    "scope": "3",
                    "category": "business_travel",
                    "subcategory": subcategory,
                    "activity_date": txn_date.date().isoformat() if txn_date else None,
                    "period_start": txn_date.date().isoformat() if txn_date else None,
                    "period_end": txn_date.date().isoformat() if txn_date else None,
                    "site_name": "",
                    "plant_code": "",
                    "vendor_or_carrier": _pick(row, "vendor"),
                    "description": f"{expense_type}: {origin} → {destination}".strip(" :→"),
                    "quantity_raw": str(distance_raw or amount) if (distance_raw or amount) else None,
                    "unit_raw": _pick(row, "distance_unit") or _pick(row, "currency"),
                    "quantity_normalized": str(qty_norm) if qty_norm is not None else "0",
                    "unit_normalized": unit_norm or "km",
                    "source_reference": _pick(row, "report_id"),
                    "source_row_hash": row_hash(row),
                    "suspicion_flags": flags,
                },
            }
        )

    return results
