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
- [x] De komende dagen parsen

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

# v0.4.1 (klaar)

- [x] Bugfix: Home Assistant's `NumberSelector` geeft altijd een `float`
      terug (ongeacht step/mode), waardoor het wijzigen van het aantal
      vooruitkijkdagen of het update-interval elke sensor liet crashen
      (`TypeError: 'float' object cannot be interpreted as an integer`).
      Beide waarden worden nu expliciet naar `int` omgezet, zowel bij het
      opslaan als bij het uitlezen - een al opgeslagen `float`-waarde
      herstelt zichzelf dus vanzelf, zonder het formulier opnieuw in te
      hoeven dienen.

---

# v0.5.0 (klaar)

- [x] Adres als attribuut (`address`) op de status-sensor - `Location.address`
      werd al geparst, maar was nergens in Home Assistant zichtbaar
- [x] Reconfigure flow: gemeente van een bestaande config entry wijzigen
      zonder verwijderen + opnieuw toevoegen. Bij een daadwerkelijke
      wijziging vraagt de flow eerst expliciet om bevestiging, omdat alle
      sensoren en hun geschiedenis van de huidige gemeente vervangen worden
- [x] Repair-issue bij een kapotte parser (via
      `homeassistant.helpers.issue_registry`): een geslaagde fetch die geen
      enkele locatie meer oplevert toont nu een zichtbare
      "reparatie"-melding in de Home Assistant-UI, in plaats van alleen een
      debug-logregel
- [x] Twee nieuwe sensoren per milieustraat, "volgende open" en "volgende
      gesloten" (`next_open`/`next_close`, timestamp-device-class) - stond
      al in het allereerste ChatGPT-ontwerp ("Derived"-sectie) maar was
      nooit gebouwd

---

# v0.5.1 (klaar)

- [x] Bugfix: de reconfigure-flow werkte bij een daadwerkelijke
      gemeentewijziging wel `entry.data[CONF_MUNICIPALITY]` bij, maar gaf
      geen nieuwe `unique_id` mee aan `async_update_reload_and_abort`. De
      config entry bleef daardoor eigenaar van de oude gemeente-unique_id,
      wat een nieuwe integratie voor die (nu vrijgekomen) gemeente ten
      onrechte zou blokkeren. Gevonden tijdens een actieve, gerichte
      bug-review na v0.5.0 (niet door ruff/pytest alleen); een regressietest
      op `entry.unique_id` na een reconfigure is toegevoegd.

---

# Toekomstideeën (nog niet gepland, ter overweging)

- **Maximale robuustheid tegen opmaakwijzigingen van de website** - een
  wijziging in de HTML-structuur van de Cure-website mag de integratie
  nooit laten crashen of stilzwijgend verkeerde data tonen. De
  repair-issue (v0.5.0) meldt een kapotte parser al zichtbaar, maar de
  sensoren worden op dat moment nog steeds `unavailable`, omdat de
  coordinator de lege parse-uitkomst gewoon doorzet. Robuuster zou zijn om
  bij een lege/verdachte parse-uitkomst de laatst bekende goede data aan te
  houden (sensoren blijven dan bruikbaar, met de repair-issue als
  duidelijk signaal dat de data mogelijk verouderd is) in plaats van de
  oude data te overschrijven met niets. Daarnaast: meerdere fallback-
  selectors per element in `selectors.py` (in plaats van één CSS-selector
  die meteen breekt zodra Cure iets herindeelt), naar het voorbeeld van de
  bestaande h3-naar-h1-fallback in `location_addresses()`.
- **Landelijke uitbreiding** - de integratie op termijn herdopen (en
  mogelijk ook het logo wijzigen) naar een naam die niet aan Cure gebonden
  is, om milieustraten van alle Nederlandse gemeentes te ondersteunen, niet
  alleen de gemeentes die Cure bedient. Een groot traject: andere
  afvalbeheerders gebruiken andere website-structuren (dus aparte parser-/
  selector-implementaties per bron, met dezelfde laagverdeling als nu), een
  domeinwijziging (`cure_afvalbeheer` → iets generieks) is een breaking
  change voor bestaande gebruikers die een migratiepad nodig heeft, en een
  nieuw merk/logo dat niet meer aan Cure refereert. Pas te overwegen zodra
  de huidige Cure-ondersteuning stabiel en volledig is; nog geen concrete
  aanpak gekozen.
- **Navigatieknop** - een knop/actie voor op het dashboard die op een
  mobiele telefoon een navigatie-app opent (de zelfgekozen app die
  geïnstalleerd staat, of anders de standaard-app van het toestel) met de
  route naar de milieustraat, vanaf de actuele locatie van de gebruiker.
  Waarschijnlijk te realiseren zonder nieuwe Python-code, puur als
  dashboard-configuratie: een `tap_action` van het type `url` die een
  generieke maps-link opent (bijv.
  `https://www.google.com/maps/dir/?api=1&destination=<adres>`) - mobiele
  besturingssystemen laten de gebruiker daarbij zelf de navigatie-app
  kiezen, of gebruiken de ingestelde standaard. Kan het al sinds v0.5.0
  beschikbare `address`-attribuut hergebruiken; zou als extra voorbeeld in
  README.md passen, naast de bestaande markdown-kaart en automatisering.
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
- [x] Parse the upcoming days

