"""Selectors voor Cure HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

_HEADING_LEVELS = ("h1", "h2", "h3", "h4")

# How the list of days off is headed. "Sluitingsdagen" and "Sluitingsdata"
# share their opening, and the year Cure appends is left out of all of
# them. The wider alternatives are safe because the block is read line by
# line further down: a line without a date yields nothing, and one saying
# the location is open yields adjusted hours rather than a closure.
_CLOSING_DAYS_HEADINGS = ("sluitingsda", "gesloten dagen", "feestdagen")

# How an active notice announces itself. Cure varies the punctuation
# behind it ("Let op!", "Let op:", "Let op,"), so only the words count.
_ATTENTION_HEADING = re.compile(r"^let\s*op\b", re.IGNORECASE)


def page_title(soup: BeautifulSoup) -> str:
    """Return de paginatitel."""

    if soup.title:
        return soup.title.get_text(strip=True)

    return ""


def headings(soup: BeautifulSoup) -> list[Tag]:
    """Return alle headings."""

    return soup.find_all(list(_HEADING_LEVELS))


def main_content(soup: BeautifulSoup) -> Tag | None:
    """Return the main page content."""

    return soup.find("main")


def all_headings(soup: BeautifulSoup) -> list[str]:
    """Return all heading text."""

    result: list[str] = []

    for heading in headings(soup):
        text = heading.get_text(" ", strip=True)

        if text:
            result.append(text)

    return result


def blocks_under_heading(
    soup: BeautifulSoup, wanted: str, *, starting_too: bool = False
) -> list[tuple[str, list[str]]]:
    """Return every block whose heading carries the given text.

    Each block is its heading's own text plus the lines belonging to it,
    up to the next heading of the same or a higher level. That boundary is
    what keeps a list sharing one container with another (Cure puts the
    opening hours and the closing days in a single prose div) from
    bleeding into its neighbour.

    Matching is case-insensitive across every heading level. Cure adds
    words to its headings from time to time ("Openingstijden
    milieustraat"), so a heading that merely opens with the wanted text,
    or carries it somewhere inside, counts too - but only the closest kind
    of match found is returned. Exact headings beat ones that only start
    with the text, which in turn beat ones that only contain it, so a
    heading reading "Afwijkende openingstijden" never joins the real ones.

    Every match of that kind is returned rather than only the first: a
    page could carry a summer and a winter set of hours side by side, and
    picking one of those by document order would be picking at random.

    With starting_too, headings that open with the text are returned next
    to the exact ones: "Openingstijden" followed by "Openingstijden vanaf
    1 december 2026" are two sets of the same hours, not a better and a
    worse match.
    """

    target = wanted.strip().lower()

    exact: list[Tag] = []
    starts_with: list[Tag] = []
    contains: list[Tag] = []

    for heading in headings(soup):
        # The site-wide news block is about every municipality at once and
        # is read on its own; "Gewijzigde openingstijden" in its heading is
        # a message, not this page's hours.
        if heading.find_parent(attrs={"data-block": "newsBlock"}) is not None:
            continue

        text = _plain_text(heading).lower()

        if text == target:
            exact.append(heading)

        elif text.startswith(target):
            starts_with.append(heading)

        elif target in text:
            contains.append(heading)

    return [
        (
            _plain_text(heading),
            [
                line
                for element in _text_elements_after(heading)
                for line in _lines_of(element)
            ],
        )
        for heading in (
            (exact + starts_with if starting_too else exact) or starts_with or contains
        )
    ]


def location_name(soup: BeautifulSoup) -> str:
    """Return the location name."""

    heading = soup.find("h1")

    if heading is None:
        return ""

    return heading.get_text(strip=True)


def address_section(soup: BeautifulSoup) -> Tag | None:
    """Return the section containing the recycling centre addresses.

    The heading is singular ("Adres Milieustraat <Gemeente>") for
    municipalities with one location and plural ("Adres Milieustraten
    <Gemeente>") for municipalities with more than one. Dutch pluralises
    "straat" as "straten" (not "straaten"), so "Milieustraat" is not a
    prefix of "Milieustraten" - match on "milieustra", the part shared by
    both, rather than an exact, municipality-specific string. The label in
    front of it is matched on "adres" alone for the same reason ("Adres",
    "Adressen"), and the whole comparison is case-insensitive: how a
    heading is capitalised says nothing about what it is.
    """

    for heading in soup.find_all("h2"):
        text = _plain_text(heading).lower()

        if text.startswith(("adres", "locatie")) and "milieustra" in text:
            return heading.parent

    return None


def news_heading(soup: BeautifulSoup) -> str | None:
    """Return the site-wide news banner heading, if present.

    This block is identical across every municipality page - it is a
    site-wide announcement (e.g. an active heat protocol), not specific
    to one municipality.
    """

    block = soup.find(attrs={"data-block": "newsBlock"})

    if block is None:
        return None

    heading = block.find("h2")

    if heading is None:
        return None

    return heading.get_text(strip=True)


def news_item_texts(soup: BeautifulSoup) -> list[str]:
    """Return the teaser line of every item in the site-wide news block.

    The block's own heading is written by the editors and can say anything;
    the items below it are the news articles themselves, and an
    announcement the heading words loosely is often spelled out precisely
    in the item it links to. Each item carries its date and its title
    twice (once for screen readers), so only the paragraph holding the
    title is taken.
    """

    block = soup.find(attrs={"data-block": "newsBlock"})

    if block is None:
        return []

    result: list[str] = []

    for item in block.find_all("li"):
        teaser = item.find("p")

        if teaser is None:
            continue

        text = _plain_text(teaser)

        if text:
            result.append(text)

    return result


def closure_notice_section(soup: BeautifulSoup) -> Tag | None:
    """Return the active closure/renovation notice block, if present.

    A municipality page can have several "textAndMedia" blocks for
    unrelated content (packing tips, etc). An active notice is the only
    one whose heading opens with "Let op" - the punctuation Cure puts
    behind that is not part of the signal.

    Falls back to any section/div/article with such a heading if no block
    is tagged data-block="textAndMedia" - the "Let op!" heading text is
    the reliable signal, not that specific attribute. The site-wide news
    block is skipped there: its heading opens with "Let op!" just as often
    (an active heat protocol, say), and reading a heading about adjusted
    hours as a closure would state the opposite of what it says.
    """

    for block in soup.find_all(attrs={"data-block": "textAndMedia"}):
        heading = block.find("h2")

        if heading is None:
            continue

        if _ATTENTION_HEADING.match(_plain_text(heading)):
            return block

    for heading in soup.find_all("h2"):
        if not _ATTENTION_HEADING.match(_plain_text(heading)):
            continue

        if heading.find_parent(attrs={"data-block": "newsBlock"}) is not None:
            continue

        return heading.find_parent(["section", "div", "article"]) or heading.parent

    return None


def _plain_text(element: Tag) -> str:
    """Return an element's text with non-breaking spaces normalised."""

    return element.get_text(" ", strip=True).replace("\xa0", " ").strip()


def _lines_of(element: Tag) -> list[str]:
    """Return the lines of text inside one element.

    Cure sometimes writes a whole list as one paragraph broken up with
    <br> tags ("Vanaf 1 december:<br>Maandag ...<br>Zondag gesloten"),
    which would otherwise read as one long line that matches nothing. Each
    <br> therefore ends a line, just as the end of a paragraph does.
    """

    lines: list[str] = []
    parts: list[str] = []

    for node in element.descendants:
        if isinstance(node, Tag) and node.name == "br":
            lines.append(" ".join(parts))
            parts = []

        elif isinstance(node, NavigableString) and type(node) is NavigableString:
            # Only plain text counts: comments, CDATA and the like are
            # subclasses of NavigableString that a visitor never sees.
            parts.append(str(node))

    lines.append(" ".join(parts))

    return [
        " ".join(line.replace("\xa0", " ").split())
        for line in lines
        if line.replace("\xa0", " ").strip()
    ]


def _block_end_tags(heading: Tag) -> tuple[str, ...]:
    """Return the heading tags that end the block started by heading."""

    if heading.name not in _HEADING_LEVELS:
        return _HEADING_LEVELS

    return _HEADING_LEVELS[: _HEADING_LEVELS.index(heading.name) + 1]


_LINE_TAGS = ("p", "li", "tr")


def _owns_its_line(element: Tag) -> bool:
    """Return whether an element holds a line of its own.

    A <li><p>...</p></li> and a <tr><td><p>...</p></td></tr> both yield
    their text more than once; the outermost of them owns the line.
    """

    if element.name == "tr":
        return True

    return element.find_parent(["li", "tr"]) is None


def _text_elements_after(heading: Tag) -> list[Tag]:
    """Return the text elements belonging to heading's block.

    Cure gives this content no container of its own, so it is collected by
    walking forward from the heading until the next heading of the same or
    a higher level. Paragraphs, list items and table rows all count: a
    line-per-line list is content, and Cure can move it from one of those
    into another without changing a word of it. The sibling walk is the
    precise one; the document-order walk is a fallback for the day the
    heading gets wrapped in an element of its own, which would leave it
    without any content siblings at all.
    """

    end_tags = _block_end_tags(heading)

    elements: list[Tag] = []

    for sibling in heading.next_siblings:
        if not isinstance(sibling, Tag):
            continue

        if sibling.name in end_tags:
            break

        if sibling.name in _LINE_TAGS:
            elements.append(sibling)

        elements.extend(sibling.find_all(list(_LINE_TAGS)))

    if not elements:
        for element in heading.find_all_next():
            if element.name in end_tags:
                break

            if element.name in _LINE_TAGS:
                elements.append(element)

    return [element for element in elements if _owns_its_line(element)]


def closing_days_blocks(soup: BeautifulSoup) -> list[tuple[str, list[str]]]:
    """Return every "Sluitingsdagen" heading with its own text lines.

    Cure renames this heading every year ("Sluitingsdagen 2026") and does
    not always do so on time - halfway through 2025 the page still said
    2024 - so only the word itself is matched here and the year is left
    for the caller to treat as a hint rather than a fact. Around the turn
    of the year the page can carry two of these lists at once, hence every
    match is returned rather than only the first.
    """

    blocks: list[tuple[str, list[str]]] = []

    for heading in soup.find_all(list(_HEADING_LEVELS)):
        title = _plain_text(heading)

        if not title.lower().startswith(_CLOSING_DAYS_HEADINGS):
            continue

        lines: list[str] = []

        for element in _text_elements_after(heading):
            # A <li><p>...</p></li> yields both elements, which is the
            # same line twice.
            if element.name == "p" and element.find_parent("li") is not None:
                continue

            line = _plain_text(element)

            if line:
                lines.append(line)

        blocks.append((title, lines))

    return blocks


def announcement_blocks(soup: BeautifulSoup) -> list[tuple[str, list[str]]]:
    """Return every heading that talks about opening hours, with its lines.

    Cure announces a change of hours not only inside the "Openingstijden"
    block but also in a block of its own ("Vanaf 01 december 2026
    openingstijden Eindhovense milieustraten: ..."). The parser reads those
    to check the hours it found against them. The regular "Openingstijden"
    headings themselves are left out, as is the site-wide news block, whose
    heading is about every municipality at once.
    """

    blocks: list[tuple[str, list[str]]] = []

    for heading in headings(soup):
        text = _plain_text(heading)
        lower = text.lower()

        if lower.startswith("openingstijden"):
            continue

        if not re.search(r"openingstijd|geopend|\bopen\b", lower):
            continue

        if heading.find_parent(attrs={"data-block": "newsBlock"}) is not None:
            continue

        blocks.append(
            (
                text,
                [
                    line
                    for element in _text_elements_after(heading)
                    for line in _lines_of(element)
                ],
            )
        )

    return blocks


def blocks_with_heading(soup: BeautifulSoup) -> list[tuple[str, list[str]]]:
    """Return every heading on the page with the lines belonging to it.

    The site-wide news block and the page footer are left out: the first
    is read on its own, the second is navigation.
    """

    blocks: list[tuple[str, list[str]]] = []

    for heading in headings(soup):
        if heading.find_parent(attrs={"data-block": ("newsBlock", "footerContent")}):
            continue

        if heading.find_parent("footer") is not None:
            continue

        text = _plain_text(heading)

        if not text:
            continue

        blocks.append(
            (
                text,
                [
                    line
                    for element in _text_elements_after(heading)
                    for line in _lines_of(element)
                ],
            )
        )

    return blocks


# A site map card names one location ("Plattegrond Milieustraat Acht").
_SITE_MAP_HEADING = re.compile(r"^plattegrond\s+(?P<name>milieustra\w*\s+.+)$", re.I)


def site_map_location_names(soup: BeautifulSoup) -> list[str]:
    """Return the location names the site map cards mention."""

    names: list[str] = []

    for heading in headings(soup):
        match = _SITE_MAP_HEADING.match(_plain_text(heading))

        if match is not None and match.group("name") not in names:
            names.append(match.group("name"))

    return names
