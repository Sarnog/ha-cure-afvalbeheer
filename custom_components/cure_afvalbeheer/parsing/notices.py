"""The temporary deviations on a page, and the messages that would not read.

Each kind of message has a reader of its own (heat_protocol, attention,
closing_days); this module finds them on the page, hands each its text and
collects the results.
"""

from __future__ import annotations

import re
from datetime import date

from bs4 import BeautifulSoup

from ..models import Location, Notice
from . import selectors
from .attention import (
    is_attention_heading,
    mentions_deviation,
    parse_closure_notice,
)
from .closing_days import parse_closing_days
from .dates import mentions_date
from .heat_protocol import heat_protocol_unreadable, parse_heat_protocol_notice
from .locations import location_hint_for

# Headings the safety net leaves alone because another reader covers
# them in full: the regular hours, the address section, the site maps and
# the English copy of a notice.
_READ_ELSEWHERE = re.compile(
    r"^(?:openingstijden|adres|locatie|plattegrond|attention)", re.IGNORECASE
)

# Headings announcing new hours. Those hours are checked against the
# regular ones, but nothing else in the block is: a closure mentioned in
# its body would go unread.
_HOURS_ANNOUNCEMENT = re.compile(r"openingstijd|geopend|\bopen\b", re.IGNORECASE)

# What a body says when a location is shut for a while, as opposed to the
# "Zondag gesloten" every list of hours ends with.
_CLOSURE_WORDING = re.compile(
    r"verbouw|sluiting|toegankelijk|heropen|\bdicht\b|storing|werkzaamheden",
    re.IGNORECASE,
)


def _unread_message(heading: str, lines: list[str]) -> bool:
    """Return whether a block nobody reads talks about a dated change.

    A heading announcing new hours only counts when its body talks about
    a closure: the hours themselves are read already.
    """

    if _READ_ELSEWHERE.search(heading):
        return False

    if _HOURS_ANNOUNCEMENT.search(heading):
        flagged = _CLOSURE_WORDING.search(" ".join(lines)) is not None
    else:
        flagged = mentions_deviation(heading)

    return flagged and mentions_date(" ".join([heading, *lines]))


def heat_protocol_notice(soup: BeautifulSoup, today: date) -> Notice | None:
    """Parse the site-wide heat protocol announcement, if present.

    Both the news block's heading and the news items below it are
    tried, in that order. The heading is the announcement Cure puts in
    front of every visitor, but it is free-form editorial text, while
    the item it links to words the same period more consistently - so
    one reads what the other happens to leave unreadable.

    Only the heading counts as current. The items below it are the
    news archive: they stay on the page for months, so an item saying
    "vandaag" is not saying anything about today.
    """

    heading = selectors.news_heading(soup)

    candidates: list[tuple[str, bool]] = [(heading, True)] if heading else []

    candidates += [(text, False) for text in selectors.news_item_texts(soup)]

    for text, current in candidates:
        notice = parse_heat_protocol_notice(text, today, current=current)

        if notice is not None:
            return notice

    return None


def read_notices(
    soup: BeautifulSoup, locations: list[Location], today: date
) -> tuple[list[Notice], list[str]]:
    """Parse the deviations, and list every message that would not read.

    Each kind of message is read as before. What is new is that a
    message which clearly is one (a "Let op" block, a heat protocol
    banner, a dated closing day) but yields nothing is reported rather
    than skipped. A message that has simply expired is not reported:
    that is the page being out of date, not the parser.

    Last, every other heading on the page that talks about closing or
    changed hours next to a date is reported too. That is the safety
    net for a layout change: a notice Cure moves into a block of a
    new kind would otherwise vanish from the sensors without a trace.
    """

    result: list[Notice] = []
    warnings: list[str] = []

    # Headings handled by one of the readers below; the safety net at
    # the end leaves those alone.
    handled: set[str] = set()

    heat_protocol = heat_protocol_notice(soup, today)

    if heat_protocol is not None:
        result.append(heat_protocol)

    news = selectors.news_heading(soup)

    if news:
        handled.add(news)

        if heat_protocol is None and heat_protocol_unreadable(news, today):
            warnings.append(f"Hitteprotocol niet leesbaar: {news}")

        elif (
            "hitte" not in news.lower()
            and mentions_deviation(news)
            and mentions_date(news)
        ):
            warnings.append(f"Bericht niet verwerkt: {news}")

    closure_section = selectors.closure_notice_section(soup)

    if closure_section is not None:
        closure_heading = closure_section.find("h2")

        if closure_heading is not None:
            # A space between the pieces, so "Let op! <span>Acht</span>"
            # does not come out as "Let op!Acht".
            closure_heading_text = closure_heading.get_text(" ", strip=True)
            body_text = closure_section.get_text(" ", strip=True)

            handled.add(closure_heading_text)

            closure = parse_closure_notice(closure_heading_text, body_text, today)

            if closure is not None:
                # The heading names the location; failing that, the
                # sentence the title was taken from.
                closure.location_hint = location_hint_for(
                    closure_heading_text, locations
                ) or location_hint_for(closure.title, locations)

            if closure is None or (
                closure.location_hint is None
                and not is_attention_heading(closure_heading_text)
            ):
                # A closure found only by its "Datum sluiting" label, with
                # no location named, would shut every location on the
                # page: reported instead.
                warnings.append(f"Mededeling niet leesbaar: {closure_heading_text}")

            else:
                result.append(closure)

    # No location hint: the closing days are listed once per
    # municipality page and apply to every recycling centre on it.
    for heading, lines in selectors.closing_days_blocks(soup):
        handled.add(heading)

        result.extend(parse_closing_days(heading, lines, today))

        for line in lines:
            if mentions_date(line) and not parse_closing_days(heading, [line], today):
                warnings.append(f"Sluitingsdag niet leesbaar: {line}")

    for heading, lines in selectors.blocks_with_heading(soup):
        if heading not in handled and _unread_message(heading, lines):
            warnings.append(f"Bericht niet verwerkt: {heading}")

    return result, warnings
