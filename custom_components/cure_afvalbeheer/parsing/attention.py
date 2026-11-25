"""The "Let op" announcements: closures and changed hours.

Cure's editors announce temporary deviations (renovations, closures,
weather) as free-text Dutch sentences and reword them freely from year to
year. The functions here extract a Notice from that text and return None
whenever the expected pattern is not found, so an unrecognised
announcement is skipped instead of producing a wrong result.
"""

from __future__ import annotations

import re
from datetime import date

from ..logger import LOGGER
from ..models import Notice
from .dates import (
    parse_dated_list,
    parse_explicit_closure_date,
    parse_relative_date_range,
)
from .times import parse_adjusted_hours

# How an active notice announces itself, the punctuation behind it being
# Cure's to vary ("Let op!", "Let op:", "Let op,").
_ATTENTION_WORDING = re.compile(r"^\s*let\s*op\b", re.IGNORECASE)

# Words for the location being shut, as opposed to a time it shuts at:
# "gesloten" describes the state it is in, "sluiten om 15:00" a time it
# closes at - and the second of those is an hours adjustment, not a
# closure.
_CLOSED_STATE = re.compile(r"\b(?:gesloten|dicht)\b", re.IGNORECASE)

# The causes Cure has named so far, each with the reason it maps to. The
# first match wins, so the more specific causes come first.
_REASON_WORDING: tuple[tuple[tuple[str, ...], str], ...] = (
    (("verbouw",), "verbouwing"),
    (("hitte",), "hitteprotocol"),
    (
        ("vorst", "gladheid", "ijzel", "sneeuw", "storm", "noodweer", "winterweer"),
        "weersomstandigheden",
    ),
    (("storing", "stroomuitval"), "storing"),
    (("werkzaamheden", "onderhoud", "asfalt"), "werkzaamheden"),
    (("staking",), "staking"),
)


def _attention_reason(text: str, *, closed: bool) -> str:
    """Return why a "Let op" notice deviates, as far as the text says.

    Cure names a cause in words rather than in a field, and reaches for a
    new one whenever a new kind of disruption comes along. Recognising the
    causes seen so far keeps the reason sensor meaningful; anything else
    falls back to a plain statement of what happens, which stays true even
    when the cause is one we have never seen.
    """

    lowered = text.lower()

    for words, reason in _REASON_WORDING:
        if any(word in lowered for word in words):
            return reason

    return "sluiting" if closed else "aangepaste openingstijden"


def parse_closure_notice(heading: str, body_text: str, today: date) -> Notice | None:
    """Parse a municipality-specific "Let op" notice, if present.

    The heading has to open with "Let op", whatever punctuation Cure puts
    behind it. What the body then says about dates is read in three ways,
    in descending order of how definite it is: the date behind a "Datum
    sluiting" label, a list of dated entries, or a period the notice runs
    for. A body naming none of those yields nothing at all.

    Such a notice need not announce a closure. Frost, a storm or anything
    else can shorten a day rather than cancel it, so a body naming opening
    or closing times yields an hours adjustment - the same way a line in
    the closing days list does. A body saying the location is shut
    ("gesloten", "dicht") is taken at its word regardless: those words
    describe the state it is in, where "sluiten om 15:00" describes a time
    it closes at.
    """

    if not _ATTENTION_WORDING.match(heading):
        return None

    combined_text = f"{heading} {body_text}"

    explicit_date = parse_explicit_closure_date(body_text, today)

    if explicit_date is not None:
        # "Datum sluiting" states a closure in so many words. Any times
        # the body mentions belong to the alternative location it points
        # visitors to, so they are not read as this one's hours.
        return Notice(
            reason=_attention_reason(combined_text, closed=True),
            title=heading,
            closed=True,
            starts=explicit_date if explicit_date > today else None,
        )

    opens, closes = parse_adjusted_hours(body_text)

    adjusted = (opens is not None or closes is not None) and not _CLOSED_STATE.search(
        combined_text
    )

    reason = _attention_reason(combined_text, closed=not adjusted)

    dated_list = parse_dated_list(body_text, today)

    if dated_list:
        return Notice(
            reason=reason,
            title=heading,
            closed=not adjusted,
            opens=opens if adjusted else None,
            closes=closes if adjusted else None,
            dates=dated_list,
        )

    starts, ends = parse_relative_date_range(body_text, today)

    if ends is not None:
        return Notice(
            reason=reason,
            title=heading,
            closed=not adjusted,
            opens=opens if adjusted else None,
            closes=closes if adjusted else None,
            starts=starts,
            ends=ends,
        )

    LOGGER.debug(
        "Found a 'Let op!' notice but could not parse a date from it: %s", heading
    )

    return None


# Words that mark a text as being about a change to when a location is
# open: anything carrying one of these next to a date is a message the
# sensors should reflect, so it must not slip by unread.
_DEVIATION_WORDING = re.compile(
    r"gesloten|\bdicht\b|sluit|verbouw|storing|hitte|afwijk|aangepast|gewijzigd"
    r"|openingstijd|geopend",
    re.IGNORECASE,
)


def mentions_deviation(text: str) -> bool:
    """Return whether a text talks about a change to the opening hours."""

    return _DEVIATION_WORDING.search(text) is not None
