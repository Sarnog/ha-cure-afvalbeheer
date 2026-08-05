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
`closure_notice_section` in `selectors.py`.

Kop-teksten worden nooit exact vergeleken wanneer Cure er variabele
onderdelen in zet. `closing_days_blocks` matcht daarom alleen op het woord
"Sluitingsdagen" en negeert het jaartal dat erachter staat: dat jaartal
wijzigt elk jaar en loopt in de praktijk soms achter op de werkelijkheid.
Datzelfde blok heeft geen eigen container - het deelt één prose-`div` met
de openingstijden - dus de inhoud wordt verzameld door vanaf de kop vooruit
te lopen tot de volgende kop van hetzelfde of een hoger niveau, in plaats
van via een `find_parent`.

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
gewoon doorgezet. De meldingen (`notices`) uit diezelfde fetch worden wél
altijd gebruikt, ook als de locaties bevroren blijven -
`location_addresses()` en `notices()` gebruiken losstaande selectors, dus
een opmaakwijziging kan de één breken zonder de ander te raken. Omdat
`notices()` de `location_hint` van een melding bepaalt aan de hand van de
op dát moment geparste (in dit geval lege) locatie-lijst, wordt die hint
zo nodig herberekend tegen de aangehouden locaties, anders zou een melding
die maar één milieustraat betreft per ongeluk voor alle locaties gaan
gelden.

---

# Entiteiten

Entiteiten doen nooit netwerkverzoeken.

Entiteiten lezen alleen data uit de coordinator.

---

# Notices

`notices.py` haalt tijdelijke afwijkingen (hitteprotocol, sluitingen,
verbouwingen, de sluitingsdagen rond feestdagen) uit vrije Nederlandse
tekst op de milieustraat-pagina.

Bevat geen BeautifulSoup/HTML-code en geen Home Assistant-imports - het
neemt alleen platte tekst aan en geeft een `Notice` terug (of `None` als de
tekst geen herkend patroon matcht). `parser.py` is de enige aanroeper: die
selecteert de relevante kop-/inhoudstekst via `selectors.py` en geeft die
door aan `notices.py`.

De sluitingsdagen zijn volledig datum-gedreven: `parse_closing_days` leest
elke regel los en levert alleen iets op als daar een datum in staat, zodat
de omringende huisregels in hetzelfde blok vanzelf genegeerd worden. Voor de
jaartal-bepaling geldt een vaste volgorde - het jaartal in de regel zelf,
anders dat uit de kop, anders de eerstvolgende keer dat die datum zich
voordoet. Die
volgorde is bewust zo: een verouderd jaartal uit de kop levert een datum in
het verleden op, en die wordt simpelweg nooit toegepast.

Van een reeks ("van 25 december tot en met 4 januari") schrijft Cure alleen
de twee uiteinden uit; de dagen ertussen worden aangevuld. Zo'n reeks gaat
zonder het te vermelden over de jaarwisseling heen, waardoor het einde vóór
het begin uitkomt - dat einde wordt dan een jaar later gelezen. Komt een
reeks langer uit dan `_MAX_SPAN_DAYS`, dan blijven alleen de twee uiteinden
staan: een sluitingsdagenlijst gaat over vrije dagen rond een feestdag, en
een verkeerd gelezen regel als maandenlange sluiting doorzetten is de
schadelijkste manier om fout te zitten. Een streepje telt tussen twee
datums alleen als het los staat, omdat gemeentenamen als Geldrop-Mierlo er
zelf een hebben.

Regels die geen sluiting maar andere openingstijden aankondigen leveren een
`Notice` met alleen de kant die genoemd wordt: "geopend tot 16:00 uur" vult
`closes`, "pas vanaf 10:00 uur open" vult `opens`, en "geopend van 10:00 tot
16:00 uur" allebei. De niet-genoemde kant blijft `None`, zodat `schedule.py`
daar de reguliere tijd voor aanhoudt. Een los uur telt alleen als tijd
wanneer er "uur" achter staat - "vanaf 6 april" is een datum, geen 06:00.

Kondigt een regel wél aan dat de milieustraat open is, maar zijn de tijden
niet te lezen, dan levert die regel niets op. Als sluiting doorzetten zou
namelijk precies het tegenovergestelde beweren van wat er staat. Bevat de
regel daarnaast een sluitingswoord, dan wint de sluiting alsnog.

---

# Schedule

`schedule.py` bepaalt de openingstijden voor een specifieke datum.

`hours_for_date`/`upcoming_hours` lezen alleen het reguliere weekrooster.
`resolve_day`/`resolve_upcoming` passen daarnaast elke `Notice` toe die bij
die datum en locatie hoort, en leveren een `ResolvedDay` met een
`reason`-veld op zodat entiteiten kunnen laten zien *waarom* een dag afwijkt
van het reguliere rooster.

