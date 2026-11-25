"""Gedeelde hulpjes voor de tests: echte teksten van cure-afvalbeheer.nl."""

from pathlib import Path


def read_fixture(name: str) -> str:
    """Return a saved page from tests/fixtures as text."""

    return (Path("tests/fixtures") / name).read_text(encoding="utf-8")


EINDHOVEN_CLOSURE_BODY = (
    "Let op! Lodewijkstraat wordt verbouwd Kijk voor alle informatie over onze "
    "verbouwing op deze pagina Kom naar onze milieustraat in Acht. Achtseweg "
    "Noord 41, 5651 GG Eindhoven Datum sluiting: 30-11-2025 Attention! "
    "Lodewijkstraat will be undergoing renovations!"
)

# Real text captured live from cure-afvalbeheer.nl on 2026-07-17.
HEAT_PROTOCOL_HEADING = (
    "Hitteprotocol update! Tot en met donderdag 16 juli gewijzigde "
    "openingstijden op de milieustraten: geopend van 08:00 tot 14:00"
)

# The news item that same banner links to, which words it differently again.
HEAT_PROTOCOL_NEWS_ITEM = (
    "Hitteprotocol! 13 tot en met 15 Augustus aangepaste openingstijden "
    "(08:00 - 14:00) op onze milieustraten"
)

# The same announcement as Cure worded it a month later: a period written
# out with both of its ends, and "t/m" instead of "tot en met".
HEAT_PROTOCOL_RANGE_HEADING = (
    "Let op! Hitteprotocol van 13 t/m 15 Augustus! Gewijzigde "
    "openingstijden milieustraten van 08:00 tot 14:00."
)

NO_NOTICE_HEADING = "Inpaktips voor vertrek"

VALKENSWAARD_CLOSURE_BODY = (
    "Let op! Milieustraat Valkenswaard dicht i.v.m. werkzaamheden. Op de "
    "volgende data is de milieustraat in Valkenswaard gesloten in verband met "
    "werkzaamheden: Dinsdag 30 juni 2026 Woensdag 1 juli 2026 Donderdag 2 juli "
    "2026 Bewoners van de gemeenten Valkenswaard en Heeze-Leende kunnen terecht "
    "bij de milieustraat in Geldrop."
)
