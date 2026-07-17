from pathlib import Path

from custom_components.cure_afvalbeheer.models import CureData
from custom_components.cure_afvalbeheer.parser import CureParser


def test_parse_returns_cure_data():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    result = parser.parse()

    assert isinstance(result, CureData)

    assert len(result.locations) == 2

    assert result.locations[0].name == "Milieustraat Acht"
    assert result.locations[0].address == "Achtseweg Noord 41 5651 GG Eindhoven"

    assert result.locations[1].name == "Milieustraat Lodewijkstraat"
    assert result.locations[1].address == "Lodewijkstraat 9 5652 AC Eindhoven"
