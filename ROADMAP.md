🇳🇱 [Nederlands](#routekaart) | 🇬🇧 [English](#roadmap)

---

# Routekaart

## Visie

Bouw een hoogwaardige Home Assistant-integratie voor Cure Afvalbeheer.

De integratie moet betrouwbare en actuele informatie bieden over alle Cure-milieustraten, inclusief tijdelijke wijzigingen die via de Cure-website worden aangekondigd.

Het project streeft ernaar de Home Assistant Integration Quality Scale te volgen en geschikt te zijn voor publicatie via HACS.

---

# v0.1.0 (klaar)

## Basis

- [x] GitHub-repository
- [x] HACS-structuur
- [x] Config Flow (gemeentekeuze: Eindhoven, Valkenswaard, Geldrop-Mierlo)
- [x] Options Flow (instelbaar vooruitkijkvenster)
- [x] Logging
- [x] Parser-framework
- [x] HTML-fixture
- [x] Ontwikkelomgeving

## Parser

- [x] Alle milieustraten parsen voor elke ondersteunde gemeente
- [x] Reguliere openingstijden parsen
- [x] Adressen parsen
- [x] Openingstijden van vandaag parsen
- [x] De komende N dagen parsen

## Coordinator

- [x] HTTP-client
- [x] DataUpdateCoordinator
- [x] Update-interval
- [x] Foutafhandeling
- [x] Retry-logica (via DataUpdateCoordinator)

## Home Assistant

- [x] Device (één per gemeente-config-entry)
- [x] Sensor (één per milieustraat)
- [x] DeviceInfo

## Overig

- [x] Home Assistant brand-assets voorbereid (later vervangen, zie v0.3.1)

---

# v0.2.0 (klaar)

- [x] Hitteprotocol-detectie (aangepaste tijden + einddatum)
- [x] Tijdelijke sluitingen/verbouwingen (expliciete sluitingsdatum, of een
      lijst specifieke sluitingsdagen)
- [x] Afwijkingsreden zichtbaar als sensor-attribuut
- [x] Geen los RSS-feed nodig - afwijkingen worden geparst van dezelfde
      milieustraat-pagina die al wordt opgehaald

---

# v0.3.0 (klaar)

- [x] Losse reden-sensoren per milieustraat, vandaag en morgen, zodat een
      automatisering al één dag vooraf kan waarschuwen in plaats van pas als
      de wijziging al is ingegaan
- [x] `reason` weggehaald uit het `today`-attribuut van de status-sensor (nu
      overbodig); blijft staan in elke `upcoming[]`-entry
- [x] Nieuwe milieustraten die Cure aan een gemeentepagina toevoegt worden
      gedetecteerd en krijgen automatisch hun entiteiten, zonder herstart
- [x] Locaties die permanent verdwijnen worden `unavailable` in plaats van
      dat er iets in code wordt verwijderd; blijft de locatie na een herstart
      nog steeds weg, dan biedt Home Assistants eigen entity-platform de
      gebruiker een verwijderoptie voor de resulterende wees-entiteit

---

# v0.3.1 (klaar)

- [x] Merklogo lokaal geserveerd via de eigen `brand/`-map van de integratie
      (Home Assistant 2026.3+ Brands Proxy API) - geen
      `home-assistant/brands`-pull-request meer nodig, vervangt de
      v0.1.0-aanpak
- [x] Herstijlde markdown-kaart-voorbeeld in README (gecentreerde kop, een
      knipperend donkeroranje `mdi:alert-outline`-icoon via `card-mod`, een
      alleen-afwijkingen-dagenlijst die terugvalt op de volledige vooruitblik
      als niets afwijkt)

---

# v0.4.0 (klaar)

- [x] Diagnostics (`diagnostics.py`): downloadbare dump van de config entry
      en de actuele coordinator-data, voor bugrapporten
- [x] Configureerbaar update-interval (Options Flow, naast de bestaande
      vooruitkijkvenster-instelling)

---

# Toekomstideeën (nog niet gepland, ter overweging)

- **Repair-issues bij een kapotte parser** - als Cure de pagina-opmaak ooit
  zo wijzigt dat er geen locaties/openingstijden meer worden gevonden, blijft
  dat nu beperkt tot een debug-logregel. Een zichtbare "reparatie"-melding in
  de Home Assistant-UI (via `homeassistant.helpers.issue_registry`) zou veel
  behulpzamer zijn en sluit aan bij de eigen AGENTS.md-wens: niet hoeven
  gissen wat er mis is.
- **`next_change`/`next_open`/`next_close`-achtige info** - stond al in het
  allereerste ontwerp (de oorspronkelijke ChatGPT-verkenning, "Derived"-
  sectie) maar is nooit gebouwd: alleen de actuele open/gesloten-status en
  vandaag/morgen bestaan, niet "wanneer verandert dit precies" verder dan dat.
- **Adres als attribuut/entiteit** - `Location.address` wordt al geparst maar
  nergens in Home Assistant getoond. Kleine, makkelijke aanvulling.
- **Reconfigure flow** - de gemeente van een bestaande config entry wijzigen
  zonder verwijderen + opnieuw toevoegen (`async_step_reconfigure`, moderne
  HA-conventie).
- **Langetermijnstatistieken** - hoe vaak/hoe lang een milieustraat de
  afgelopen periode gesloten was, via HA's recorder/statistics.
- Kalender-stijl output, een handmatige refresh-actie, reparaties/
  geaccepteerde afvalsoorten/kaarten/navigatie, meerdere talen - zie eerdere
  overwegingen; nog geen concrete aanpak voor gekozen.

---

# Wensenlijst

- [ ] Reparatiegeschiedenis
- [ ] Automatisering/scripting voor diagnostics-download

---

# Roadmap

## Vision

Build a high-quality Home Assistant integration for Cure Afvalbeheer.

The integration should provide reliable and up-to-date information about all Cure recycling centres (milieustraten), including temporary changes announced through the Cure website.

The project aims to follow the Home Assistant Integration Quality Scale and be suitable for publication through HACS.

---

# v0.1.0 (done)

## Core

- [x] GitHub repository
- [x] HACS structure
- [x] Config Flow (per-municipality selection: Eindhoven, Valkenswaard, Geldrop-Mierlo)
- [x] Options Flow (configurable forecast window)
- [x] Logging
- [x] Parser framework
- [x] HTML fixture
- [x] Development environment

## Parser

- [x] Parse all recycling centres for every supported municipality
- [x] Parse regular opening hours
- [x] Parse addresses
- [x] Parse today's opening hours
- [x] Parse the upcoming N days

## Coordinator

- [x] HTTP client
- [x] DataUpdateCoordinator
- [x] Update interval
- [x] Error handling
- [x] Retry logic (via DataUpdateCoordinator)

## Home Assistant

- [x] Device (one per municipality config entry)
- [x] Sensor (one per milieustraat)
- [x] DeviceInfo

## Other

- [x] Home Assistant brand assets prepared (later superseded, see v0.3.1)

---

# v0.2.0 (done)

- [x] Heat protocol detection (adjusted hours + end date)
- [x] Temporary closures / renovations (explicit closing date, or a list of
      specific closed dates)
- [x] Deviation reason exposed as a sensor attribute
- [x] No separate RSS feed needed - deviations are parsed from the same
      milieustraat page that is already fetched

---

# v0.3.0 (done)

- [x] Dedicated reason sensors per milieustraat, today and tomorrow, so an
      automation can warn a day ahead of a change instead of only once it
      has already taken effect
- [x] `reason` removed from the status sensor's `today` attribute (now
      redundant); kept in each `upcoming[]` entry
