from datetime import date

import pytest

from custom_components.cure_afvalbeheer.notices import (
    parse_adjusted_hours,
    parse_closing_days,
    parse_closure_notice,
    parse_dated_list,
    parse_explicit_closure_date,
    parse_heat_protocol_notice,
    parse_relative_date_range,
    parse_relative_end_date,
    parse_time_range,
)

# Real text captured live from cure-afvalbeheer.nl on 2026-07-17.
_HEAT_PROTOCOL_HEADING = (
    "Hitteprotocol update! Tot en met donderdag 16 juli gewijzigde "
    "openingstijden op de milieustraten: geopend van 08:00 tot 14:00"
)

# The same announcement as Cure worded it a month later: a period written
# out with both of its ends, and "t/m" instead of "tot en met".
_HEAT_PROTOCOL_RANGE_HEADING = (
    "Let op! Hitteprotocol van 13 t/m 15 Augustus! Gewijzigde "
    "openingstijden milieustraten van 08:00 tot 14:00."
)

# The news item that same banner links to, which words it differently again.
_HEAT_PROTOCOL_NEWS_ITEM = (
    "Hitteprotocol! 13 tot en met 15 Augustus aangepaste openingstijden "
    "(08:00 - 14:00) op onze milieustraten"
)

_EINDHOVEN_CLOSURE_HEADING = "Let op! Lodewijkstraat wordt verbouwd"
_EINDHOVEN_CLOSURE_BODY = (
    "Let op! Lodewijkstraat wordt verbouwd Kijk voor alle informatie over onze "
    "verbouwing op deze pagina Kom naar onze milieustraat in Acht. Achtseweg "
    "Noord 41, 5651 GG Eindhoven Datum sluiting: 30-11-2025 Attention! "
    "Lodewijkstraat will be undergoing renovations!"
)

_VALKENSWAARD_CLOSURE_HEADING = (
    "Let op! Milieustraat Valkenswaard dicht i.v.m. werkzaamheden."
)
_VALKENSWAARD_CLOSURE_BODY = (
    "Let op! Milieustraat Valkenswaard dicht i.v.m. werkzaamheden. Op de "
    "volgende data is de milieustraat in Valkenswaard gesloten in verband met "
    "werkzaamheden: Dinsdag 30 juni 2026 Woensdag 1 juli 2026 Donderdag 2 juli "
    "2026 Bewoners van de gemeenten Valkenswaard en Heeze-Leende kunnen terecht "
    "bij de milieustraat in Geldrop."
)

_NO_NOTICE_HEADING = "Inpaktips voor vertrek"

# Real text captured live from cure-afvalbeheer.nl on 2026-08-05.
_CLOSING_DAYS_HEADING = "Sluitingsdagen 2026"
_CLOSING_DAYS_LINES = [
    "De milieustraat is gesloten op onderstaande data:",
    "Maandag 6 april 2026 (Pasen)",
    "Maandag 27 april 2026 (Koningsdag)",
    "Donderdag 14 mei 2026 (Hemelvaartsdag)",
    "Maandag 25 mei 2026 (Tweede Pinksterdag)",
    "Vrijdag 25 en zaterdag 26 december 2026 (Kerstmis)",
    "Vrijdag 1 januari 2027 (nieuwjaarsdag)",
    "Afwijkende openingstijden: op donderdag 24 december (Kerstavond) en "
    "donderdag 31 december (Oudejaarsavond) is de milieustraat geopend tot "
    "16:00 uur.",
    "Ben op tijd. Heb je te veel afval bij waardoor je de openingstijd "
    "overschrijdt, kan toegang worden geweigerd. De poortmedewerker oordeelt "
    "hierover.",
    "Zorg ervoor dat je de Cure milieupas bij hebt. Zonder Cure milieupas is "
    "toegang tot de milieustraat niet mogelijk.",
]

# The same block as Cure worded it before the 2025 website rebuild: the
# holiday name comes first, the weekday is missing and so is the year.
_OLD_CLOSING_DAYS_HEADING = "Sluitingsdagen 2024"
_OLD_CLOSING_DAYS_LINES = [
    "De milieustraat is gesloten op onderstaande data:",
    "2e Paasdag, 1 april",
    "Koningsdag, 27 april",
    "1e Kerstdag, 25 december",
    "1 januari 2025",
    "Op Kerstavond, dinsdag 24 december, én Oudjaarsavond, dinsdag 31 "
    "december, sluiten de milieustraten om 16 uur.",
]


