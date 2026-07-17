"""Constants for the Cure Afvalbeheer integration."""

DOMAIN = "cure_afvalbeheer"

NAME = "Cure Afvalbeheer"

MANUFACTURER = "Cure Afvalbeheer"

BASE_URL = "https://www.cure-afvalbeheer.nl"

MUNICIPALITIES: dict[str, str] = {
    "eindhoven": "Eindhoven",
    "valkenswaard": "Valkenswaard",
    "geldrop-mierlo": "Geldrop-Mierlo",
}

CONF_MUNICIPALITY = "municipality"
CONF_LOOKAHEAD_DAYS = "lookahead_days"
CONF_UPDATE_INTERVAL_MINUTES = "update_interval_minutes"

DEFAULT_LOOKAHEAD_DAYS = 5
DEFAULT_UPDATE_INTERVAL_MINUTES = 60

ISSUE_NO_LOCATIONS_FOUND = "no_locations_found"
