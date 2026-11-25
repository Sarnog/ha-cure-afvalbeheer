"""Tests for parsing/heat_protocol.py: The heat protocol banner."""

from datetime import date

import pytest

from custom_components.cure_afvalbeheer.parsing.heat_protocol import (
    parse_heat_protocol_notice,
)
from tests.hulp import (
    HEAT_PROTOCOL_HEADING,
    HEAT_PROTOCOL_NEWS_ITEM,
    HEAT_PROTOCOL_RANGE_HEADING,
    NO_NOTICE_HEADING,
)


def test_parse_heat_protocol_notice():
    notice = parse_heat_protocol_notice(HEAT_PROTOCOL_HEADING, date(2026, 7, 10))

    assert notice is not None
    assert notice.reason == "hitteprotocol"
    assert notice.closed is False
    assert notice.opens == "08:00"
    assert notice.closes == "14:00"
    assert notice.ends == date(2026, 7, 16)


def test_parse_heat_protocol_notice_reads_a_slash_range():
    notice = parse_heat_protocol_notice(HEAT_PROTOCOL_RANGE_HEADING, date(2026, 8, 14))

    assert notice is not None
    assert notice.reason == "hitteprotocol"
    assert notice.closed is False
    assert notice.opens == "08:00"
    assert notice.closes == "14:00"
    assert notice.starts == date(2026, 8, 13)
    assert notice.ends == date(2026, 8, 15)


def test_parse_heat_protocol_notice_reads_the_news_item_wording():
    notice = parse_heat_protocol_notice(HEAT_PROTOCOL_NEWS_ITEM, date(2026, 8, 14))

    assert notice is not None
    assert notice.opens == "08:00"
    assert notice.closes == "14:00"
    assert notice.starts == date(2026, 8, 13)
    assert notice.ends == date(2026, 8, 15)


def test_parse_heat_protocol_notice_does_not_start_before_its_period():
    """A banner put up in advance adjusts nothing until the heat arrives."""

    notice = parse_heat_protocol_notice(HEAT_PROTOCOL_RANGE_HEADING, date(2026, 8, 10))

    assert notice is not None
    assert notice.starts == date(2026, 8, 13)


def test_parse_heat_protocol_notice_ignores_a_stale_banner():
    """A banner left standing reads as next year's, which is months of
    adjusted hours rather than a spell of hot days."""

    assert parse_heat_protocol_notice(HEAT_PROTOCOL_HEADING, date(2026, 12, 1)) is None


def test_parse_heat_protocol_notice_ignores_unrelated_heading():
    assert parse_heat_protocol_notice(NO_NOTICE_HEADING, date(2026, 7, 10)) is None


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


def test_parse_heat_protocol_notice_ignores_vandaag_in_archived_text():
    """A news item stays on the page for months; its "vandaag" is not today."""

    text = "Hitteprotocol! Vandaag geopend van 08:00 tot 14:00 uur"

    assert parse_heat_protocol_notice(text, date(2026, 8, 14)) is not None
    assert parse_heat_protocol_notice(text, date(2026, 8, 14), current=False) is None
