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