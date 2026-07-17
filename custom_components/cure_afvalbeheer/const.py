"""Constants for the Cure Afvalbeheer integration."""

DOMAIN = "cure_afvalbeheer"

NAME = "Cure Afvalbeheer"

MANUFACTURER = "Cure Afvalbeheer"

DEFAULT_SCAN_INTERVAL = 3600  # seconden

BASE_URL = "https://www.cure-afvalbeheer.nl"

MUNICIPALITIES: dict[str, str] = {
    "eindhoven": "Eindhoven",
    "valkenswaard": "Valkenswaard",
    "geldrop-mierlo": "Geldrop-Mierlo",
}

CONF_MUNICIPALITY = "municipality"
CONF_LOOKAHEAD_DAYS = "lookahead_days"

DEFAULT_LOOKAHEAD_DAYS = 5
