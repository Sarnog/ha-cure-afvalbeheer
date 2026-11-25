"""Parser voor Cure Afvalbeheer."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from bs4 import BeautifulSoup

from . import selectors
from .logger import LOGGER
from .models import (
    CureData,
    Location,
    Notice,
    OpeningHours,
    ScheduledHours,
)
from .notices import (
    announces_effective_date,
    heat_protocol_unreadable,
    mentions_date,
    mentions_deviation,
    parse_closing_days,
    parse_closure_notice,
    parse_effective_from,
    parse_effective_until,
    parse_heat_protocol_notice,
    season_covers,
)
from .parsers import (
    is_opening_hours_line,
    mentions_hours,
    parse_opening_hours,
)
from .weekday import Weekday


def _mentions_location(heading_lower: str, location: Location) -> bool:
    """Return whether a lower-cased heading names this location."""

    name = location.name.removeprefix("Milieustraat ").strip().lower()

    if not name:
        return False

    return re.search(rf"(?<!\w){re.escape(name)}(?!\w)", heading_lower) is not None


def location_hint_for(heading: str, locations: list[Location]) -> str | None:
    """Return the single location name mentioned in heading, if any.

    Only the heading is checked, not the full notice body: a renovation
    notice for one location often mentions another as the alternative to
    visit instead, which would otherwise be picked up as a false match.

    Matching is on whole words. Short location names are ordinary Dutch
    words too - "Acht" sits inside "achter" and "gedacht" - so a plain
    substring test would scope a municipality-wide notice to a single
    location purely on the wording of its heading.
    """

    heading_lower = heading.lower()

    matches = [
        location.name
        for location in locations
        if _mentions_location(heading_lower, location)
    ]

    if len(matches) == 1:
        return matches[0]

    return None


@dataclass(slots=True)
class _Period:
    """One set of regular hours lines as written on the page."""

    starts: date | None
    ends: date | None
    lines: list[str] = field(default_factory=list)


def _merged(
    previous: list[OpeningHours], changes: list[OpeningHours]
) -> list[OpeningHours]:
    """Return previous hours with every day that changes listed replaced."""

    by_day = {hours.day: hours for hours in previous}

    for hours in changes:
        by_day[hours.day] = hours

    return list(by_day.values())


# How far back an announced change is still compared with the hours found.
_ANNOUNCEMENT_MAX_AGE_DAYS = 31

# The colon behind a heading's introduction ("... milieustraten: Ma t/m
# vr ..."), as opposed to the one inside a time like "10:00".
_INTRODUCTION_COLON = re.compile(r"(?<!\d):(?!\d)")

# What separates the days in a one-line summary ("Ma t/m vr 10:00-17:00,
# za 09:00-17:00, zo gesloten.").
_SUMMARY_SEPARATOR = re.compile(r"[,;]|\.\s")

_DAY_NAMES_NL = {
    Weekday.MONDAY: "maandag",
    Weekday.TUESDAY: "dinsdag",
    Weekday.WEDNESDAY: "woensdag",
    Weekday.THURSDAY: "donderdag",
    Weekday.FRIDAY: "vrijdag",
    Weekday.SATURDAY: "zaterdag",
    Weekday.SUNDAY: "zondag",
    Weekday.HOLIDAY: "feestdagen",
}


def _announced_hours_lines(heading: str, lines: list[str]) -> list[str]:
    """Return the readable opening hours lines of an announcement.

    The heading can carry a summary behind a colon, and the lines below it
    spell the hours out per location; both are read.
    """

    candidates: list[str] = []

    parts = _INTRODUCTION_COLON.split(heading, maxsplit=1)

    if len(parts) == 2:
        candidates.extend(_SUMMARY_SEPARATOR.split(parts[1]))

    candidates.extend(lines)

    return [
        line.strip(" .")
        for line in candidates
        if is_opening_hours_line(line.strip(" ."))
    ]


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


def _same_hours(first: OpeningHours, second: OpeningHours) -> bool:
    """Return whether two entries say the same about their day."""

    if first.closed or second.closed:
        return first.closed == second.closed

    return (first.opens, first.closes) == (second.opens, second.closes)


def _describe(hours: OpeningHours | None) -> str:
    """Return one day's hours the way the warnings write them."""

    if hours is None:
        return "niets"

    if hours.closed:
        return "gesloten"

    return f"{hours.opens}-{hours.closes}"


