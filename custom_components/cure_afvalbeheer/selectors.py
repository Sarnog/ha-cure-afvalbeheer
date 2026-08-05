"""Selectors voor Cure HTML."""

from __future__ import annotations

from bs4 import BeautifulSoup
from bs4.element import Tag

_HEADING_LEVELS = ("h1", "h2", "h3", "h4")

_CLOSING_DAYS_HEADING = "sluitingsdag"


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


def section_with_heading(
    soup: BeautifulSoup,
    heading: str,
) -> Tag | None:
    """Return the section that contains the given heading.

    Matches case-insensitively, and falls back to the nearest div/article
    ancestor if there is no <section> wrapper - the heading text is the
    reliable signal, not the specific container tag Cure happens to use.
    """

    heading_lower = heading.strip().lower()

    for h2 in soup.find_all("h2"):
        text = h2.get_text(" ", strip=True)

        if text.lower() != heading_lower:
            continue

        section = h2.find_parent("section")

        if section is not None:
            return section

        return h2.find_parent(["div", "article"]) or h2.parent

    return None


def paragraphs(section: Tag) -> list[str]:
    """Return all paragraph text."""

    result: list[str] = []

    for paragraph in section.find_all("p"):
        text = paragraph.get_text(" ", strip=True)

        if text:
            result.append(text)

    return result


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
    prefix of "Milieustraten" - match on "Milieustra", the part shared by
    both, rather than an exact, municipality-specific string.
    """

    for heading in soup.find_all("h2"):
        if heading.get_text(strip=True).startswith("Adres Milieustra"):
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


def closure_notice_section(soup: BeautifulSoup) -> Tag | None:
    """Return the active closure/renovation notice block, if present.

    A municipality page can have several "textAndMedia" blocks for
    unrelated content (packing tips, etc). An active notice is the only
    one whose heading starts with "Let op!".

    Falls back to any section/div/article with such a heading if no block
    is tagged data-block="textAndMedia" - the "Let op!" heading text is
    the reliable signal, not that specific attribute.
    """

    for block in soup.find_all(attrs={"data-block": "textAndMedia"}):
        heading = block.find("h2")

        if heading is None:
            continue

        if heading.get_text(strip=True).lower().startswith("let op!"):
            return block

    for heading in soup.find_all("h2"):
        if heading.get_text(strip=True).lower().startswith("let op!"):
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


def _text_elements_after(heading: Tag) -> list[Tag]:
    """Return the paragraphs and list items belonging to heading's block.

    Cure gives this content no container of its own, so it is collected by
    walking forward from the heading until the next heading of the same or
    a higher level. The sibling walk is the precise one; the document-order
    walk is a fallback for the day the heading gets wrapped in an element
    of its own, which would leave it without any content siblings at all.
    """

    end_tags = _block_end_tags(heading)

    elements: list[Tag] = []

    for sibling in heading.next_siblings:
        if not isinstance(sibling, Tag):
            continue

        if sibling.name in end_tags:
            return elements

        if sibling.name in ("p", "li"):
            elements.append(sibling)

        elements.extend(sibling.find_all(["p", "li"]))

    if elements:
        return elements

    for element in heading.find_all_next():
        if element.name in end_tags:
            break

        if element.name in ("p", "li"):
            elements.append(element)

    return elements


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

        if not title.lower().startswith(_CLOSING_DAYS_HEADING):
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
