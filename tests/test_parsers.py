from custom_components.cure_afvalbeheer.parsers import (
    parse_opening_hours_line,
)


def test_parse_regular_day():
    result = parse_opening_hours_line("Maandag: 08:30 tot 17:00")

    assert result.day == "Maandag"
    assert result.opens == "08:30"
    assert result.closes == "17:00"
    assert not result.closed


def test_parse_closed_day():
    result = parse_opening_hours_line("Zon- en feestdagen: Gesloten")

    assert result.day == "Zon- en feestdagen"
    assert result.closed
    assert result.opens is None
    assert result.closes is None
