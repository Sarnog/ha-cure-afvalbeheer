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
from .attention import mentions_deviation, parse_closure_notice
from .closing_days import parse_closing_days
from .dates import mentions_date
from .heat_protocol import heat_protocol_unreadable, parse_heat_protocol_notice
from .locations import location_hint_for

# Headings the safety net leaves alone because another reader covers them:
# the regular hours, announcements checked against those, the address
# section and the house rules.
_COVERED_HEADING = re.compile(
    r"^(?:openingstijden|adres|locatie|plattegrond|attention)"
    r"|openingstijd|geopend|\bopen\b",
    re.IGNORECASE,
)


def _covered_elsewhere(heading: str) -> bool:
    """Return whether another part of the parser already reads this heading."""

    return _COVERED_HEADING.search(heading) is not None


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
            closure_heading_text = closure_heading.get_text(strip=True)
            body_text = closure_section.get_text(" ", strip=True)

            handled.add(closure_heading.get_text(" ", strip=True))

            closure = parse_closure_notice(closure_heading_text, body_text, today)

            if closure is not None:
                closure.location_hint = location_hint_for(
                    closure_heading_text, locations
                )
                result.append(closure)

            else:
                warnings.append(f"Mededeling niet leesbaar: {closure_heading_text}")

    # No location hint: the closing days are listed once per
    # municipality page and apply to every recycling centre on it.
    for heading, lines in selectors.closing_days_blocks(soup):
        handled.add(heading)

        result.extend(parse_closing_days(heading, lines, today))

        for line in lines:
            if mentions_date(line) and not parse_closing_days(heading, [line], today):
                warnings.append(f"Sluitingsdag niet leesbaar: {line}")

    for heading, lines in selectors.blocks_with_heading(soup):
        if heading in handled or _covered_elsewhere(heading):
            continue

        text = " ".join([heading, *lines])

        if mentions_deviation(heading) and mentions_date(text):
            warnings.append(f"Bericht niet verwerkt: {heading}")

    return result, warnings
