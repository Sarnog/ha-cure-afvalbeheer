"""Clock time helpers shared by the text parsers.

Cure writes clock times as "08:30" on the opening hours lines and as
"08.30" or "8:30" elsewhere, so every parser needs the same two things:
turn a written hour and minute into one "HH:MM" string, and reject numbers
that are not a time at all.
"""

from __future__ import annotations

# The separator between hour and minute, and the one between the two times
# of a range. Both are kept here so the parsers cannot drift apart on which
# spellings they accept.
CLOCK_SEPARATOR = r"[:.]"

RANGE_SEPARATOR = r"(?:tot en met|tot|t/m|[-–—])"


def hhmm(hour: str | int, minute: str | int | None) -> str | None:
    """Return an "HH:MM" time, or None if the numbers are not a time."""

    hours = int(hour)
    minutes = int(minute) if minute is not None else 0

    if hours > 23 or minutes > 59:
        return None

    return f"{hours:02d}:{minutes:02d}"
