"""Tests for parsing/dates.py: Dates as Cure writes them in free text."""

from datetime import date

import pytest

from custom_components.cure_afvalbeheer.parsing.dates import (
    _a_month_earlier,
    _range_start,
    parse_dated_list,
    parse_effective_from,
    parse_effective_until,
    parse_explicit_closure_date,
    parse_relative_date_range,
    relative_date,
    season_covers,
)
from tests.hulp import (
    EINDHOVEN_CLOSURE_BODY,
    HEAT_PROTOCOL_HEADING,
    HEAT_PROTOCOL_NEWS_ITEM,
    HEAT_PROTOCOL_RANGE_HEADING,
    VALKENSWAARD_CLOSURE_BODY,
)


def test_parse_relative_date_range_end():
    result = parse_relative_date_range(HEAT_PROTOCOL_HEADING, date(2026, 7, 10))[1]

    assert result == date(2026, 7, 16)


def test_parse_relative_date_range_end_rolls_over_to_next_year():
    # "16 juli" relative to a "today" far past it (>30 days) should roll
    # forward to next year rather than being treated as long overdue.
    result = parse_relative_date_range(HEAT_PROTOCOL_HEADING, date(2026, 12, 1))[1]

    assert result == date(2027, 7, 16)


def test_parse_relative_date_range_end_reads_a_slash_range():
    result = parse_relative_date_range(HEAT_PROTOCOL_RANGE_HEADING, date(2026, 8, 14))[
        1
    ]

    assert result == date(2026, 8, 15)


def test_parse_relative_date_range_reads_both_ends():
    assert parse_relative_date_range(
        HEAT_PROTOCOL_RANGE_HEADING, date(2026, 8, 14)
    ) == (date(2026, 8, 13), date(2026, 8, 15))


def test_parse_relative_date_range_reads_a_written_out_range():
    assert parse_relative_date_range(HEAT_PROTOCOL_NEWS_ITEM, date(2026, 8, 14)) == (
        date(2026, 8, 13),
        date(2026, 8, 15),
    )


def test_parse_relative_date_range_without_a_start_date():
    assert parse_relative_date_range(HEAT_PROTOCOL_HEADING, date(2026, 7, 10)) == (
        None,
        date(2026, 7, 16),
    )


def test_parse_relative_date_range_reads_a_start_in_the_previous_month():
    """The month is written behind the end date only: "van 30 t/m 2 augustus"."""

    assert parse_relative_date_range(
        "Hitteprotocol van 30 t/m 2 augustus", date(2026, 7, 29)
    ) == (date(2026, 7, 30), date(2026, 8, 2))


def test_parse_relative_date_range_reads_a_start_in_the_previous_year():
    assert parse_relative_date_range(
        "Gesloten van 28 december tot en met 4 januari", date(2026, 12, 20)
    ) == (date(2026, 12, 28), date(2027, 1, 4))


def test_parse_relative_date_range_ignores_a_time_range():
    assert parse_relative_date_range(
        "De milieustraten zijn geopend van 08:00 tot 14:00 uur", date(2026, 8, 14)
    ) == (None, None)


def test_parse_relative_date_range_without_a_period():
    assert parse_relative_date_range("Inpaktips voor vertrek", date(2026, 8, 14)) == (
        None,
        None,
    )


def test_parse_explicit_closure_date():
    assert parse_explicit_closure_date(EINDHOVEN_CLOSURE_BODY) == date(2025, 11, 30)


def test_parse_dated_list():
    result = parse_dated_list(VALKENSWAARD_CLOSURE_BODY)

    assert result == [
        date(2026, 6, 30),
        date(2026, 7, 1),
        date(2026, 7, 2),
    ]


@pytest.mark.parametrize(
    "body",
    [
        "Datum sluiting: 30-11-2025",
        "Datum sluiting 30-11-2025",
        "Datum sluiting: 30/11/2025",
        "Datum van sluiting: 30-11-2025",
        "Sluitingsdatum: 30-11-2025",
        "Datum sluiting: 30 november 2025",
    ],
)
def test_parse_explicit_closure_date_however_it_is_written(body):
    assert parse_explicit_closure_date(body, date(2026, 7, 17)) == date(2025, 11, 30)


def test_parse_explicit_closure_date_ignores_a_date_further_along():
    """Only the text right behind the label counts as the closure date."""

    body = "Datum sluiting: nog niet bekend. Wij zijn geopend op 6 april 2026."

    assert parse_explicit_closure_date(body, date(2026, 1, 1)) is None


def test_parse_dated_list_without_a_year():
    result = parse_dated_list(
        "Gesloten op dinsdag 30 juni en woensdag 1 juli", date(2026, 6, 1)
    )

    assert result == [date(2026, 6, 30), date(2026, 7, 1)]