- [x] New milieustraten that Cure adds to a municipality page are detected
      and get their entities automatically, without a restart
- [x] Locations that permanently disappear become `unavailable` instead of
      anything being deleted in code; if still gone after a restart, Home
      Assistant's own entity platform offers the user a removal option for
      the resulting orphaned entity

---

# v0.3.1 (done)

- [x] Brand logo served locally via the integration's own `brand/` folder
      (Home Assistant 2026.3+ Brands Proxy API) - no `home-assistant/brands`
      pull request needed anymore, superseding the v0.1.0 approach
- [x] Restyled markdown card example in README (centered heading, a
      blinking dark-orange `mdi:alert-outline` icon via `card-mod`, a
      deviation-only day list that falls back to the full forecast when
      nothing deviates)

---

# v0.4.0 (done)

- [x] Diagnostics (`diagnostics.py`): downloadable dump of the config entry
      and the coordinator's current data, for bug reports
- [x] Configurable update interval (Options Flow, alongside the existing
      forecast-window setting)

---

# Future ideas (not yet planned, for consideration)

- **Repair issues on a broken parser** - if Cure ever changes the page
  markup so that no locations/opening hours are found anymore, this
  currently stays limited to a debug log line. A visible "repair"
  notification in the Home Assistant UI (via
  `homeassistant.helpers.issue_registry`) would be far more helpful, and
  matches AGENTS.md's own wish: never having to guess what went wrong.
- **`next_change`/`next_open`/`next_close`-style info** - already present in
  the very first design (the original ChatGPT exploration, "Derived"
  section) but never built: only the current open/closed status and
  today/tomorrow exist, not "exactly when does this change" beyond that.
- **Address as an attribute/entity** - `Location.address` is already parsed
  but never shown anywhere in Home Assistant. Small, easy addition.
- **Reconfigure flow** - change the municipality of an existing config entry
  without removing and re-adding it (`async_step_reconfigure`, a modern HA
  convention).
- **Long-term statistics** - how often/how long a milieustraat was closed
  over a given period, via HA's recorder/statistics.
- Calendar-style output, a manual refresh action, repairs/accepted waste
  types/maps/navigation, additional languages - see earlier considerations;
  no concrete approach chosen yet.

---

# Nice to have

- [ ] Repairs history
- [ ] Diagnostics download automation/scripting