def test_parse_time_range_with_tot():
    assert parse_time_range("geopend van 08:00 tot 14:00") == ("08:00", "14:00")


def test_parse_time_range_with_dash():
    assert parse_time_range("aangepaste openingstijden (08:00 - 14:00)") == (
        "08:00",
        "14:00",
    )


def test_parse_time_range_returns_none_without_match():
    assert parse_time_range("geen tijden hier") is None


def test_parse_relative_end_date():
    result = parse_relative_end_date(_HEAT_PROTOCOL_HEADING, date(2026, 7, 10))

    assert result == date(2026, 7, 16)


def test_parse_relative_end_date_rolls_over_to_next_year():
    # "16 juli" relative to a "today" far past it (>30 days) should roll
    # forward to next year rather than being treated as long overdue.
    result = parse_relative_end_date(_HEAT_PROTOCOL_HEADING, date(2026, 12, 1))

    assert result == date(2027, 7, 16)


def test_parse_relative_end_date_reads_a_slash_range():
    result = parse_relative_end_date(_HEAT_PROTOCOL_RANGE_HEADING, date(2026, 8, 14))

    assert result == date(2026, 8, 15)


def test_parse_relative_date_range_reads_both_ends():
    assert parse_relative_date_range(
        _HEAT_PROTOCOL_RANGE_HEADING, date(2026, 8, 14)
    ) == (date(2026, 8, 13), date(2026, 8, 15))


def test_parse_relative_date_range_reads_a_written_out_range():
    assert parse_relative_date_range(_HEAT_PROTOCOL_NEWS_ITEM, date(2026, 8, 14)) == (
        date(2026, 8, 13),
        date(2026, 8, 15),
    )


