"""Selectors voor Cure HTML."""

from __future__ import annotations

from bs4 import BeautifulSoup
from bs4.element import Tag


def page_title(soup: BeautifulSoup) -> str:
    """Return de paginatitel."""

    if soup.title:
        return soup.title.get_text(strip=True)

    return ""


def headings(soup: BeautifulSoup) -> list[Tag]:
    """Return alle headings."""

    return soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
        ]
    )


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
    """Return the section that contains the given heading."""

    for h2 in soup.find_all("h2"):
        text = h2.get_text(" ", strip=True)

        if text == heading:
            return h2.find_parent("section")

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
    """

    for block in soup.find_all(attrs={"data-block": "textAndMedia"}):
        heading = block.find("h2")

        if heading is None:
            continue

        if heading.get_text(strip=True).lower().startswith("let op!"):
            return block

    return None