class CureParser:
    """Parser voor Cure HTML-pagina's."""

    def __init__(self, html: str) -> None:
        """Initialiseer de parser."""

        LOGGER.debug("Initialising Cure HTML parser")

        self._soup = BeautifulSoup(html, "html.parser")

    def page_title(self) -> str:
        """Return the page title."""

        title = selectors.page_title(self._soup)

        LOGGER.debug("Page title: %s", title)

        return title

    def headings(self) -> list[str]:
        """Return all headings."""

        return selectors.all_headings(self._soup)

    def location_name(self) -> str:
        """Return the location name."""

        return selectors.location_name(self._soup)

    def _hours_block(self, today: date) -> tuple[str, list[str]]:
        """Return the opening hours block that applies today.

        A page carrying one block is the ordinary case. Should Cure ever
        split its hours into a summer and a winter set, the heading naming
        the months that cover today decides; picking one by document order
        would mean showing winter hours in August. When several blocks
        apply, or none names a season at all, the first is used and the
        log says so - a wrong guess about which set is current is worth
        knowing about.
        """

        # Headings carrying a start date ("Openingstijden vanaf 1 december
        # 2026") are not seasons but successive sets: _periods reads all of
        # them, so they are joined here into one block, each heading kept
        # as the line that announces its start date.
        all_blocks = selectors.blocks_under_heading(
            self._soup, "Openingstijden", starting_too=True
        )

        if len(all_blocks) > 1 and any(
            parse_effective_from(heading, today) for heading, _ in all_blocks
        ):
            # The undated heading goes first, whatever order the page
            # used: its own lines are the set before any start date, and
            # behind a dated heading they would be merged into that set.
            all_blocks.sort(
                key=lambda block: parse_effective_from(block[0], today) is not None
            )

            lines: list[str] = []

            for index, (heading, block_lines) in enumerate(all_blocks):
                if index:
                    lines.append(heading)

                lines.extend(block_lines)

            return all_blocks[0][0], lines

        blocks = selectors.blocks_under_heading(self._soup, "Openingstijden")

        if len(blocks) <= 1:
            return blocks[0] if blocks else ("", [])

        current = [block for block in blocks if season_covers(block[0], today)]

        if len(current) == 1:
            return current[0]

        LOGGER.warning(
            "Found %d opening hours blocks and could not tell which one "
            "applies today; using the first: %s",
            len(blocks),
            [heading for heading, _ in blocks],
        )

        return blocks[0]

    def _periods(self, today: date) -> tuple[list[_Period], list[str]]:
        """Split the opening hours block into sets with their start dates.

        Cure announces new regular hours inside the same block as the
        current ones: "Openingstijden tot en met 30 november 2026", the
        current lines, then "Vanaf dinsdag 1 december 2026:" followed by
        the new lines. Every line announcing a start date opens a new set;
        everything before the first one is the set that applies until
        then. The heading's own dates ("vanaf ...", "tot en met ...")
        belong to that first set.

        Lines that look like hours (a time range, a word meaning closed)
        but cannot be read are returned as warnings rather than dropped
        without a word: that silent drop is exactly how announced hours
        once went missing.
        """

        heading, lines = self._hours_block(today)

        first = _Period(
            starts=parse_effective_from(heading, today),
            ends=parse_effective_until(heading, today),
        )

        periods = [first]
        warnings: list[str] = []

        for line in lines:
            if is_opening_hours_line(line):
                periods[-1].lines.append(line)
                continue

            starts = parse_effective_from(line, today)

            if starts is not None:
                period = _Period(starts=starts, ends=parse_effective_until(line, today))
                periods.append(period)

                # "Vanaf 1 december: maandag t/m vrijdag 10:00 - 17:00"
                # puts the first line of the new set behind the date.
                _, _, rest = line.partition(":")

                if rest and is_opening_hours_line(rest):
                    period.lines.append(rest.strip())

                continue

            if announces_effective_date(line):
                warnings.append(f"Ingangsdatum niet leesbaar: {line}")

            elif mentions_hours(line):
                warnings.append(f"Regel niet leesbaar: {line}")

        return periods, warnings

    def _regular_hours(
        self, today: date
    ) -> tuple[list[OpeningHours], list[ScheduledHours], list[str]]:
        """Return today's regular hours, the announced later sets, and warnings.

        A later set only lists what it says: days it leaves out keep the
        hours of the set before it, since "Vanaf 1 januari: zaterdag
        09:00 - 15:00" changes Saturday and nothing else.
        """

        periods, warnings = self._periods(today)

        # Sets without a start date apply from the start; dated ones
        # follow in date order, whatever order the page wrote them in.
        undated = [period for period in periods if period.starts is None]
        dated = sorted(
            (period for period in periods if period.starts is not None),
            key=lambda period: period.starts,
        )

        hours: list[OpeningHours] = []
        current: list[OpeningHours] = []
        current_period: _Period | None = None
        scheduled: list[ScheduledHours] = []

        for period in undated + dated:
            if not period.lines:
                if period.starts is not None:
                    warnings.append(
                        "Geen openingstijden gevonden bij ingangsdatum "
                        f"{period.starts.strftime('%d-%m-%Y')}"
                    )

                continue

            hours = _merged(hours, parse_opening_hours(period.lines))

            if period.starts is None or period.starts <= today or not current:
                # Started already, or the page knows nothing earlier.
                current = hours
                current_period = period
            else:
                scheduled.append(ScheduledHours(starts=period.starts, hours=hours))

        # "Openingstijden tot en met 30 november" read in December, with
        # nothing that starts by today: the page itself says these hours are
        # over, so showing them is a guess. That holds just as well when a
        # later set exists but only starts after a gap.
        if (
            current_period is not None
            and current_period.ends is not None
            and current_period.ends < today
        ):
            warnings.append(
                "Openingstijden waren volgens de website geldig tot en met "
                f"{current_period.ends.strftime('%d-%m-%Y')}; voor vandaag "
                "zijn geen geldige openingstijden gevonden"
            )

        warnings.extend(self._announcement_mismatches(current, scheduled, today))

        for warning in warnings:
            LOGGER.warning("Opening hours: %s", warning)

        return current, scheduled, warnings

    def _announcement_mismatches(
        self,
        current: list[OpeningHours],
        scheduled: list[ScheduledHours],
        today: date,
    ) -> list[str]:
        """Check the hours found against announcements elsewhere on the page.

        The same change is usually written twice: in the "Openingstijden"
        block and in an announcement of its own. Reading both and comparing
        them turns a reworded or half-updated page into a warning instead of
        sensors that quietly disagree with what a visitor reads.

        Only announcements starting recently or later are checked: one from
        long ago describes hours that may have changed again since.
        """

        warnings: list[str] = []

        for heading, lines in selectors.announcement_blocks(self._soup):
            starts = parse_effective_from(heading, today)

            if starts is None or (today - starts).days > _ANNOUNCEMENT_MAX_AGE_DAYS:
                continue

            announced = parse_opening_hours(_announced_hours_lines(heading, lines))

            if not announced:
                # The heading promises hours from a date but none of them
                # could be read, so nothing can be checked.
                warnings.append(f"Aankondiging niet leesbaar: {heading}")
                continue

            expected = current

            for later in scheduled:
                if later.starts <= starts:
                    expected = later.hours

            by_day = {hours.day: hours for hours in expected}

            for hours in announced:
                found = by_day.get(hours.day)

                if found is not None and _same_hours(found, hours):
                    continue

                warnings.append(
                    f"Aankondiging vanaf {starts.strftime('%d-%m-%Y')} noemt "
                    f"{_DAY_NAMES_NL[hours.day]} {_describe(hours)}, maar de "
                    f"openingstijden zeggen {_describe(found)}"
                )

        return warnings

    def opening_hours_lines(self, today: date | None = None) -> list[str]:
        """Return only valid opening hours lines.

        Only the lines under the "Openingstijden" heading itself are
        considered: the closing days share one container with them, and a
        dated line from that list ("Zaterdag 26 december: 10:00 tot 14:00")
        would otherwise be filed as that weekday's regular hours.
        """

        if today is None:
            today = date.today()

        return [
            line for line in self._hours_block(today)[1] if is_opening_hours_line(line)
        ]

    def opening_hours(self, today: date | None = None) -> list[OpeningHours]:
        """Return the regular opening hours that apply today."""

        if today is None:
            today = date.today()

        return self._regular_hours(today)[0]

    def scheduled_hours(self, today: date | None = None) -> list[ScheduledHours]:
        """Return announced sets of regular hours that start after today."""

        if today is None:
            today = date.today()

        return self._regular_hours(today)[1]

    def hours_warnings(self, today: date | None = None) -> list[str]:
        """Return what in the opening hours section could not be read."""

        if today is None:
            today = date.today()

        return self._regular_hours(today)[2]

    def location_addresses(self) -> list[tuple[str, str]]:
        """Parse the recycling centre addresses.

        Municipalities with a single recycling centre sometimes omit the
        repeated h3 location name in the address section entirely (e.g.
        Geldrop-Mierlo has just a heading and one address paragraph, no
        h3). Fall back to the page's own h1 title as the location name
        in that case, since it is otherwise dropped silently.
        """

        return self._addresses_and_warnings()[0]

    def _addresses_and_warnings(self) -> tuple[list[tuple[str, str | None]], list[str]]:
        """Return the addresses, and what in the address section did not fit.

        A location name directly followed by the next one has no address
        of its own. It used to be dropped without a word; now it is kept
        (without an address) and reported, since a location missing from
        the sensors is just as wrong as wrong opening hours.
        """

        section = selectors.address_section(self._soup)

        if section is None:
            return [], []

        result: list[tuple[str, str | None]] = []
        warnings: list[str] = []

        current_name: str | None = None

        for element in section.find_all(["h3", "p"]):
            if element.name == "h3":
                if current_name is not None:
                    result.append((current_name, None))
                    warnings.append(f"Geen adres gevonden voor {current_name}")

                current_name = element.get_text(strip=True)

            elif element.name == "p":
                address = " ".join(element.stripped_strings)

                if not address:
                    continue

                result.append(
                    (
                        current_name or self.location_name(),
                        address,
                    )
                )

                current_name = None

        if current_name is not None:
            result.append((current_name, None))
            warnings.append(f"Geen adres gevonden voor {current_name}")

        return result, warnings

    def location_warnings(self) -> list[str]:
        """Return what suggests the locations found are not all there is.

        Besides the address section itself, the page names its locations
        elsewhere too, on the site maps ("Plattegrond Milieustraat Acht").
        A location named there but not among the addresses points at a
        layout the address section no longer matches.
        """

        addresses, warnings = self._addresses_and_warnings()

        known = {name.strip().lower() for name, _ in addresses}

        for name in selectors.site_map_location_names(self._soup):
            if name.lower() not in known:
                warnings.append(f"{name} staat op de pagina, maar niet bij de adressen")

        return warnings

    def parse_locations(self, today: date | None = None) -> list[Location]:
        """Parse all recycling centres."""

        if today is None:
            today = date.today()

        locations: list[Location] = []

        hours, scheduled, _ = self._regular_hours(today)

        for name, address in self.location_addresses():
            locations.append(
                Location(
                    name=name,
                    address=address,
                    hours=hours,
                    scheduled=scheduled,
                )
            )

        return locations

    def heat_protocol_notice(self, today: date) -> Notice | None:
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

        heading = selectors.news_heading(self._soup)

        candidates: list[tuple[str, bool]] = [(heading, True)] if heading else []

        candidates += [(text, False) for text in selectors.news_item_texts(self._soup)]

        for text, current in candidates:
            notice = parse_heat_protocol_notice(text, today, current=current)

            if notice is not None:
                return notice

        return None

    def notices(
        self,
        locations: list[Location],
        today: date | None = None,
    ) -> list[Notice]:
        """Parse temporary deviations (heat protocol, closures, closing days)."""

        if today is None:
            today = date.today()

        return self._notices_and_warnings(locations, today)[0]

    def notice_warnings(
        self,
        locations: list[Location],
        today: date | None = None,
    ) -> list[str]:
        """Return the messages on the page that could not be read."""

        if today is None:
            today = date.today()

        return self._notices_and_warnings(locations, today)[1]

    def _notices_and_warnings(
        self, locations: list[Location], today: date
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

        heat_protocol = self.heat_protocol_notice(today)

        if heat_protocol is not None:
            result.append(heat_protocol)

        news = selectors.news_heading(self._soup)

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

        closure_section = selectors.closure_notice_section(self._soup)

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
        for heading, lines in selectors.closing_days_blocks(self._soup):
            handled.add(heading)

            result.extend(parse_closing_days(heading, lines, today))

            for line in lines:
                if mentions_date(line) and not parse_closing_days(
                    heading, [line], today
                ):
                    warnings.append(f"Sluitingsdag niet leesbaar: {line}")

        for heading, lines in selectors.blocks_with_heading(self._soup):
            if heading in handled or _covered_elsewhere(heading):
                continue

            text = " ".join([heading, *lines])

            if mentions_deviation(heading) and mentions_date(text):
                warnings.append(f"Bericht niet verwerkt: {heading}")

        return result, warnings

    def parse(self, today: date | None = None) -> CureData:
        """Parse the complete page."""

        if today is None:
            today = date.today()

        locations = self.parse_locations(today)

        notices, notice_warnings = self._notices_and_warnings(locations, today)

        warnings = [
            *self.location_warnings(),
            *self.hours_warnings(today),
            *notice_warnings,
        ]

        for warning in [*self.location_warnings(), *notice_warnings]:
            LOGGER.warning("Page content: %s", warning)

        return CureData(locations=locations, notices=notices, warnings=warnings)
