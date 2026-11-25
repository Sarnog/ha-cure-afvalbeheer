"""Tests for parsing/times.py: Clock times and adjusted hours in free text."""

from custom_components.cure_afvalbeheer.parsing.times import (
    parse_adjusted_hours,
    parse_time_range,
)


def test_parse_time_range_with_tot():
    assert parse_time_range("geopend van 08:00 tot 14:00") == ("08:00", "14:00")


def test_parse_time_range_with_dash():
    assert parse_time_range("aangepaste openingstijden (08:00 - 14:00)") == (
        "08:00",
        "14:00",
    )


def test_parse_time_range_returns_none_without_match():
    assert parse_time_range("geen tijden hier") is None


def test_parse_adjusted_hours_reads_a_closing_time_only():
    assert parse_adjusted_hours("is de milieustraat geopend tot 16:00 uur") == (
        None,
        "16:00",
    )


def test_parse_adjusted_hours_reads_a_closing_time_without_minutes():
    assert parse_adjusted_hours("sluiten de milieustraten om 16 uur") == (None, "16:00")


def test_parse_adjusted_hours_reads_an_opening_time_only():
    assert parse_adjusted_hours("zijn we pas vanaf 10:00 uur open") == ("10:00", None)


def test_parse_adjusted_hours_reads_both_sides():
    assert parse_adjusted_hours(
        "is de milieustraat geopend van 10:00 tot 16:00 uur"
    ) == (
        "10:00",
        "16:00",
    )


def test_parse_adjusted_hours_reads_a_later_closing_time():
    """Any combination counts - a range is not assumed to be a shortening."""

    assert parse_adjusted_hours("geopend van 10:00 tot 18:00 uur") == ("10:00", "18:00")


def test_parse_adjusted_hours_reads_a_range_of_whole_hours():
    assert parse_adjusted_hours("geopend van 10 tot 16 uur") == ("10:00", "16:00")


def test_parse_adjusted_hours_ignores_a_regular_opening_hours_line():
    assert parse_adjusted_hours("Maandag: 08:30 tot 17:00") == (None, None)


def test_parse_adjusted_hours_does_not_read_a_date_as_a_time():
    """ "vanaf 6 april" is a date; only "uur" or minutes make it a time."""

    assert parse_adjusted_hours("Gesloten vanaf 6 april") == (None, None)


def test_parse_adjusted_hours_rejects_an_impossible_time():
    assert parse_adjusted_hours("geopend tot 45:99 uur") == (None, None)


def test_parse_time_range_with_dots():
    assert parse_time_range("geopend van 08.00 tot 14.00 uur") == ("08:00", "14:00")


def test_parse_time_range_pads_a_single_digit_hour():
    assert parse_time_range("geopend van 8:00 tot 14:00") == ("08:00", "14:00")
