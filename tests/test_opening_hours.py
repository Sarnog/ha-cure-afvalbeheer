from pathlib import Path

from custom_components.cure_afvalbeheer.parser import CureParser


def test_opening_hours():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    hours = parser.opening_hours()

    assert len(hours) >= 7

    assert hours[0].day == "Maandag"

    assert not hours[0].closed
