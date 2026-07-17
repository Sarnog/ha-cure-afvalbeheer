# Architecture

## Overview

The project is divided into several layers.

```
Internet
    │
    ▼
HTTP Client
    │
    ▼
Selectors
    │
    ▼
Parser ──uses──> notices.py (free-text deviation parsing)
    │
    ▼
Models (incl. Notice)
    │
    ▼
Coordinator
    │
    ▼
schedule.py (resolve_day / resolve_upcoming: applies Notices to the
             regular weekly schedule)
    │
    ▼
Entities
```

Each layer has exactly one responsibility.

---

# HTTP Client

Responsible only for downloading web pages.

No parsing.

No Home Assistant code.

---

# Selectors

Responsible for locating HTML elements.

Uses BeautifulSoup.

Contains all HTML selectors.

No Home Assistant imports.

---

# Parser

Responsible for converting HTML elements into Python models.

Must never contain CSS selectors.

Uses only functions from `selectors.py`.

---

# Models

Contains dataclasses only.

No parsing logic.

No Home Assistant code.

---

# Coordinator

Uses Home Assistant's `DataUpdateCoordinator`.

Responsible for:

- downloading data
- caching
- update intervals
- retry logic
- error handling

---

# Entities

Entities never perform network requests.

Entities only read data from the coordinator.

---

# Notices

`notices.py` extracts temporary deviations (heat protocol, closures,
renovations) from free Dutch text found on the milieustraat page.

Contains no BeautifulSoup/HTML code and no Home Assistant imports - it only
takes plain strings and returns a `Notice` (or `None` when the text does not
match a recognised pattern). `parser.py` is the only caller: it selects the
relevant heading/body text via `selectors.py` and hands it to `notices.py`.

---

# Schedule

`schedule.py` resolves the opening hours for a specific date.

`hours_for_date`/`upcoming_hours` read only the regular weekly schedule.
`resolve_day`/`resolve_upcoming` additionally apply any `Notice`s that match
that date and location, producing a `ResolvedDay` with a `reason` field so
entities can show *why* a day deviates from the regular schedule.

---

# Diagnostics

`diagnostics.py` exposes `async_get_config_entry_diagnostics`, Home
Assistant's standard downloadable-diagnostics entry point (auto-detected, no
manifest.json change needed). It serialises `entry.data`/`entry.options` and
the coordinator's current locations/opening hours/notices into plain, explicit
dicts - no redaction, since nothing here is more sensitive than the chosen
municipality and public opening-hours info already on the Cure website.

---

# Logging

Use `logger.py`.

Never use `print()`.

---

# Async

All network communication uses `aiohttp`.

No blocking I/O.

---

# Parser Rules

Prefer semantic HTML.

Search in this order:

1. headings
2. tables
3. semantic HTML elements
4. CSS classes (only when unavoidable)

---

# Future Extensions

Done, without changing the parser architecture:

- multiple municipalities (v0.1.0)
- temporary closures, heat protocol (v0.2.0) - parsed from the milieustraat
  page itself; no separate RSS feed turned out to be necessary
- diagnostics, configurable update interval (v0.4.0)

Still to support:

- additional sensors (see ROADMAP.md's "Toekomstideeën" for concrete ideas)