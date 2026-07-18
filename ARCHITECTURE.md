🇳🇱 [Nederlands](#architectuur) | 🇬🇧 [English](#architecture)

---

# Architectuur

## Overzicht

Het project is opgedeeld in verschillende lagen.

```
Internet
    │
    ▼
HTTP-client
    │
    ▼
Selectors
    │
    ▼
Parser ──gebruikt──> notices.py (parsing van vrije-tekst-afwijkingen)
    │
    ▼
Models (incl. Notice)
    │
    ▼
Coordinator
    │
    ▼
schedule.py (resolve_day / resolve_upcoming: past Notices toe op het
             reguliere weekrooster)
    │
    ▼
Entiteiten
```

Elke laag heeft precies één verantwoordelijkheid.

---

# HTTP-client

Uitsluitend verantwoordelijk voor het downloaden van webpagina's.

Geen parsing.

Geen Home Assistant-code.

---

# Selectors

Verantwoordelijk voor het lokaliseren van HTML-elementen.

Gebruikt BeautifulSoup.

Bevat alle HTML-selectors.

Geen Home Assistant-imports.

Waar mogelijk hebben selectors een structurele fallback naast de
inhoudelijke check: als een specifieke tag/attribuut verdwijnt door een
opmaakwijziging, blijft het onderscheidende kenmerk (de kop-tekst) leidend
in plaats van meteen `None` terug te geven. Zie `location_addresses()`'s
h3-naar-h1-fallback in `parser.py`, en `section_with_heading`/
`closure_notice_section` in `selectors.py` (v0.6.0).

---

# Parser

Verantwoordelijk voor het omzetten van HTML-elementen naar Python-modellen.

Mag nooit CSS-selectors bevatten.

Gebruikt alleen functies uit `selectors.py`.

---

# Models

Bevat uitsluitend dataclasses.

Geen parslogica.

Geen Home Assistant-code.

---

# Coordinator

Gebruikt Home Assistant's `DataUpdateCoordinator`.

Verantwoordelijk voor:

- het downloaden van data
- caching
- update-intervallen
- retry-logica
- foutafhandeling

Levert een fetch geen enkele locatie op (na een verder geslaagde
HTTP-request), dan blijven de laatst bekende goede locaties staan in
plaats van overschreven te worden met niets - de repair-issue (zie
Repairs) blijft wel actief als signaal dat de locatiedata mogelijk
verouderd is. Is er nog geen eerdere goede data, dan wordt de lege data
gewoon doorgezet (v0.6.0). De meldingen (`notices`) uit diezelfde fetch
worden wél altijd gebruikt, ook als de locaties bevroren blijven -
`location_addresses()` en `notices()` gebruiken losstaande selectors, dus
een opmaakwijziging kan de één breken zonder de ander te raken (v0.6.1).
Omdat `notices()` de `location_hint` van een melding bepaalt aan de hand
van de op dát moment geparste (in dit geval lege) locatie-lijst, wordt die
hint zo nodig herberekend tegen de aangehouden locaties, anders zou een
melding die maar één milieustraat betreft per ongeluk voor alle locaties
gaan gelden (v0.6.2).

---

# Entiteiten

Entiteiten doen nooit netwerkverzoeken.

Entiteiten lezen alleen data uit de coordinator.

---

# Notices

`notices.py` haalt tijdelijke afwijkingen (hitteprotocol, sluitingen,
verbouwingen) uit vrije Nederlandse tekst op de milieustraat-pagina.

Bevat geen BeautifulSoup/HTML-code en geen Home Assistant-imports - het
neemt alleen platte tekst aan en geeft een `Notice` terug (of `None` als de
tekst geen herkend patroon matcht). `parser.py` is de enige aanroeper: die
selecteert de relevante kop-/inhoudstekst via `selectors.py` en geeft die
door aan `notices.py`.

---

# Schedule

`schedule.py` bepaalt de openingstijden voor een specifieke datum.

`hours_for_date`/`upcoming_hours` lezen alleen het reguliere weekrooster.
`resolve_day`/`resolve_upcoming` passen daarnaast elke `Notice` toe die bij
die datum en locatie hoort, en leveren een `ResolvedDay` met een
`reason`-veld op zodat entiteiten kunnen laten zien *waarom* een dag afwijkt
van het reguliere rooster. `next_open_close` loopt over een al opgeloste
`ResolvedDay`-lijst en levert de eerstvolgende open- en sluitingstijd als
`datetime` op (of `None` buiten het lookahead-venster) - pure functie, geen
Home Assistant-imports, net als de rest van deze module.

---

# Diagnostics

`diagnostics.py` biedt `async_get_config_entry_diagnostics`, Home
Assistant's standaard downloadbare-diagnostics-instappunt (automatisch
gedetecteerd, geen manifest.json-wijziging nodig). Het serialiseert
`entry.data`/`entry.options` en de actuele locaties/openingstijden/meldingen
van de coordinator naar platte, expliciete dicts - geen redactie nodig, want
niets hierin is gevoeliger dan de gekozen gemeente en de publieke
openingstijden-info die al op de Cure-website staat.