def test_parse_relative_date_range_without_a_start_date():
    assert parse_relative_date_range(_HEAT_PROTOCOL_HEADING, date(2026, 7, 10)) == (
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
    assert parse_explicit_closure_date(_EINDHOVEN_CLOSURE_BODY) == date(2025, 11, 30)


def test_parse_dated_list():
    result = parse_dated_list(_VALKENSWAARD_CLOSURE_BODY)

    assert result == [
        date(2026, 6, 30),
        date(2026, 7, 1),
        date(2026, 7, 2),
    ]


def test_parse_heat_protocol_notice():
    notice = parse_heat_protocol_notice(_HEAT_PROTOCOL_HEADING, date(2026, 7, 10))

    assert notice is not None
    assert notice.reason == "hitteprotocol"
    assert notice.closed is False
    assert notice.opens == "08:00"
    assert notice.closes == "14:00"
    assert notice.ends == date(2026, 7, 16)


def test_parse_heat_protocol_notice_reads_a_slash_range():
    notice = parse_heat_protocol_notice(_HEAT_PROTOCOL_RANGE_HEADING, date(2026, 8, 14))

    assert notice is not None
    assert notice.reason == "hitteprotocol"
    assert notice.closed is False
    assert notice.opens == "08:00"
    assert notice.closes == "14:00"
    assert notice.starts == date(2026, 8, 13)
    assert notice.ends == date(2026, 8, 15)


def test_parse_heat_protocol_notice_reads_the_news_item_wording():
    notice = parse_heat_protocol_notice(_HEAT_PROTOCOL_NEWS_ITEM, date(2026, 8, 14))

    assert notice is not None
    assert notice.opens == "08:00"
    assert notice.closes == "14:00"
    assert notice.starts == date(2026, 8, 13)
    assert notice.ends == date(2026, 8, 15)


def test_parse_heat_protocol_notice_does_not_start_before_its_period():
    """A banner put up in advance adjusts nothing until the heat arrives."""

    notice = parse_heat_protocol_notice(_HEAT_PROTOCOL_RANGE_HEADING, date(2026, 8, 10))

    assert notice is not None
    assert notice.starts == date(2026, 8, 13)


def test_parse_heat_protocol_notice_ignores_a_stale_banner():
    """A banner left standing reads as next year's, which is months of
    adjusted hours rather than a spell of hot days."""

    assert parse_heat_protocol_notice(_HEAT_PROTOCOL_HEADING, date(2026, 12, 1)) is None


def test_parse_heat_protocol_notice_ignores_unrelated_heading():
    assert parse_heat_protocol_notice(_NO_NOTICE_HEADING, date(2026, 7, 10)) is None


def test_parse_closure_notice_eindhoven_explicit_date_in_past():
    notice = parse_closure_notice(
        _EINDHOVEN_CLOSURE_HEADING, _EINDHOVEN_CLOSURE_BODY, date(2026, 7, 17)
    )

    assert notice is not None
    assert notice.reason == "verbouwing"
    assert notice.closed is True
    assert notice.starts is None  # already started, no lower bound needed
    assert notice.ends is None  # indefinite, no announced reopening
    assert notice.dates is None


def test_parse_closure_notice_explicit_date_in_future():
    notice = parse_closure_notice(
        "Let op! Milieustraat wordt verbouwd",
        "Datum sluiting: 01-01-2027",
        date(2026, 7, 17),
    )

    assert notice is not None
    assert notice.starts == date(2027, 1, 1)


def test_parse_closure_notice_valkenswaard_dated_list():
    notice = parse_closure_notice(
        _VALKENSWAARD_CLOSURE_HEADING, _VALKENSWAARD_CLOSURE_BODY, date(2026, 7, 17)
    )

    assert notice is not None
    assert notice.reason == "werkzaamheden"
    assert notice.closed is True
    assert notice.dates == [
        date(2026, 6, 30),
        date(2026, 7, 1),
        date(2026, 7, 2),
    ]


def test_parse_closure_notice_ignores_unrelated_heading():
    assert (
        parse_closure_notice(_NO_NOTICE_HEADING, "wat tekst", date(2026, 7, 17)) is None
    )


def test_parse_closure_notice_returns_none_without_parsable_date():
    notice = parse_closure_notice(
        "Let op! Iets is anders", "Geen datum hier te vinden.", date(2026, 7, 17)
    )

    assert notice is None


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


def test_parse_closing_days_reads_every_listed_day():
    notices = parse_closing_days(
        _CLOSING_DAYS_HEADING, _CLOSING_DAYS_LINES, date(2026, 8, 5)
    )

    closures = [notice for notice in notices if notice.closed]

    assert [notice.dates for notice in closures] == [
        [date(2026, 4, 6)],
        [date(2026, 4, 27)],
        [date(2026, 5, 14)],
        [date(2026, 5, 25)],
        [date(2026, 12, 25), date(2026, 12, 26)],  # "25 en zaterdag 26 december"
        [date(2027, 1, 1)],
    ]

    assert {notice.reason for notice in closures} == {"sluitingsdag"}


def test_parse_closing_days_reads_the_adjusted_closing_time():
    notices = parse_closing_days(
        _CLOSING_DAYS_HEADING, _CLOSING_DAYS_LINES, date(2026, 8, 5)
    )

    adjusted = [notice for notice in notices if not notice.closed]

    assert len(adjusted) == 1
    assert adjusted[0].reason == "aangepaste openingstijden"
    assert adjusted[0].closes == "16:00"
    assert adjusted[0].opens is None  # keeps the regular opening time
    # The year is missing from the sentence and taken from the heading.
    assert adjusted[0].dates == [date(2026, 12, 24), date(2026, 12, 31)]


def test_parse_closing_days_ignores_lines_without_a_date():
    notices = parse_closing_days(
        _CLOSING_DAYS_HEADING, _CLOSING_DAYS_LINES, date(2026, 8, 5)
    )

    assert len(notices) == 7  # six closing days plus one adjusted closing time


def test_parse_closing_days_handles_the_pre_2025_wording():
    """Weekday-less entries, the holiday name first and no year at all."""

    notices = parse_closing_days(
        _OLD_CLOSING_DAYS_HEADING, _OLD_CLOSING_DAYS_LINES, date(2025, 6, 1)
    )

    assert [notice.dates for notice in notices] == [
        [date(2024, 4, 1)],
        [date(2024, 4, 27)],
        [date(2024, 12, 25)],
        [date(2025, 1, 1)],  # the only entry that spells out its own year
        [date(2024, 12, 24), date(2024, 12, 31)],
    ]

    assert notices[-1].closes == "16:00"


def test_parse_closing_days_expands_a_range():
    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Van 23 t/m 27 december 2026 gesloten"],
        date(2026, 8, 5),
    )

    assert notices[0].dates == [
        date(2026, 12, 23),
        date(2026, 12, 24),
        date(2026, 12, 25),
        date(2026, 12, 26),
        date(2026, 12, 27),
    ]


def test_parse_closing_days_reads_a_line_adjusting_both_sides():
    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Op donderdag 24 december geopend van 10:00 tot 16:00 uur"],
        date(2026, 8, 5),
    )

    assert notices[0].closed is False
    assert notices[0].opens == "10:00"
    assert notices[0].closes == "16:00"
    assert notices[0].dates == [date(2026, 12, 24)]


