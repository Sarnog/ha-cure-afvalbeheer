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
