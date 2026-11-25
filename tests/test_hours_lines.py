import pytest

from custom_components.cure_afvalbeheer.exceptions import ParserError
from custom_components.cure_afvalbeheer.parsing.hours_lines import (
    days_in_label,
    is_opening_hours_line,
    parse_opening_hours,
    parse_opening_hours_line,
)
from custom_components.cure_afvalbeheer.parsing.times import parse_time_range
from custom_components.cure_afvalbeheer.weekday import Weekday

_NBSP = "\xa0"


def test_parse_regular_day():
    result = parse_opening_hours_line("Maandag: 08:30 tot 17:00")

    assert len(result) == 1
    assert result[0].day is Weekday.MONDAY
    assert result[0].opens == "08:30"
    assert result[0].closes == "17:00"
    assert not result[0].closed


def test_parse_closed_day():
    result = parse_opening_hours_line("Zon- en feestdagen: Gesloten")

    assert len(result) == 1
    assert result[0].day is Weekday.HOLIDAY
    assert result[0].closed
    assert result[0].opens is None
    assert result[0].closes is None


def test_parse_closed_day_ampersand_variant():
    result = parse_opening_hours_line("Zon & Feestdagen: Gesloten")

    assert result[0].day is Weekday.HOLIDAY
    assert result[0].closed


@pytest.mark.parametrize(
    "line",
    [
        "Maandag: 08:30 tot 17:00",
        "maandag: 08:30 tot 17:00",
        "MAANDAG: 08:30 TOT 17:00",
        "Maandag: 08:30 - 17:00",
        "Maandag: 08:30 – 17:00",
        "Maandag: 08:30 t/m 17:00",
        "Maandag: 8:30 tot 17:00",
        "Maandag: 08.30 tot 17.00",
        "Maandag: van 08:30 tot 17:00 uur",
        "Maandag 08:30 tot 17:00",
        "Ma: 08:30 tot 17:00",
        f"Maandag:{_NBSP}08:30 tot 17:00",
    ],
)
def test_parse_the_same_monday_however_it_is_written(line):
    result = parse_opening_hours_line(line)

    assert is_opening_hours_line(line)
    assert len(result) == 1
    assert result[0].day is Weekday.MONDAY
    assert result[0].opens == "08:30"
    assert result[0].closes == "17:00"


@pytest.mark.parametrize(
    "line",
    [
        "Zon & Feestdagen: Gesloten",
        "Zon- en feestdagen: Gesloten",
        "Zon & feestdagen: gesloten",
        "Zondag en feestdagen: Gesloten",
        "Zon-/feestdagen: Gesloten",
        f"Zon &{_NBSP}Feestdagen: Gesloten",
        "Feestdagen: Gesloten",
    ],
)
def test_parse_the_holiday_line_however_it_is_written(line):
    result = parse_opening_hours_line(line)

    assert is_opening_hours_line(line)
    assert len(result) == 1
    assert result[0].day is Weekday.HOLIDAY
    assert result[0].closed


def test_parse_a_day_range():
    result = parse_opening_hours_line("Maandag t/m vrijdag: 13:00 tot 17:00")

    assert [hours.day for hours in result] == [
        Weekday.MONDAY,
        Weekday.TUESDAY,
        Weekday.WEDNESDAY,
        Weekday.THURSDAY,
        Weekday.FRIDAY,
    ]
    assert {hours.opens for hours in result} == {"13:00"}
    assert {hours.closes for hours in result} == {"17:00"}


def test_parse_an_abbreviated_day_range():
    result = parse_opening_hours_line("Ma t/m vr: 13:00 tot 17:00")

    assert [hours.day for hours in result] == [
        Weekday.MONDAY,
        Weekday.TUESDAY,
        Weekday.WEDNESDAY,
        Weekday.THURSDAY,
        Weekday.FRIDAY,
    ]


def test_parse_a_day_list():
    result = parse_opening_hours_line("Zaterdag en zondag: 10:00 tot 16:00")

    assert [hours.day for hours in result] == [Weekday.SATURDAY, Weekday.SUNDAY]


def test_parse_closed_with_a_reason_behind_it():
    result = parse_opening_hours_line("Woensdag: Gesloten (i.v.m. werkzaamheden)")

    assert result[0].day is Weekday.WEDNESDAY
    assert result[0].closed


def test_parse_opening_hours_flattens_every_day_it_covers():
    result = parse_opening_hours(
        [
            "Maandag t/m vrijdag: 13:00 tot 17:00",
            "Zaterdag: 10:00 tot 16:00",
            "Zon & Feestdagen: Gesloten",
        ]
    )

    assert len(result) == 7
    assert result[-1].day is Weekday.HOLIDAY


@pytest.mark.parametrize(
    "line",
    [
        "Zorg dat je op tijd bent, anders wordt toegang geweigerd.",
        "Let op: neem je milieupas mee.",
        "Maximaal 2 m3 per bezoek",
        "Openingstijden: zie hieronder",
        "Maandag: onbekend",
    ],
)
def test_lines_that_are_not_opening_hours(line):
    assert not is_opening_hours_line(line)

    with pytest.raises(ParserError):
        parse_opening_hours_line(line)


def test_parse_time_range_rejects_an_impossible_time():
    assert parse_time_range("25:00 tot 26:00") is None


def test_days_in_label_returns_nothing_for_an_unknown_label():
    assert days_in_label("Openingstijden") == []


def test_parse_opening_hours_skips_a_line_it_cannot_read():
    """One unreadable line must not take the whole update with it."""

    result = parse_opening_hours(
        [
            "Maandag: 08:30 tot 17:00",
            "Maandag: onbekend",
            "Zaterdag: 10:00 tot 16:00",
        ]
    )

    assert [hours.day for hours in result] == [Weekday.MONDAY, Weekday.SATURDAY]