def test_parse_closing_days_reads_a_line_adjusting_the_opening_only():
    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Op donderdag 24 december zijn we pas vanaf 10:00 uur open"],
        date(2026, 8, 5),
    )

    assert notices[0].closed is False
    assert notices[0].opens == "10:00"
    assert notices[0].closes is None  # the regular closing time stands


def test_parse_closing_days_skips_an_open_day_whose_times_are_unreadable():
    """Calling such a day closed would state the opposite of the line."""

    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Op donderdag 24 december gaan we later open"],
        date(2026, 8, 5),
    )

    assert notices == []


def test_parse_closing_days_still_closes_a_day_that_says_it_is_closed():
    """An open-sounding word must not rescue a line that says "gesloten"."""

    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Vrijdag 25 december 2026 gesloten, milieustraat Acht is wel open"],
        date(2026, 8, 5),
    )

    assert notices[0].closed is True
    assert notices[0].dates == [date(2026, 12, 25)]


def test_parse_closing_days_expands_a_range_across_a_month_boundary():
    """Only the two ends are written out; the days between are implied."""

    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Gesloten van 30 december 2026 tot en met 2 januari 2027"],
        date(2026, 8, 5),
    )

    assert notices[0].dates == [
        date(2026, 12, 30),
        date(2026, 12, 31),
        date(2027, 1, 1),
        date(2027, 1, 2),
    ]


def test_parse_closing_days_reads_a_range_crossing_new_year_without_a_year():
    """The end of such a range is a year on from the heading's year."""

    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Gesloten van 30 december tot en met 2 januari"],
        date(2026, 8, 5),
    )

    assert notices[0].dates == [
        date(2026, 12, 30),
        date(2026, 12, 31),
        date(2027, 1, 1),
        date(2027, 1, 2),
    ]


def test_parse_closing_days_keeps_only_the_ends_of_an_implausible_range():
    """A closing days list is days off, never a closure of months."""

    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Gesloten van 1 januari tot en met 31 december 2026"],
        date(2026, 8, 5),
    )

    assert notices[0].dates == [date(2026, 1, 1), date(2026, 12, 31)]


def test_parse_closing_days_does_not_read_a_hyphenated_name_as_a_range():
    """Municipality names such as Geldrop-Mierlo carry a hyphen of their own."""

    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["1 mei Geldrop-Mierlo en 2 juni 2026"],
        date(2026, 8, 5),
    )

    assert notices[0].dates == [date(2026, 5, 1), date(2026, 6, 2)]


def test_parse_closing_days_infers_the_year_without_one_anywhere():
    """No year in the entry and none in the heading: read it as upcoming."""

    notices = parse_closing_days("Sluitingsdagen", ["25 december"], date(2026, 8, 5))

    assert notices[0].dates == [date(2026, 12, 25)]


def test_parse_closing_days_rolls_a_bare_date_over_into_next_year():
    notices = parse_closing_days("Sluitingsdagen", ["1 januari"], date(2026, 8, 5))

    assert notices[0].dates == [date(2027, 1, 1)]


def test_parse_closing_days_returns_nothing_for_an_unparsable_block():
    assert (
        parse_closing_days("Sluitingsdagen 2026", ["Zie de kalender"], date.today())
        == []
    )


def test_parse_closing_days_skips_an_impossible_date():
    assert (
        parse_closing_days("Sluitingsdagen 2026", ["30 februari 2026"], date.today())
        == []
    )


# --- Spellings Cure has not used yet, but readily could ---


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("Maandag 6 april 2026 (Pasen)", date(2026, 4, 6)),
        ("6 apr 2026", date(2026, 4, 6)),
        ("Maandag 6 apr. 2026", date(2026, 4, 6)),
        ("06-04-2026", date(2026, 4, 6)),
        ("6-4-2026 (Pasen)", date(2026, 4, 6)),
        ("06/04/2026", date(2026, 4, 6)),
    ],
)
def test_parse_closing_days_reads_a_date_however_it_is_written(line, expected):
    notices = parse_closing_days("Sluitingsdagen 2026", [line], date(2026, 1, 1))

    assert notices[0].dates == [expected]
    assert notices[0].closed is True


def test_parse_closing_days_does_not_read_a_number_pair_as_a_date():
    """A numeric date needs its year in full, or a house number would do."""

    assert parse_closing_days("Sluitingsdagen 2026", ["6-4-26"], date(2026, 1, 1)) == []


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


