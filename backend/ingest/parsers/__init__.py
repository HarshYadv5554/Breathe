from .sap import parse_sap_csv
from .travel import parse_travel_csv
from .utility import parse_utility_csv

PARSERS = {
    "sap_mm": parse_sap_csv,
    "utility_portal": parse_utility_csv,
    "travel_concur": parse_travel_csv,
}
