import csv
import hashlib
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from dateutil import parser as date_parser


def read_csv_rows(content: str, delimiter: str | None = None) -> list[dict]:
    """Detect delimiter (; common in DE SAP exports, or comma)."""
    sample = content[:2048]
    if delimiter is None:
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    return [dict(row) for row in reader]


def normalize_header(key: str) -> str:
    return re.sub(r"\s+", "_", key.strip().lower())


def normalize_row_keys(row: dict) -> dict:
    return {normalize_header(k): v.strip() if isinstance(v, str) else v for k, v in row.items()}


def parse_decimal(value) -> Decimal | None:
    if value is None or value == "":
        return None
    s = str(value).strip().replace(",", ".")
    s = re.sub(r"[^\d.\-]", "", s)
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def parse_date_flexible(value) -> datetime | None:
    if not value or not str(value).strip():
        return None
    s = str(value).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return date_parser.parse(s, dayfirst=True)
    except (ValueError, TypeError):
        return None


def row_hash(payload: dict) -> str:
    canonical = "|".join(f"{k}={payload.get(k, '')}" for k in sorted(payload.keys()))
    return hashlib.sha256(canonical.encode()).hexdigest()[:32]


# Unit conversion to canonical bases for GHG calc prep
UNIT_TO_NORMALIZED = {
    "l": ("liters", Decimal("1")),
    "liter": ("liters", Decimal("1")),
    "liters": ("liters", Decimal("1")),
    "litre": ("liters", Decimal("1")),
    "gal": ("liters", Decimal("3.78541")),
    "gallon": ("liters", Decimal("3.78541")),
    "gallons": ("liters", Decimal("3.78541")),
    "kg": ("kg", Decimal("1")),
    "kilogram": ("kg", Decimal("1")),
    "t": ("kg", Decimal("1000")),
    "ton": ("kg", Decimal("1000")),
    "tonne": ("kg", Decimal("1000")),
    "kwh": ("kwh", Decimal("1")),
    "mwh": ("kwh", Decimal("1000")),
    "mi": ("km", Decimal("1.60934")),
    "miles": ("km", Decimal("1.60934")),
    "km": ("km", Decimal("1")),
    "eur": ("eur_spend", Decimal("1")),
    "usd": ("usd_spend", Decimal("1")),
}


def normalize_unit(quantity: Decimal | None, unit: str) -> tuple[Decimal | None, str, list[str]]:
    flags = []
    if quantity is None:
        return None, "", flags
    u = (unit or "").strip().lower()
    if u in UNIT_TO_NORMALIZED:
        norm_unit, factor = UNIT_TO_NORMALIZED[u]
        return quantity * factor, norm_unit, flags
    if u:
        flags.append("unit_mismatch")
    return quantity, u or "unknown", flags
