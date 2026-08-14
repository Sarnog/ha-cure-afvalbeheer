"""Selectors voor Cure HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup
from bs4.element import Tag

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


def heading_with_text(soup: BeautifulSoup, wanted: str) -> Tag | None:
    """Return the heading carrying the given text, if the page has one.

    Matches case-insensitively across every heading level. Cure adds words
    to its headings from time to time ("Openingstijden milieustraat"), so
    a heading that merely opens with the wanted text, or carries it
    somewhere inside, counts too. The closest match wins: an exact heading
    beats one that only starts with it, which in turn beats one that only
    contains it - otherwise a heading reading "Afwijkende openingstijden"
    could be picked over the real one purely for standing higher up the
    page.
    """

    target = wanted.strip().lower()

    starts_with: Tag | None = None
    contains: Tag | None = None

    for heading in headings(soup):
        text = _plain_text(heading).lower()

        if text == target:
            return heading

        if starts_with is None and text.startswith(target):
            starts_with = heading

        elif contains is None and target in text:
            contains = heading

    return starts_with or contains


def lines_under_heading(soup: BeautifulSoup, wanted: str) -> list[str]:
    """Return the lines of text belonging to one heading's own block.

    The block ends where the next heading of the same or a higher level
    begins, which is what keeps a list sharing one container with another
    (Cure puts the opening hours and the closing days in a single prose
    div) from bleeding into its neighbour.
    """

    heading = heading_with_text(soup, wanted)

    if heading is None:
        return []

    return [
        text
        for text in (_plain_text(el) for el in _text_elements_after(heading))
        if text
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
