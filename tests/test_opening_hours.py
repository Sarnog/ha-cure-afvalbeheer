from pathlib import Path

from custom_components.cure_afvalbeheer.parser import CureParser
from custom_components.cure_afvalbeheer.weekday import Weekday


def test_opening_hours():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    hours = parser.opening_hours()

    assert len(hours) == 7
    assert hours[0].day is Weekday.MONDAY
    assert hours[-2].day is Weekday.SATURDAY
    assert hours[-1].day is Weekday.HOLIDAY