## Coordinator

- [x] HTTP client
- [x] DataUpdateCoordinator
- [x] Update interval
- [x] Error handling
- [x] Retry logic (via DataUpdateCoordinator)

## Home Assistant

- [x] Device (one per municipality config entry)
- [x] Sensor (one per recycling centre)
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
      recycling centre page that is already fetched

---

# v0.3.0 (done)

- [x] Dedicated reason sensors per recycling centre, today and tomorrow, so
      an automation can warn a day ahead of a change instead of only once
      it has already taken effect
- [x] `reason` removed from the status sensor's `today` attribute (now
      redundant); kept in each `upcoming[]` entry
- [x] New recycling centres that Cure adds to a municipality page are
      detected and get their entities automatically, without a restart
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

# v0.4.1 (done)

- [x] Bugfix: Home Assistant's `NumberSelector` always returns a `float`
      (regardless of step/mode), so changing the forecast window or the
      update interval crashed every sensor
      (`TypeError: 'float' object cannot be interpreted as an integer`).
      Both values are now explicitly coerced to `int`, both when stored and
      when read back - an already-stored float value self-heals
      automatically, without needing to resubmit the form.

---

# v0.5.0 (done)

- [x] Address as an attribute (`address`) on the status sensor -
      `Location.address` was already parsed but never shown anywhere in
      Home Assistant
- [x] Reconfigure flow: change the municipality of an existing config entry
      without removing and re-adding it. On an actual change, the flow
      first asks for explicit confirmation, since all sensors and their
      history for the current municipality get replaced
- [x] Repair issue for a broken parser (via
      `homeassistant.helpers.issue_registry`): a successful fetch that
      returns no locations at all now shows a visible "repair" notification
      in the Home Assistant UI, instead of just a debug log line
- [x] Two new sensors per recycling centre, "next open" and "next close"
      (`next_open`/`next_close`, timestamp device class) - already present
      in the very first ChatGPT design ("Derived" section) but never built

---

# v0.5.1 (done)

- [x] Bugfix: the reconfigure flow updated `entry.data[CONF_MUNICIPALITY]`
      on an actual municipality change, but never passed a new `unique_id`
      to `async_update_reload_and_abort`. The config entry kept owning the
      old municipality's unique_id, which would incorrectly block a new
      integration from being added for that (now freed-up) municipality.
      Found during an active, targeted bug review after v0.5.0 (not by
      ruff/pytest alone); a regression test asserting `entry.unique_id`
      after a reconfigure was added.

---

# Future ideas (not yet planned, for consideration)

- **Maximum robustness against website layout changes** - a change in the
  Cure website's HTML structure should never crash the integration or
  silently show wrong data. The repair issue (v0.5.0) already surfaces a
  broken parser visibly, but the sensors still become `unavailable` at
  that point, because the coordinator passes the empty parse result
  straight through. It would be more robust to keep the last known good
  data on an empty/suspicious parse result (sensors stay usable, with the
  repair issue as a clear signal that the data may be stale) instead of
  overwriting the old data with nothing. In addition: multiple fallback
  selectors per element in `selectors.py` (instead of a single CSS
  selector that breaks the moment Cure reorganises something), following
  the existing h3-to-h1 fallback in `location_addresses()` as an example.
- **Nationwide expansion** - eventually rename the integration (and
  possibly its logo) to something not tied to Cure, to support recycling
  centres for every Dutch municipality, not just the ones Cure serves. A
  big undertaking: other waste management providers use different website
  structures (so separate parser/selector implementations per source,
  with the same layering as today), a domain rename
  (`cure_afvalbeheer` → something generic) is a breaking change for
  existing users that needs a migration path, and a new brand/logo no
  longer referencing Cure. Only worth considering once the current Cure
  support is stable and complete; no concrete approach chosen yet.
- **Navigation button** - a dashboard button/action that, on a mobile
  phone, opens a navigation app (whichever app the user has installed and
  picks, or otherwise the device's default) with the route to the
  recycling centre, from the user's current location. Likely achievable
  without any new Python code, purely as dashboard configuration: a
  `tap_action` of type `url` that opens a generic maps link (e.g.
  `https://www.google.com/maps/dir/?api=1&destination=<address>`) - mobile
  operating systems let the user pick their own navigation app for that,
  or use their configured default. Can reuse the `address` attribute
  already available since v0.5.0; would fit as an extra example in
  README.md, alongside the existing markdown card and automation.
- **Long-term statistics** - how often/how long a recycling centre was closed
  over a given period, via HA's recorder/statistics.
- Calendar-style output, a manual refresh action, repairs/accepted waste
  types/maps/navigation, additional languages - see earlier considerations;
  no concrete approach chosen yet.

---

# Nice to have

- [ ] Repairs history
- [ ] Diagnostics download automation/scripting
