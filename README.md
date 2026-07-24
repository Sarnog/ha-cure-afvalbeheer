🇳🇱 [Nederlands](#cure-afvalbeheer-voor-home-assistant) | 🇬🇧 [English](#cure-afvalbeheer-for-home-assistant)

---

# Cure Afvalbeheer voor Home Assistant

Een custom Home Assistant integratie voor Cure Afvalbeheer.

<!-- Tabel zodat de labels en de knoppen in twee nette, uitgelijnde kolommen
     staan die zich op elk scherm aanpassen. -->
<table>
  <tr>
    <td>Integratie toevoegen:</td>
    <td><a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Sarnog&amp;repository=ha-cure-afvalbeheer&amp;category=integration"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open je Home Assistant-installatie en open deze repository binnen de Home Assistant Community Store."></a></td>
  </tr>
  <tr>
    <td>Blueprint:</td>
    <td><a href="https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FSarnog%2Fha-cure-afvalbeheer%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fcure_afvalbeheer%2Fdeviation_warning.yaml"><img src="https://my.home-assistant.io/badges/blueprint_import.svg" alt="Open je Home Assistant-installatie en toon het importvenster voor de blueprint."></a></td>
  </tr>
</table>

De eerste knop voegt de repository als custom repository toe aan HACS, de
tweede importeert de kant-en-klare blueprint — je hoeft geen URL's zelf over
te typen.

## Doel

Deze integratie toont de actuele openingstijden van de milieustraten van een
Cure-gemeente naar keuze (Eindhoven, Valkenswaard of Geldrop-Mierlo).

Daarnaast worden tijdelijke afwijkingen van de reguliere openingstijden verwerkt,
zoals:

- aangepaste openingstijden vanwege het hitteprotocol
- tijdelijke sluitingen (bijvoorbeeld wegens werkzaamheden)
- verbouwingen

Alle informatie wordt rechtstreeks opgehaald vanaf de officiële Cure-website —
er is geen los RSS-abonnement nodig.

## Features

- **Config Flow** — kies een Cure-gemeente (Eindhoven, Valkenswaard of
  Geldrop-Mierlo); voeg dezelfde of een andere gemeente nogmaals toe voor
  meerdere devices.
- **Instelbaar via Opties / Herconfigureren** — het aantal vooruitkijkdagen
  (standaard 5, max. 30) en het update-interval (5-1440 minuten, standaard 60)
  zijn na installatie te wijzigen; via de reconfigure-flow wissel je ook de
  gemeente van een bestaande integratie (met een bevestigingsstap, omdat de
  sensoren en hun geschiedenis dan vervangen worden).
- **Live vanaf de officiële Cure-website** — een DataUpdateCoordinator haalt
  per gemeente de milieustraat-pagina op en parst adressen en openingstijden;
  geen los RSS-abonnement nodig.
- **Automatische locatie-detectie** — milieustraten die Cure aan een
  gemeentepagina toevoegt verschijnen automatisch, zonder herstart. Verdwijnt
  een milieustraat permanent, dan worden de sensoren `unavailable` en biedt
  Home Assistant zelf een verwijderoptie aan.
- **Vijf sensoren per milieustraat** — de status (open/gesloten) met `address`,
  `today` en `upcoming` als attributen, twee "reden"-sensoren (vandaag/morgen)
  en twee timestamp-sensoren ("volgende open" / "volgende gesloten"), zodat je
  al een dag vooraf kunt waarschuwen en de eerstvolgende statuswijziging direct
  bruikbaar is.
- **Tijdelijke afwijkingen** — hitteprotocol, tijdelijke sluitingen en
  verbouwingen worden uit dezelfde pagina geparst en passen de status en
  openingstijden automatisch aan, met een reden erbij.
- **Robuust bij site-wijzigingen** — bij een plotseling lege parse-uitkomst
  houdt de integratie de laatst bekende goede gegevens aan en toont een
  zichtbare reparatie-melding (**Instellingen → Systeem → Reparaties**), zodat
  je weet dat de data mogelijk verouderd is.
- **Diagnostics** — een downloadbare dump van de config entry en de actuele
  coordinator-data, handig bij bugrapporten.
- **Lokaal merklogo** — geserveerd via de eigen `brand/`-map (Home Assistant
  2026.3+), zonder externe pull request.

Zie [ROADMAP.md](ROADMAP.md) voor toekomstige ideeën en de
[release notes](https://github.com/Sarnog/ha-cure-afvalbeheer/releases) voor de
wijzigingsgeschiedenis per versie.

## Installatie

Via HACS:

1. Voeg deze repository toe als Custom Repository.
2. Installeer de integratie.
3. Herstart Home Assistant.
4. Voeg de integratie toe via Apparaten & Diensten en kies een gemeente.

## Ondersteunde gemeentes

- Eindhoven
- Valkenswaard
- Geldrop-Mierlo

Milieustraat-locaties binnen een gemeente worden automatisch ontdekt uit de
pagina; er is geen aparte configuratie per locatie nodig.

## Gebruik in het dashboard

Elke milieustraat krijgt vijf sensoren:

- **`sensor.<device>_<milieustraat>`** — status `open`/`closed`, met
  `address`, `today` en `upcoming` (de ingestelde vooruitkijkdagen) als
  attributen.
- **`sensor.<device>_<milieustraat>_reden_vandaag`** en
  **`..._reden_morgen`** — leeg (`""`) als er geen afwijking is, anders de
  reden (`hitteprotocol`, `verbouwing`, `werkzaamheden`).
- **`sensor.<device>_<milieustraat>_volgende_open`** en
  **`..._volgende_close`** — timestamp van de eerstvolgende keer dat de
  milieustraat open respectievelijk dicht gaat, binnen het ingestelde
  vooruitkijkvenster (anders `unknown`).

Zoek je eigen entity-ID's op via **Ontwikkelaarshulpmiddelen → Staten** — de
onderstaande voorbeelden gebruiken die van "Milieustraat Acht" in Eindhoven
(`sensor.cure_afvalbeheer_eindhoven_milieustraat_acht`) ter illustratie.

### Voorbeeld: markdown-kaart

Vereist de HACS-frontendkaart **[card-mod](https://github.com/thomasloven/lovelace-card-mod)**
— HA's markdown-kaart filtert het `style`-attribuut uit HTML (sanitizer), dus
de opmaak (kop centreren, icoon-kleur/animatie) wordt hier via `card_mod`
toegepast in plaats van inline.

Het voorbeeld hieronder gebruikt "Milieustraat Acht" in Eindhoven; pas
**één plek** aan naar je eigen situatie: de entity-ID op de regel
`{%- set sensor = ... -%}` — vervang
`sensor.cure_afvalbeheer_eindhoven_milieustraat_acht` door je eigen sensor
(op te zoeken via Ontwikkelaarshulpmiddelen → Staten). De koptekst wordt
automatisch afgeleid uit de naam van die sensor, dus die hoef je nergens
meer los aan te passen.

```yaml
type: markdown
content: >-
  {#- Bronsensor en attributen ophalen -#}
  {%- set sensor = 'sensor.cure_afvalbeheer_eindhoven_milieustraat_acht' -%}
  {%- set vandaag = state_attr(sensor, 'today') -%}
  {%- set upcoming = state_attr(sensor, 'upcoming') or [] -%}
  {%- set adres = state_attr(sensor, 'address') -%}
  {#- Naam en hulpsensoren worden afgeleid van de bronsensor hierboven -#}
  {%- set volledig = state_attr(sensor, 'friendly_name') or '' -%}
  {#- Alles vóór het woord 'Milieustraat' weglaten (integratie- en apparaatnaam)
  -#}
  {%- set pos = (volledig | lower).find('milieustraat') -%}
  {%- set naam = volledig[pos:] if pos >= 0 else (volledig or 'Milieustraat')
  -%}
  {%- set s_open = states(sensor ~ '_volgende_open') -%}
  {%- set s_dicht = states(sensor ~ '_volgende_gesloten') -%}
  {#- Is de milieustraat op dit moment daadwerkelijk open? -#}
  {%- set nu_open = vandaag is not none and not vandaag.closed
        and vandaag.opens is not none and vandaag.closes is not none
        and now() >= today_at(vandaag.opens) and now() <= today_at(vandaag.closes) -%}
  {#- Sluitingstijd voorbij? Dan geldt vandaag als gesloten -#}
  {%- set na_sluiting = vandaag is not none and not vandaag.closed and
  vandaag.closes is not none and now() > today_at(vandaag.closes) -%}
  {#- Alleen de sensor die nu telt hoeft een geldig tijdstip te hebben; zo niet:
  regel weglaten -#}
  {%- set d_open = as_datetime(s_open, none) -%}
  {%- set d_dicht = as_datetime(s_dicht, none) -%}
  {%- set toon_teller = (d_dicht if nu_open else d_open) is not none -%}
  {#- Datum van yyyy-mm-dd naar dd-mm-yyyy -#}
  {%- macro datum_nl(d) -%}
  {%- set s = d | string -%}{{ s[8:10] }}-{{ s[5:7] }}-{{ s[0:4] }}
  {%- endmacro -%}
  {#- Aftellen naar een timestamp-sensor: de frontend doet dit alleen in
  entity-rijen, hier zelf rekenen -#}
  {%- macro aftellen(t) -%}
  {%- set d = as_datetime(t, none) -%}
  {%- if d is none -%}onbekend
  {%- else -%}
  {%- set sec = ((d - now()).total_seconds() | int, 0) | max -%}
  {%- set dg = (sec // 86400) | int -%}
  {%- set uu = ((sec % 86400) // 3600) | int -%}
  {%- set mm = ((sec % 3600) // 60) | int -%}
  {%- if dg > 0 -%}{{ dg }} {{ 'dag' if dg == 1 else 'dagen' }}{% if uu > 0 %}
  en {{ uu }} uur{% endif %}
  {%- elif uu > 0 -%}{{ uu }} uur{% if mm > 0 %} en {{ mm }} min{% endif %}
  {%- elif mm > 0 -%}{{ mm }} min
  {%- else -%}minder dan een minuut
  {%- endif -%}
  {%- endif -%}
  {%- endmacro -%}
  <h2>{{ naam }}</h2>


  **Vandaag:** {% if vandaag is none %}Onbekend{% elif vandaag.closed or
  na_sluiting %}Gesloten{% else %}Geopend van {{ vandaag.opens }} tot {{
  vandaag.closes }}{% endif %}

  {% if toon_teller %}
  {% if nu_open %}**Sluit over:** {{ aftellen(s_dicht) }}{%
  else %}**Weer open over:** {{ aftellen(s_open) }}{% endif %}

  {% endif %}
  {% if adres %}

  [🧭 Route naar {{ naam
  }}](https://www.google.com/maps/dir/?api=1&destination={{ adres | urlencode
  }})

  {% endif %}
  **Openingstijden de komende dagen:**
  {% for dag in upcoming %}

  - {% if dag.reason %}<ha-icon icon="mdi:alert-outline"></ha-icon>{% endif %}{{
  datum_nl(dag.date) }}: {% if dag.closed %}Gesloten{% else %}Open van {{
  dag.opens }} tot {{ dag.closes }}{% endif %}{% if dag.reason %} — {{
  dag.reason }}{% endif %}

  {%- endfor %}
card_mod:
  style:
    ha-markdown $: >
      /* Kop centreren (style-attribuut werkt niet, sanitizer stript het) */

      ha-markdown-element h2 {
        text-align: center;
      }

      /* Bullets en de standaard lijst-inspring weg: het icoon neemt die plek in
      */

      ha-markdown-element ul {
        list-style: none;
        padding-inline-start: 0 !important;   /* browser zet hier standaard 40px */
        margin-inline-start: 0 !important;
        margin: 0;
      }

      /* Alle tekstregels dezelfde smalle inspring: precies genoeg voor het
      icoon */

      ha-markdown-element p,

      ha-markdown-element li {
        padding-left: 26px;   /* 20px icoon + 6px lucht */
      }

      /* Icoon absoluut in die ruimte, dus buiten de tekstflow: geen inspringing
      */

      ha-markdown-element li {
        position: relative;
      }

      ha-markdown-element li ha-icon {
        position: absolute;
        left: 0;
        top: 1px;              /* fijnafstelling verticaal */
      }

      /* Waarschuwingsicoon: donkeroranje + knipperen */

      ha-markdown-element ha-icon {
        color: darkorange;
        --mdc-icon-size: 20px;
        vertical-align: text-bottom;   /* icoon netjes op de tekstregel */
        animation: knipper-alert 1.5s ease-in-out infinite;
      }

      @keyframes knipper-alert {
        50% { opacity: 0.25; }
      }
```

De koptekst wordt automatisch afgeleid uit de `friendly_name` van de
bronsensor (alles vanaf het woord "Milieustraat"), en staat gecentreerd via
`card_mod`. "Vandaag" toont "Gesloten" zodra de sluitingstijd is
gepasseerd, ook al staat er geen afwijking actief (de `na_sluiting`-check
vergelijkt het huidige tijdstip met `vandaag.closes`). Zodra de "volgende
open"- en "volgende gesloten"-sensoren een geldige waarde binnen het
vooruitkijkvenster hebben, toont de kaart daaronder ook een aftelling:
"Sluit over: ..." als de milieustraat nu open is, of "Weer open over: ..."
als die nu gesloten is (in dagen/uren/minuten, via de `aftellen`-macro);
zonder geldige waarde blijft die regel gewoon weg. Is het `address`-attribuut
van de sensor bekend, dan verschijnt daaronder een klikbare
**🧭 Route naar ...**-link: tikken opent op een mobiel de navigatie-app met
de route naar de milieustraat (een `maps/dir`-link met het URL-gecodeerde
adres). Zonder adres blijft die regel weg. Datums worden via de
`datum_nl`-macro in `dd-mm-jjjj`-notatie getoond. Elke dag in de lijst
krijgt nu een eigen, knipperend waarschuwingsicoon (`mdi:alert-outline`)
zodra die specifieke dag een `reason` heeft, in plaats van één icoon bij
een kop die af en toe wisselt — de bijbehorende CSS zorgt ervoor dat het
icoon los van de tekst staat, zodat regels zonder afwijking niet
inspringen.

**Werkt dit automatisch mee met het ingestelde aantal vooruitkijkdagen?** Ja.
Het aantal dagen dat de integratie toont is instelbaar via **Instellingen →
Apparaten & Diensten → Cure Afvalbeheer → Configureren**: standaard 5, met
een maximum van 30. De `{% for dag in upcoming %}`-lus in de kaart telt
nergens hard tot 5 — hij loopt over precies wat de sensor aanlevert. Stel je
10 dagen vooruitkijken in, dan toont de kaart 10 regels; bij 30 dagen worden
dat er 30. Er hoeft dus niets aan de kaart zelf te veranderen.

Twee dingen om in gedachten te houden naarmate je richting het maximum gaat:

- **Hoogte/scroll**: plaats je deze kaart in een layout met een vaste hoogte
  (bijvoorbeeld naast andere kaarten in een kolom), dan kan een lange lijst
  een scrollbalk krijgen. Zet in dat geval `overflow: visible` en/of
  `height: auto` op de omliggende container.
- **Leesbaarheid**: bij 30 dagen wordt de kaart behoorlijk lang. Wil je dan
  liever alleen de dagen mét een afwijking zien in plaats van alle dagen,
  filter `upcoming` dan op `dag.reason` (zoals in een eerdere versie van dit
  voorbeeld) zodra de lijst lang wordt — dat is een keuze, geen noodzaak.

### Waarschuwing bij een afwijking morgen

Hiervoor bestaat de aparte "reden morgen"-sensor: de melding komt binnen
zodra Cure de wijziging aankondigt, niet pas op de dag zelf. Er zijn twee
manieren, van simpel naar flexibel:

1. **Kant-en-klare blueprint.** Klik de **Blueprint**-badge bovenaan dit
   bestand om
   [`deviation_warning.yaml`](blueprints/automation/cure_afvalbeheer/deviation_warning.yaml)
   te importeren, en kies daarna in een keuzemenu de milieustraat (de
   bijbehorende "... reden morgen"-sensor) en je telefoon (een toestel dat
   de HA Companion App draait). Titel en tekst worden automatisch ingevuld,
   geen sjablonen typen nodig; optioneel bewaak je meerdere milieustraten
   tegelijk en kies je op Android een eigen meldingskanaal. Home Assistant
   vraagt bij het opslaan zelf om een naam voor de automation.
2. **Zelf een automation bouwen**, voor volledige controle. Laat een
   **status**-trigger reageren op de `..._reden_morgen`-sensor van je
   milieustraat en filter met een template-conditie op de overgang van
   "geen afwijking" (`''`) naar een reden — bijvoorbeeld
   `{{ trigger.from_state.state == '' and trigger.to_state.state != '' }}` —
   en stuur in de actie een melding met `{{ trigger.to_state.state }}` als
   reden. De sensorwaarde is leeg (`""`) zolang er geen afwijking is, en
   anders `hitteprotocol`, `verbouwing` of `werkzaamheden`.

### Voorbeeld: navigatie-knop

Gebruikt het `address`-attribuut om op een mobiele telefoon rechtstreeks
naar de gekozen (of standaard) navigatie-app te linken, met de route naar
de milieustraat. Pas **één plek** aan: de entity-ID op de regel
`{%- set sensor = ... -%}`.

```yaml
type: markdown
content: |
  {%- set sensor = 'sensor.cure_afvalbeheer_eindhoven_milieustraat_acht' -%}
  {%- set adres = state_attr(sensor, 'address') -%}
  [🧭 Route naar Milieustraat Acht](https://www.google.com/maps/dir/?api=1&destination={{ adres | urlencode }})
```

Tikken op de link opent op een mobiele telefoon het OS-brede keuzemenu
voor navigatie-apps (of direct de ingestelde standaard-app), met de route
vanaf de huidige locatie van de gebruiker — dat gedrag regelt het
besturingssysteem zelf bij een `maps/dir`-link, niet de integratie. Er is
geen extra HACS-kaart voor nodig: de link staat gewoon in dezelfde
markdown-kaart als de andere voorbeelden, zodat de Jinja-templating
gegarandeerd werkt (in tegenstelling tot een `tap_action: url` met een
getemplatete URL, wat standaard Lovelace-kaarten niet betrouwbaar
ondersteunen).

## Architectuur

Zie [ARCHITECTURE.md](ARCHITECTURE.md).

## Ontwikkeling

Gebruik:

- Python 3.13
- Ruff
- pytest
- Home Assistant development guidelines

## Licentie

MIT

---

# Cure Afvalbeheer for Home Assistant

A custom Home Assistant integration for Cure Afvalbeheer.

<!-- Table so the labels and the buttons sit in two neat, aligned columns
     that adapt to any screen size. -->
<table>
  <tr>
    <td>Add integration:</td>
    <td><a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Sarnog&amp;repository=ha-cure-afvalbeheer&amp;category=integration"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store."></a></td>
  </tr>
  <tr>
    <td>Blueprint:</td>
    <td><a href="https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FSarnog%2Fha-cure-afvalbeheer%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fcure_afvalbeheer%2Fdeviation_warning.yaml"><img src="https://my.home-assistant.io/badges/blueprint_import.svg" alt="Open your Home Assistant instance and show the blueprint import dialog."></a></td>
  </tr>
</table>

The first button adds the repository as a custom repository in HACS, the
second imports the ready-made blueprint - no need to type any URLs in
yourself.

## Purpose

This integration shows the current opening hours of the recycling centres
(milieustraten) for a Cure municipality of your choice (Eindhoven,
Valkenswaard, or Geldrop-Mierlo).

It also processes temporary deviations from the regular opening hours, such
as:

- adjusted opening hours due to the heat protocol
- temporary closures (e.g. due to maintenance work)
- renovations

All information is fetched directly from the official Cure website — no
separate RSS subscription is needed.

## Features

- **Config Flow** — pick a Cure municipality (Eindhoven, Valkenswaard or
  Geldrop-Mierlo); add the same or a different municipality again for multiple
  devices.
- **Configurable via Options / Reconfigure** — the number of forecast days
  (default 5, max 30) and the update interval (5-1440 minutes, default 60) can
  be changed after installation; the reconfigure flow also lets you switch an
  existing integration's municipality (with a confirmation step, since the
  sensors and their history are then replaced).
- **Live from the official Cure website** — a DataUpdateCoordinator fetches
  each municipality's recycling-centre page and parses addresses and opening
  hours; no separate RSS subscription needed.
- **Automatic location discovery** — recycling centres that Cure adds to a
  municipality page appear automatically, without a restart. If one permanently
  disappears, its sensors become `unavailable` and Home Assistant offers a
  removal option.
- **Five sensors per recycling centre** — the status (open/closed) with
  `address`, `today` and `upcoming` attributes, two "reason" sensors
  (today/tomorrow) and two timestamp sensors ("next open" / "next close"), so
  you can warn a day ahead and the next status change is directly usable.
- **Temporary deviations** — heat protocol, temporary closures and renovations
  are parsed from the same page and automatically adjust the status and opening
  hours, with a reason attached.
- **Robust against site changes** — on a suddenly empty parse result the
  integration keeps the last known good data and shows a visible repair
  notification (**Settings → System → Repairs**), so you know the data may be
  stale.
- **Diagnostics** — a downloadable dump of the config entry and the current
  coordinator data, handy for bug reports.
- **Local brand logo** — served via the integration's own `brand/` folder
  (Home Assistant 2026.3+), with no external pull request.

See [ROADMAP.md](ROADMAP.md) for future ideas and the
[release notes](https://github.com/Sarnog/ha-cure-afvalbeheer/releases) for the
per-version change history.

## Installation

Via HACS:

1. Add this repository as a Custom Repository.
2. Install the integration.
3. Restart Home Assistant.
4. Add the integration via Devices & Services and pick a municipality.

## Supported municipalities

- Eindhoven
- Valkenswaard
- Geldrop-Mierlo

Recycling centre locations within a municipality are discovered
automatically from the page; no separate per-location configuration is
needed.

## Using it on your dashboard

Each recycling centre gets five sensors:

- **`sensor.<device>_<milieustraat>`** — status `open`/`closed`, with
  `address`, `today` and `upcoming` (the configured forecast days) as
  attributes.
- **`sensor.<device>_<milieustraat>_reden_vandaag`** and
  **`..._reden_morgen`** — empty (`""`) if there is no deviation, otherwise
  the reason (`hitteprotocol`, `verbouwing`, `werkzaamheden` — these values
  are always Dutch, since that is what the integration itself produces).
- **`sensor.<device>_<milieustraat>_volgende_open`** and
  **`..._volgende_close`** — timestamp of the next time the recycling
  centre opens and closes respectively, within the configured forecast
  window (otherwise `unknown`).

Look up your own entity IDs via **Developer Tools → States** — the examples
below use those of "Milieustraat Acht" in Eindhoven
(`sensor.cure_afvalbeheer_eindhoven_milieustraat_acht`) for illustration.

### Example: markdown card

Requires the HACS frontend card
**[card-mod](https://github.com/thomasloven/lovelace-card-mod)** — HA's
markdown card strips the `style` attribute from HTML (sanitizer), so the
styling (centered heading, icon colour/animation) is applied here via
`card_mod` instead of inline.

The example below uses "Milieustraat Acht" in Eindhoven; adjust **one
spot** for your own situation: the entity ID on the
`{%- set sensor = ... -%}` line — replace
`sensor.cure_afvalbeheer_eindhoven_milieustraat_acht` with your own sensor
(look it up via Developer Tools → States). The heading is derived
automatically from that sensor's name, so there is nothing else to change
by hand.

```yaml
type: markdown
content: >-
  {#- Fetch the source sensor and its attributes -#}
  {%- set sensor = 'sensor.cure_afvalbeheer_eindhoven_milieustraat_acht' -%}
  {%- set today = state_attr(sensor, 'today') -%}
  {%- set upcoming = state_attr(sensor, 'upcoming') or [] -%}
  {%- set address = state_attr(sensor, 'address') -%}
  {#- The name and helper sensors are derived from the source sensor above -#}
  {%- set full_name = state_attr(sensor, 'friendly_name') or '' -%}
  {#- Drop everything before the word 'Milieustraat' (integration and device
  name) -#}
  {%- set pos = (full_name | lower).find('milieustraat') -%}
  {%- set name = full_name[pos:] if pos >= 0 else (full_name or 'Milieustraat')
  -%}
  {%- set s_open = states(sensor ~ '_volgende_open') -%}
  {%- set s_close = states(sensor ~ '_volgende_gesloten') -%}
  {#- Is the recycling centre actually open right now? -#}
  {%- set now_open = today is not none and not today.closed
        and today.opens is not none and today.closes is not none
        and now() >= today_at(today.opens) and now() <= today_at(today.closes) -%}
  {#- Past closing time? Then today counts as closed -#}
  {%- set past_closing = today is not none and not today.closed and
  today.closes is not none and now() > today_at(today.closes) -%}
  {#- Only the sensor that currently matters needs a valid timestamp; skip the
  line if not -#}
  {%- set d_open = as_datetime(s_open, none) -%}
  {%- set d_close = as_datetime(s_close, none) -%}
  {%- set show_countdown = (d_close if now_open else d_open) is not none -%}
  {#- Date from yyyy-mm-dd to dd-mm-yyyy -#}
  {%- macro format_date(d) -%}
  {%- set s = d | string -%}{{ s[8:10] }}-{{ s[5:7] }}-{{ s[0:4] }}
  {%- endmacro -%}
  {#- Counting down to a timestamp sensor: the frontend only does this in
  entity rows, so it's calculated here -#}
  {%- macro countdown(t) -%}
  {%- set d = as_datetime(t, none) -%}
  {%- if d is none -%}unknown
  {%- else -%}
  {%- set sec = ((d - now()).total_seconds() | int, 0) | max -%}
  {%- set days = (sec // 86400) | int -%}
  {%- set hours = ((sec % 86400) // 3600) | int -%}
  {%- set mins = ((sec % 3600) // 60) | int -%}
  {%- if days > 0 -%}{{ days }} {{ 'day' if days == 1 else 'days' }}{% if hours > 0 %}
  and {{ hours }} hour{% if hours != 1 %}s{% endif %}{% endif %}
  {%- elif hours > 0 -%}{{ hours }} hour{% if hours != 1 %}s{% endif %}{% if mins > 0 %} and {{ mins }} min{% endif %}
  {%- elif mins > 0 -%}{{ mins }} min
  {%- else -%}less than a minute
  {%- endif -%}
  {%- endif -%}
  {%- endmacro -%}
  <h2>{{ name }}</h2>


  **Today:** {% if today is none %}Unknown{% elif today.closed or
  past_closing %}Closed{% else %}Open from {{ today.opens }} to {{
  today.closes }}{% endif %}

  {% if show_countdown %}
  {% if now_open %}**Closes in:** {{ countdown(s_close) }}{%
  else %}**Opens again in:** {{ countdown(s_open) }}{% endif %}

  {% endif %}
  {% if address %}

  [🧭 Route to {{ name
  }}](https://www.google.com/maps/dir/?api=1&destination={{ address | urlencode
  }})

  {% endif %}
  **Opening hours for the coming days:**
  {% for day in upcoming %}

  - {% if day.reason %}<ha-icon icon="mdi:alert-outline"></ha-icon>{% endif %}{{
  format_date(day.date) }}: {% if day.closed %}Closed{% else %}Open from {{
  day.opens }} to {{ day.closes }}{% endif %}{% if day.reason %} — {{
  day.reason }}{% endif %}

  {%- endfor %}
card_mod:
  style:
    ha-markdown $: >
      /* Center the heading (style attribute doesn't work, sanitizer strips it) */

      ha-markdown-element h2 {
        text-align: center;
      }

      /* Remove bullets and the default list indent: the icon takes that space */

      ha-markdown-element ul {
        list-style: none;
        padding-inline-start: 0 !important;   /* browsers default this to 40px */
        margin-inline-start: 0 !important;
        margin: 0;
      }

      /* Same narrow indent for every line: just enough room for the icon */

      ha-markdown-element p,

      ha-markdown-element li {
        padding-left: 26px;   /* 20px icon + 6px spacing */
      }

      /* Position the icon absolutely in that space, outside the text flow */

      ha-markdown-element li {
        position: relative;
      }

      ha-markdown-element li ha-icon {
        position: absolute;
        left: 0;
        top: 1px;              /* fine-tune vertical alignment */
      }

      /* Warning icon: dark orange + blinking */

      ha-markdown-element ha-icon {
        color: darkorange;
        --mdc-icon-size: 20px;
        vertical-align: text-bottom;   /* keep the icon on the text line */
        animation: blink-alert 1.5s ease-in-out infinite;
      }

      @keyframes blink-alert {
        50% { opacity: 0.25; }
      }
```

The heading is derived automatically from the source sensor's
`friendly_name` (everything from the word "Milieustraat" onward), and is
centered via `card_mod`. "Today" shows "Closed" once the closing time has
passed, even when no deviation is active (the `past_closing` check
compares the current time against `today.closes`). Once the "next open"
and "next close" sensors have a valid value within the forecast window,
the card also shows a countdown below that: "Closes in: ..." if the
recycling centre is currently open, or "Opens again in: ..." if it is
currently closed (in days/hours/minutes, via the `countdown` macro);
without a valid value, that line is simply omitted. If the sensor's
`address` attribute is known, a clickable **🧭 Route to ...** link appears
below that: tapping it opens the navigation app on a phone with the route to
the recycling centre (a `maps/dir` link with the URL-encoded address).
Without an address, that line is omitted. Dates are shown in
`dd-mm-yyyy` notation via the `format_date` macro. Every day in the list
now gets its own blinking warning icon (`mdi:alert-outline`) whenever that
specific day has a `reason`, instead of a single icon next to a heading
that occasionally switches — the accompanying CSS keeps the icon separate
from the text so lines without a deviation do not get indented.

**Does this automatically follow the configured number of forecast days?**
Yes. The number of days the integration shows is configurable via
**Settings → Devices & Services → Cure Afvalbeheer → Configure**: default
5, with a maximum of 30. The `{% for day in upcoming %}` loop in the card
never hardcodes a count of 5 — it simply loops over whatever the sensor
provides. Set the integration to look 10 days ahead and the card shows 10
lines; at 30 days it shows 30. Nothing in the card itself needs to change.

Two things to keep in mind as you get closer to the maximum:

- **Height/scrolling**: if you place this card in a layout with a fixed
  height (e.g. next to other cards in a column), a long list can end up
  with a scrollbar. In that case, set `overflow: visible` and/or
  `height: auto` on the surrounding container.
- **Readability**: at 30 days the card gets quite long. If you would rather
  only see the days with a deviation instead of every day, filter
  `upcoming` on `day.reason` (as in an earlier version of this example)
  once the list gets long — that is a choice, not a requirement.

### Warning about a deviation tomorrow

This is exactly why a dedicated "reason tomorrow" sensor exists: the
notification comes in as soon as Cure announces the change, not only once
the day itself arrives. There are two ways, from simple to flexible:

1. **Ready-made blueprint.** Click the **Blueprint** badge at the top of
   this file to import
   [`deviation_warning.yaml`](blueprints/automation/cure_afvalbeheer/deviation_warning.yaml),
   then pick the recycling centre (its matching "... reden morgen" sensor)
   and your phone (a device running the HA Companion App) from a menu. The
   title and text are filled in automatically, no templates to write
   yourself; you can optionally watch several recycling centres at once and,
   on Android, choose a dedicated notification channel. Home Assistant
   prompts you for a name when saving.
2. **Build your own automation**, for full control. Use a **state** trigger
   on your recycling centre's `..._reden_morgen` sensor and filter with a
   template condition for the transition from "no deviation" (`''`) to a
   reason — for example
   `{{ trigger.from_state.state == '' and trigger.to_state.state != '' }}` —
   then send a notification with `{{ trigger.to_state.state }}` as the
   reason. The sensor value is empty (`""`) while there is no deviation, and
   otherwise `hitteprotocol`, `verbouwing` or `werkzaamheden`.

### Example: navigation button

Uses the `address` attribute to link straight to a navigation app on a
mobile phone, with the route to the recycling centre. Adjust **one
spot**: the entity ID on the `{%- set sensor = ... -%}` line.

```yaml
type: markdown
content: |
  {%- set sensor = 'sensor.cure_afvalbeheer_eindhoven_milieustraat_acht' -%}
  {%- set address = state_attr(sensor, 'address') -%}
  [🧭 Route to Milieustraat Acht](https://www.google.com/maps/dir/?api=1&destination={{ address | urlencode }})
```

Tapping the link on a mobile phone opens the OS-wide navigation app
chooser (or the configured default app directly), with the route from the
user's current location - the operating system handles that behaviour for
a `maps/dir` link, not the integration. No extra HACS card is needed: the
link just lives in the same markdown card style as the other examples, so
the Jinja templating is guaranteed to work (unlike a `tap_action: url`
with a templated URL, which standard Lovelace cards don't reliably
support).

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md).

## Development

Uses:

- Python 3.13
- Ruff
- pytest
- Home Assistant development guidelines

## License

MIT
