from pathlib import Path

from custom_components.cure_afvalbeheer.models import CureData
from custom_components.cure_afvalbeheer.parser import CureParser
from custom_components.cure_afvalbeheer.weekday import Weekday


def test_parse_returns_cure_data():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    result = parser.parse()

    assert isinstance(result, CureData)

    assert len(result.locations) == 1

    location = result.locations[0]

    assert location.name == "Milieustraat Eindhoven"
    assert location.address is None

    assert len(location.hours) == 6
    assert location.hours[0].day is Weekday.MONDAY
    assert location.hours[-1].day is Weekday.SATURDAY
