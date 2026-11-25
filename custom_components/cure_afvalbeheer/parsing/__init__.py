"""Reading the Cure website: from HTML to locations, hours and notices.

The modules are layered, each using only the ones below it:

- page: CureParser, the entry point for the rest of the integration
- locations, regular_hours, notices: one part of the page each
- selectors: finding those parts in the HTML
- hours_lines, closing_days, heat_protocol, attention: one kind of text each
- dates, times: dates and clock times as Cure writes them
"""

from .locations import location_hint_for
from .page import CureParser

__all__ = ["CureParser", "location_hint_for"]