---

# Repairs

De coordinator maakt via `homeassistant.helpers.issue_registry` een
zichtbare "reparatie"-melding aan (`async_create_issue`) als een geslaagde
fetch geen enkele locatie oplevert - een betrouwbaar signaal dat de
Cure-pagina-opmaak veranderd is en de parser niet meer aansluit. Zodra een
volgende fetch weer locaties oplevert, wordt de melding automatisch
verwijderd (`async_delete_issue`); dezelfde opruiming gebeurt expliciet bij
het verwijderen/uitschakelen van de config entry.

---

# Logging

Gebruik `logger.py`.

Gebruik nooit `print()`.

---

# Async

Alle netwerkcommunicatie gebruikt `aiohttp`.

Geen blokkerende I/O.

---

# Parserregels

Geef de voorkeur aan semantische HTML.

Zoek in deze volgorde:

1. koppen
2. tabellen
3. semantische HTML-elementen
4. CSS-klassen (alleen als het niet anders kan)

---

# Toekomstige uitbreidingen

Klaar, zonder de parser-architectuur te wijzigen:

- meerdere gemeentes (v0.1.0)
- tijdelijke sluitingen, hitteprotocol (v0.2.0) - geparst van de
  milieustraat-pagina zelf; een los RSS-feed bleek niet nodig
- diagnostics, configureerbaar update-interval (v0.4.0)
- adres-attribuut, reconfigure flow, repair-issue bij een kapotte parser,
  `next_open`/`next_close`-sensoren (v0.5.0)
- robuustheid tegen opmaakwijzigingen (laatst bekende goede data aanhouden,
  fallback-selectors), navigatieknop-voorbeeld (v0.6.0)

Nog te ondersteunen:

- aanvullende sensoren (zie ROADMAP.md's "Toekomstideeën" voor concrete
  ideeën)

---

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

Where possible, selectors have a structural fallback alongside the
content check: if a specific tag/attribute disappears due to a layout
change, the distinguishing signal (the heading text) stays authoritative
instead of immediately returning `None`. See `location_addresses()`'s
h3-to-h1 fallback in `parser.py`, and `section_with_heading`/
`closure_notice_section` in `selectors.py` (v0.6.0).

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

If a fetch returns no locations at all (after an otherwise successful
HTTP request), the last known good locations are kept instead of being
overwritten with nothing - the repair issue (see Repairs) still stays
active as a signal that the location data may be stale. If there is no
earlier good data yet, the empty data is passed through as-is (v0.6.0).
The notices from that same fetch are always used regardless, even while
locations stay frozen - `location_addresses()` and `notices()` use
unrelated selectors, so a layout change can break one without affecting
the other (v0.6.1). Since `notices()` resolves a notice's
`location_hint` against that same cycle's (in this case empty) parsed
location list, that hint is re-resolved against the retained locations
where it is missing, otherwise a notice naming only one recycling centre
would end up incorrectly applying to all of them (v0.6.2).

---

# Entities

Entities never perform network requests.

Entities only read data from the coordinator.

---

# Notices

`notices.py` extracts temporary deviations (heat protocol, closures,
renovations) from free Dutch text found on the recycling centre page.

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
`next_open_close` walks an already-resolved `ResolvedDay` list and returns
the next opening and closing time as a `datetime` (or `None` outside the
lookahead window) - a pure function, no Home Assistant imports, same as the
rest of this module.

---

# Diagnostics

`diagnostics.py` exposes `async_get_config_entry_diagnostics`, Home
Assistant's standard downloadable-diagnostics entry point (auto-detected, no
manifest.json change needed). It serialises `entry.data`/`entry.options` and
the coordinator's current locations/opening hours/notices into plain, explicit
dicts - no redaction, since nothing here is more sensitive than the chosen
municipality and public opening-hours info already on the Cure website.

---

# Repairs

The coordinator creates a visible "repair" notification via
`homeassistant.helpers.issue_registry` (`async_create_issue`) whenever a
successful fetch returns no locations at all - a reliable signal that the
Cure page markup has changed and the parser no longer matches it. As soon
as a later fetch finds locations again, the notification is removed
automatically (`async_delete_issue`); the same cleanup happens explicitly
when the config entry is removed or unloaded.

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
- temporary closures, heat protocol (v0.2.0) - parsed from the recycling
  centre page itself; no separate RSS feed turned out to be necessary
- diagnostics, configurable update interval (v0.4.0)
- address attribute, reconfigure flow, repair issue for a broken parser,
  `next_open`/`next_close` sensors (v0.5.0)
- robustness against layout changes (keep last known good data, fallback
  selectors), navigation button example (v0.6.0)

Still to support:

- additional sensors (see ROADMAP.md's "Toekomstideeën" for concrete ideas)
