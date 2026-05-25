"""
SAP MM procurement/fuel flat-file export parser.

Real-world: sustainability teams often receive semicolon-delimited extracts from
SAP GUI (SE16 / custom Z-reports) rather than live OData. German headers appear in
EU deployments.
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

# Map DE and EN column aliases seen in SAP Z-report exports
SAP_FIELD_ALIASES = {
    "material_document": ["material_document", "mblnr", "belegnummer"],
    "posting_date": ["posting_date", "budat", "buchungsdatum"],
    "plant": ["plant", "werks", "plant_code"],
    "material": ["material", "matnr", "material_number"],
    "description": ["description", "maktx", "kurztext", "short_text"],
    "quantity": ["quantity", "menge", "qty"],
    "unit": ["unit", "meins", "unit_of_measure", "uom"],
    "amount": ["amount", "dmbtr", "net_value", "value"],
    "currency": ["currency", "waers", "curr"],
    "vendor": ["vendor", "lifnr", "vendor_name", "name1"],
    "movement_type": ["movement_type", "bwart", "bewegungsart"],
}


def _pick(row: dict, field: str) -> str:
    for alias in SAP_FIELD_ALIASES.get(field, [field]):
        if alias in row and row[alias]:
            return str(row[alias]).strip()
    return ""


def _classify_sap_row(row: dict) -> tuple[str, str, str]:
    """Returns (scope, category, subcategory)."""
    desc = (_pick(row, "description") + " " + _pick(row, "material")).lower()
    movement = _pick(row, "movement_type")

    fuel_keywords = ("diesel", "petrol", "gasoline", "fuel", "kerosene", "heating oil", "benzin")
    if any(k in desc for k in fuel_keywords) or movement in ("201", "261"):
        return "1", "mobile_combustion" if "fleet" in desc or "vehicle" in desc else "stationary_combustion", "fuel"

    return "3", "purchased_goods", "procurement"


def parse_sap_csv(content: str, plant_lookup: dict | None = None) -> list[dict]:
    plant_lookup = plant_lookup or {}
    rows = read_csv_rows(content)
    results = []

    for i, raw in enumerate(rows, start=2):
        row = normalize_row_keys(raw)
        errors = []

        posting = parse_date_flexible(_pick(row, "posting_date"))
        if not posting:
            errors.append("Could not parse posting date")

        qty = parse_decimal(_pick(row, "quantity"))
        unit_raw = _pick(row, "unit")
        qty_norm, unit_norm, unit_flags = normalize_unit(qty, unit_raw)

        plant = _pick(row, "plant")
        site_name = plant_lookup.get(plant, "")
        flags = list(unit_flags)
        if plant and not site_name:
            flags.append("unknown_plant")

        scope, category, subcategory = _classify_sap_row(row)

        if qty_norm and qty_norm > Decimal("500000"):
            flags.append("high_quantity")

        results.append(
            {
                "row_number": i,
                "raw_payload": raw,
                "parse_errors": errors,
                "normalized": {
                    "scope": scope,
                    "category": category,
                    "subcategory": subcategory,
                    "activity_date": posting.date().isoformat() if posting else None,
                    "period_start": posting.date().isoformat() if posting else None,
                    "period_end": posting.date().isoformat() if posting else None,
                    "site_name": site_name,
                    "plant_code": plant,
                    "vendor_or_carrier": _pick(row, "vendor"),
                    "description": _pick(row, "description") or _pick(row, "material"),
                    "quantity_raw": str(qty) if qty is not None else None,
                    "unit_raw": unit_raw,
                    "quantity_normalized": str(qty_norm) if qty_norm is not None else "0",
                    "unit_normalized": unit_norm,
                    "source_reference": _pick(row, "material_document"),
                    "source_row_hash": row_hash(row),
                    "suspicion_flags": flags,
                },
            }
        )

    return results
