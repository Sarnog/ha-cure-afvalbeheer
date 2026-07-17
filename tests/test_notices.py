from datetime import date

from custom_components.cure_afvalbeheer.notices import (
    parse_closure_notice,
    parse_dated_list,
    parse_explicit_closure_date,
    parse_heat_protocol_notice,
    parse_relative_end_date,
    parse_time_range,
)

# Real text captured live from cure-afvalbeheer.nl on 2026-07-17.
_HEAT_PROTOCOL_HEADING = (
    "Hitteprotocol update! Tot en met donderdag 16 juli gewijzigde "
    "openingstijden op de milieustraten: geopend van 08:00 tot 14:00"
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