def test_parse_closure_notice_reads_a_period():
    notice = parse_closure_notice(
        "Let op! Milieustraat dicht i.v.m. werkzaamheden.",
        "De milieustraat is gesloten van 30 juni tot en met 2 juli.",
        date(2026, 6, 1),
    )

    assert notice is not None
    assert notice.closed is True
    assert notice.starts == date(2026, 6, 30)
    assert notice.ends == date(2026, 7, 2)


@pytest.mark.parametrize(
    "heading",
    [
        "Let op! Milieustraat dicht i.v.m. werkzaamheden.",
        "Let op: Milieustraat dicht i.v.m. werkzaamheden.",
        "LET OP! Milieustraat dicht i.v.m. werkzaamheden.",
        "Let op, milieustraat dicht i.v.m. werkzaamheden.",
        "Letop! Milieustraat dicht i.v.m. werkzaamheden.",
    ],
)
def test_parse_closure_notice_however_the_heading_is_punctuated(heading):
    notice = parse_closure_notice(heading, "Dinsdag 30 juni 2026", date(2026, 6, 1))

    assert notice is not None
    assert notice.dates == [date(2026, 6, 30)]


def test_parse_closure_notice_ignores_a_heading_without_the_wording():
    assert (
        parse_closure_notice(
            "Inpaktips voor vertrek", "Dinsdag 30 juni 2026", date(2026, 6, 1)
        )
        is None
    )


@pytest.mark.parametrize(
    ("text", "starts", "ends", "opens", "closes"),
    [
        (
            "Hitteprotocol van 13 tot 15 augustus: geopend van 08.00 tot 14.00 uur",
            date(2026, 8, 13),
            date(2026, 8, 15),
            "08:00",
            "14:00",
        ),
        (
            "Hitte-protocol van 13 t/m 15 augustus: geopend van 8:00 tot 14:00",
            date(2026, 8, 13),
            date(2026, 8, 15),
            "08:00",
            "14:00",
        ),
        (
            "Hitteprotocol! Vandaag sluiten onze milieustraten om 14:00 uur",
            date(2026, 8, 14),
            date(2026, 8, 14),
            None,
            "14:00",
        ),
        (
            "Hitteprotocol: milieustraten vandaag geopend tot 14:00 uur",
            date(2026, 8, 14),
            date(2026, 8, 14),
            None,
            "14:00",
        ),
        (
            "Hitteprotocol 13 augustus: geopend van 08:00 tot 14:00 uur",
            date(2026, 8, 13),
            date(2026, 8, 13),
            "08:00",
            "14:00",
        ),
        (
            "Vanwege de hitte zijn de milieustraten van 13 t/m 15 augustus "
            "geopend van 08:00 tot 14:00",
            date(2026, 8, 13),
            date(2026, 8, 15),
            "08:00",
            "14:00",
        ),
    ],
)
def test_parse_heat_protocol_notice_however_it_is_written(
    text, starts, ends, opens, closes
):
    notice = parse_heat_protocol_notice(text, date(2026, 8, 14))

    assert notice is not None
    assert notice.starts == starts
    assert notice.ends == ends
    assert notice.opens == opens
    assert notice.closes == closes


@pytest.mark.parametrize(
    "text",
    [
        "Hitteprotocol! Kijk op de website voor de aangepaste openingstijden",
        "Hittegolf op komst: 5 tips om je afval koel te bewaren",
        "Hitteprotocol van 13 t/m 15 augustus",
    ],
)
def test_parse_heat_protocol_notice_needs_both_a_period_and_a_time(text):
    """Half an announcement is not one: nothing beats a wrong guess."""

    assert parse_heat_protocol_notice(text, date(2026, 8, 14)) is None


def test_parse_time_range_with_dots():
    assert parse_time_range("geopend van 08.00 tot 14.00 uur") == ("08:00", "14:00")


def test_parse_time_range_pads_a_single_digit_hour():
    assert parse_time_range("geopend van 8:00 tot 14:00") == ("08:00", "14:00")


def test_parse_heat_protocol_notice_ignores_vandaag_in_archived_text():
    """A news item stays on the page for months; its "vandaag" is not today."""

    text = "Hitteprotocol! Vandaag geopend van 08:00 tot 14:00 uur"

    assert parse_heat_protocol_notice(text, date(2026, 8, 14)) is not None
    assert parse_heat_protocol_notice(text, date(2026, 8, 14), current=False) is None