def test_parse_dated_list_reads_numeric_dates():
    result = parse_dated_list("Gesloten op 30-06-2026 en 01-07-2026", date(2026, 6, 1))

    assert result == [date(2026, 6, 30), date(2026, 7, 1)]


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 8, 14), False),
        (date(2026, 1, 14), True),
        (date(2026, 10, 1), True),
        (date(2026, 3, 31), True),
        (date(2026, 4, 1), False),
    ],
)
def test_season_covers_a_period_running_through_new_year(day, expected):
    assert season_covers("Openingstijden winter (1 oktober t/m 31 maart)", day) is (
        expected
    )


def test_season_covers_a_period_inside_one_year():
    heading = "Openingstijden zomer (1 april t/m 30 september)"

    assert season_covers(heading, date(2026, 8, 14)) is True
    assert season_covers(heading, date(2026, 1, 14)) is False


def test_season_covers_returns_none_without_a_period():
    """None is not "no": the heading says nothing about seasons at all."""

    assert season_covers("Openingstijden", date(2026, 8, 14)) is None


# --- Grenzen, gevonden met mutatietests (mutmut) ---------------------------


def test_season_covers_a_single_day_only_on_that_day():
    assert season_covers("1 april t/m 1 april", date(2026, 4, 1)) is True
    assert season_covers("1 april t/m 1 april", date(2026, 7, 1)) is False


def test_season_covers_includes_both_ends():
    text = "1 april t/m 30 september"

    assert season_covers(text, date(2026, 4, 1)) is True
    assert season_covers(text, date(2026, 9, 30)) is True


def test_relative_date_keeps_a_date_exactly_30_days_ago():
    assert relative_date(1, 7, date(2026, 7, 31)) == date(2026, 7, 1)


def test_relative_date_rolls_over_a_date_31_days_ago():
    assert relative_date(1, 7, date(2026, 8, 1)) == date(2027, 7, 1)


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 3, 15), date(2026, 2, 15)),
        (date(2026, 2, 15), date(2026, 1, 15)),
        (date(2026, 1, 15), date(2025, 12, 15)),
        (date(2026, 3, 31), None),
    ],
)
def test_a_month_earlier(day, expected):
    assert _a_month_earlier(day) == expected


def test_range_start_on_the_end_date_itself():
    assert _range_start(15, 8, date(2026, 8, 15), False) == date(2026, 8, 15)


def test_range_start_a_month_earlier_may_land_on_the_end_date():
    assert _range_start(2, 9, date(2026, 8, 2), False) == date(2026, 8, 2)


def test_range_start_without_a_month_earlier_counterpart():
    """31 March has no 31 February to fall back to."""

    assert _range_start(31, 3, date(2026, 3, 2), False) is None


def test_parse_relative_date_range_uses_a_written_start_month():
    assert parse_relative_date_range(
        "van 20 juni t/m 5 augustus", date(2026, 6, 1)
    ) == (date(2026, 6, 20), date(2026, 8, 5))


def test_parse_explicit_closure_date_reads_words_against_today():
    assert parse_explicit_closure_date(
        "Datum sluiting: 5 januari", date(2020, 12, 20)
    ) == date(2021, 1, 5)


def test_parse_dated_list_without_today_uses_the_system_date():
    result = parse_dated_list("Gesloten op maandag 5 januari")

    assert len(result) == 1
    assert result[0].year in (date.today().year, date.today().year + 1)


def test_parse_dated_list_skips_an_impossible_date_and_reads_on():
    text = "31-02-2026, 03-03-2026, dinsdag 31 februari 2026, woensdag 4 maart 2026"

    assert parse_dated_list(text, date(2026, 3, 1)) == [
        date(2026, 3, 3),
        date(2026, 3, 4),
    ]


def test_parse_dated_list_lists_a_date_only_once():
    text = "04-03-2026 en woensdag 4 maart 2026"

    assert parse_dated_list(text, date(2026, 3, 1)) == [date(2026, 3, 4)]


def test_parse_effective_from_skips_a_marker_without_a_date():
    """ "per bezoek" is no date; the "vanaf" behind it still counts."""

    text = "Eén aanhanger per bezoek. Vanaf 1 december 2026 nieuwe tijden"

    assert parse_effective_from(text, date(2026, 11, 1)) == date(2026, 12, 1)


def test_parse_effective_from_reads_words_against_today():
    assert parse_effective_from("Vanaf 5 januari", date(2020, 12, 20)) == date(
        2021, 1, 5
    )


def test_parse_effective_until_reads_a_numeric_date():
    assert parse_effective_until("t/m 30-11-2026", date(2026, 11, 1)) == date(
        2026, 11, 30
    )


def test_parse_explicit_closure_date_without_today_uses_the_system_date():
    result = parse_explicit_closure_date("Datum sluiting: 5 januari")

    assert result is not None
    assert result.year in (date.today().year, date.today().year + 1)