Daarbij gelden drie regels. Een sluiting wint altijd van een
tijden-aanpassing. Een tijden-aanpassing geldt alleen op een dag die
volgens het reguliere rooster al open is - een hitteprotocol maakt van een
zondag dus geen open dag. Openings- en sluitingstijd worden los van elkaar
afgehandeld: de kant die de melding niet noemt houdt de reguliere tijd, en
gelden er meerdere aanpassingen op dezelfde dag, dan wint per kant de
striktste - de laatste openingstijd en de vroegste sluitingstijd. Zo hangt
de uitkomst nooit af van de volgorde waarin de pagina ze toevallig noemt.
De `reason` komt van de melding achter de sluitingstijd, want daar loopt
een bezoeker het eerst tegenaan.

`next_open_close` loopt over een al opgeloste
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

# Uitbreidbaarheid

Deze lagenstructuur is opgezet om nieuwe functionaliteit op te nemen zonder de
pijplijn zelf te wijzigen: een nieuwe gegevensbron of afwijkingssoort haakt aan
op de Selectors-/Parser-laag, afgeleide waarden komen in `schedule.py` en de
entiteiten. Meer gemeentes, extra sensoren en nieuwe afwijkingstypen passen zo
binnen dezelfde architectuur. Concrete ideeën voor uitbreidingen staan in
[ROADMAP.md](ROADMAP.md).

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
`closure_notice_section` in `selectors.py`.

Heading text is never compared in full where Cure puts a variable part in
it. `closing_days_blocks` therefore matches on the word "Sluitingsdagen"
alone and ignores the year behind it: that year changes annually and, in
practice, sometimes lags behind reality. That same block has no container
of its own - it shares one prose `div` with the opening hours - so its
content is collected by walking forward from the heading until the next
heading of the same or a higher level, rather than through a `find_parent`.

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
earlier good data yet, the empty data is passed through as-is. The
notices from that same fetch are always used regardless, even while
locations stay frozen - `location_addresses()` and `notices()` use
unrelated selectors, so a layout change can break one without affecting
the other. Since `notices()` resolves a notice's `location_hint` against
that same cycle's (in this case empty) parsed location list, that hint is
re-resolved against the retained locations where it is missing, otherwise
a notice naming only one recycling centre would end up incorrectly
applying to all of them.

---

# Entities

Entities never perform network requests.

Entities only read data from the coordinator.

---

# Notices

`notices.py` extracts temporary deviations (heat protocol, closures,
renovations, the closing days around public holidays) from free Dutch text
found on the recycling centre page.

Contains no BeautifulSoup/HTML code and no Home Assistant imports - it only
takes plain strings and returns a `Notice` (or `None` when the text does not
match a recognised pattern). `parser.py` is the only caller: it selects the
relevant heading/body text via `selectors.py` and hands it to `notices.py`.

The closing days are entirely date-driven: `parse_closing_days` reads each
line on its own and yields something only when that line holds a date, so
the house rules sharing the same block are skipped without any special
handling. Resolving
the year follows a fixed order - the year in the line itself, else the one
from the heading, else the next time that day comes round. That order is
deliberate: an out-of-date year from the heading produces a date in the
past, and such a date is simply never applied.

Of a range ("van 25 december tot en met 4 januari") Cure writes out only
the two ends; the days between them are filled in. Such a range crosses
new year without saying so, which puts its end before its start - that end
is then read as a year later. A range coming out longer than
`_MAX_SPAN_DAYS` keeps its two ends alone: a closing days list is about
days off around a holiday, and carrying a misread line through as a
closure of months is the most harmful way to be wrong. Between two dates a
dash only counts when it stands on its own, since municipality names such
as Geldrop-Mierlo carry one themselves.

A line announcing different hours rather than a closure yields a `Notice`
carrying only the side it names: "geopend tot 16:00 uur" fills `closes`,
"pas vanaf 10:00 uur open" fills `opens`, and "geopend van 10:00 tot 16:00
uur" fills both. The unnamed side stays `None`, so `schedule.py` keeps the
regular time there. A lone hour only counts as a time when "uur" follows
it - "vanaf 6 april" is a date, not 06:00.

A line that does say the recycling centre is open but whose times cannot be
read yields nothing at all: carrying it through as a closure would claim
the exact opposite of what it says. If such a line also carries a word for
being shut, the closure wins after all.

---

# Schedule

`schedule.py` resolves the opening hours for a specific date.

`hours_for_date`/`upcoming_hours` read only the regular weekly schedule.
`resolve_day`/`resolve_upcoming` additionally apply any `Notice`s that match
that date and location, producing a `ResolvedDay` with a `reason` field so
entities can show *why* a day deviates from the regular schedule.

Three rules govern that. A closure always beats an hours adjustment. An
hours adjustment only ever applies to a day the regular schedule already
opens - a heat protocol does not turn a Sunday into an open day. Opening
and closing time are handled separately: the side a notice does not name
keeps its regular time, and where several adjustments land on the same day
the strictest of each side wins - the latest opening time and the earliest
closing time. The outcome therefore never depends on the order the page
happened to mention them in. The `reason` comes from the notice behind the
closing time, since that is the one a visitor runs into first.

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

# Extensibility

This layered structure is designed to accommodate new functionality without
changing the pipeline itself: a new data source or deviation type plugs in at
the Selectors/Parser layer, derived values go in `schedule.py` and the
entities. More municipalities, extra sensors and new deviation types all fit
within the same architecture. Concrete ideas for extensions live in
[ROADMAP.md](ROADMAP.md).
