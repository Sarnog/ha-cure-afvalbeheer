"""Parser voor Cure Afvalbeheer."""

from __future__ import annotations

from bs4 import BeautifulSoup

from . import selectors
from .logger import LOGGER


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

    def parse(self) -> list:
        """Dummy parser."""

        return []

    def table_count(self) -> int:
        """Return the number of tables."""

        return len(selectors.all_tables(self._soup))

    def has_table(self) -> bool:
        """Return True if at least one table exists."""

        return selectors.first_table(self._soup) is not None
