🇳🇱 [Nederlands](#cure-afvalbeheer-voor-home-assistant) | 🇬🇧 [English](#cure-afvalbeheer-for-home-assistant)

---

# Cure Afvalbeheer voor Home Assistant

Een custom Home Assistant integratie voor Cure Afvalbeheer.

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

### v0.1.0

- Config Flow: kies een Cure-gemeente; voeg dezelfde of een andere gemeente
  desgewenst nogmaals toe voor meerdere devices.
- Options Flow: aantal vooruitkijkdagen instelbaar (standaard 5), ook na
  installatie te wijzigen.
- DataUpdateCoordinator haalt live de milieustraat-pagina van de gekozen
  gemeente op.
- Eén sensor per milieustraat: actuele status (Open/Gesloten) en `today`/
  `upcoming`-attributen voor gebruik in een markdown-kaart.
- Home Assistant brand-assets voorbereid (zie `brands/`).

### v0.2.0

- Tijdelijke afwijkingen (hitteprotocol, verbouwing, sluiting) worden uit de
  pagina zelf geparst en passen de sensor-status/attributen automatisch aan.

### v0.3.0

- Twee losse "reden"-sensoren per milieustraat (vandaag/morgen) in plaats van
  een verstopt attribuut, zodat je automatiseringen al één dag vooruit kunt
  laten waarschuwen voor een afwijking.
- Nieuwe milieustraten die Cure aan een gemeentepagina toevoegt verschijnen
  automatisch, zonder herstart. Verdwijnt een milieustraat permanent, dan
  worden de bijbehorende sensoren `unavailable`; blijft die na een herstart
  nog steeds weg, dan biedt Home Assistant zelf een verwijderoptie aan.

### v0.3.1

- Het merklogo wordt lokaal geserveerd via de eigen `brand/`-map van de
  integratie (Home Assistant 2026.3+), zonder externe pull request.

### v0.4.0

- Diagnostics: een downloadbare dump van de config entry en de actuele
  coordinator-data, handig bij bugrapporten.
- Update-interval instelbaar via de Options Flow (5-1440 minuten, standaard
  60), naast het aantal vooruitkijkdagen.

### v0.5.0

- Adres van de milieustraat is nu ook als `address`-attribuut op de
  statussensor beschikbaar (was al geparst, maar nergens getoond).
- Reconfigure flow: wijzig de gemeente van een bestaande integratie via
  **Instellingen → Apparaten & Diensten → Cure Afvalbeheer → Configureren**,
  zonder de integratie te verwijderen en opnieuw toe te voegen. Kies je een
  andere gemeente, dan vraagt de flow eerst expliciet om bevestiging — alle
  sensoren en hun geschiedenis voor de huidige gemeente worden namelijk
  vervangen door sensoren voor de nieuwe.
- Twee nieuwe sensoren per milieustraat, **"volgende open"** en **"volgende
  gesloten"** (timestamp), zodat de eerstvolgende statuswijziging direct
  bruikbaar is in automatiseringen en op het dashboard, in plaats van
  verstopt in een attribuut.
- Zichtbare "reparatie"-melding in Home Assistant (**Instellingen →
  Systeem → Reparaties**) als de parser plotseling geen enkele milieustraat
  meer vindt, bijvoorbeeld door een wijziging in de opmaak van de
  Cure-website.

Zie ROADMAP.md voor wat er nog gepland staat.

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

Het voorbeeld hieronder gebruikt "Milieustraat Acht" in Eindhoven; pas **twee
plekken** aan naar je eigen situatie:
1. De entity-ID op de regel `{%- set sensor = ... -%}` — vervang
   `sensor.cure_afvalbeheer_eindhoven_milieustraat_acht` door je eigen sensor
   (op te zoeken via Ontwikkelaarshulpmiddelen → Staten).
2. De tekst tussen `<h2>` en `</h2>` — vervang "Milieustraat Acht" door de
   naam die je op de kaart wilt zien staan.

```yaml
type: markdown
content: |
  {#- Bronsensor en attributen ophalen -#}
  {%- set sensor = 'sensor.cure_afvalbeheer_eindhoven_milieustraat_acht' -%}
  {%- set vandaag = state_attr(sensor, 'today') -%}
  {%- set upcoming = state_attr(sensor, 'upcoming') or [] -%}
  {#- Naam en hulpsensoren worden afgeleid van de bronsensor hierboven -#}
  {%- set volledig = state_attr(sensor, 'friendly_name') or '' -%}
  {#- Alles vóór het woord 'Milieustraat' weglaten (integratie- en apparaatnaam) -#}
  {%- set pos = (volledig | lower).find('milieustraat') -%}
  {%- set naam = volledig[pos:] if pos >= 0 else (volledig or 'Milieustraat') -%}
  {%- set s_open = states(sensor ~ '_volgende_open') -%}
  {%- set s_dicht = states(sensor ~ '_volgende_gesloten') -%}
  {#- Is de milieustraat op dit moment daadwerkelijk open? -#}
  {%- set nu_open = vandaag is not none and not vandaag.closed
        and vandaag.opens is not none and vandaag.closes is not none
        and now() >= today_at(vandaag.opens) and now() <= today_at(vandaag.closes) -%}
  {#- Sluitingstijd voorbij? Dan geldt vandaag als gesloten -#}
  {%- set na_sluiting = vandaag is not none and not vandaag.closed and vandaag.closes is not none and now() > today_at(vandaag.closes) -%}
  {#- Alleen de sensor die nu telt hoeft een geldig tijdstip te hebben; zo niet: regel weglaten -#}
  {%- set d_open = as_datetime(s_open, none) -%}
  {%- set d_dicht = as_datetime(s_dicht, none) -%}
  {%- set toon_teller = (d_dicht if nu_open else d_open) is not none -%}
  {#- Datum van yyyy-mm-dd naar dd-mm-yyyy -#}
  {%- macro datum_nl(d) -%}
  {%- set s = d | string -%}{{ s[8:10] }}-{{ s[5:7] }}-{{ s[0:4] }}
  {%- endmacro -%}
  {#- Aftellen naar een timestamp-sensor: de frontend doet dit alleen in entity-rijen, hier zelf rekenen -#}
  {%- macro aftellen(t) -%}
  {%- set d = as_datetime(t, none) -%}
  {%- if d is none -%}onbekend
  {%- else -%}
  {%- set sec = ((d - now()).total_seconds() | int, 0) | max -%}
  {%- set dg = (sec // 86400) | int -%}
  {%- set uu = ((sec % 86400) // 3600) | int -%}
  {%- set mm = ((sec % 3600) // 60) | int -%}
  {%- if dg > 0 -%}{{ dg }} {{ 'dag' if dg == 1 else 'dagen' }}{% if uu > 0 %} en {{ uu }} uur{% endif %}
  {%- elif uu > 0 -%}{{ uu }} uur{% if mm > 0 %} en {{ mm }} min{% endif %}
  {%- elif mm > 0 -%}{{ mm }} min
  {%- else -%}minder dan een minuut
  {%- endif -%}
  {%- endif -%}
  {%- endmacro -%}
  <h2>{{ naam }}</h2>

  **Vandaag:** {% if vandaag is none %}Onbekend{% elif vandaag.closed or na_sluiting %}Gesloten{% else %}Geopend van {{ vandaag.opens }} tot {{ vandaag.closes }}{% endif %}
  {% if toon_teller %}
  {% if nu_open %}**Sluit over:** {{ aftellen(s_dicht) }}{% else %}**Weer open over:** {{ aftellen(s_open) }}{% endif %}
  {% endif %}
  **Openingstijden de komende dagen:**
  {% for dag in upcoming %}
  - {% if dag.reason %}<ha-icon icon="mdi:alert-outline"></ha-icon>{% endif %}{{ datum_nl(dag.date) }}: {% if dag.closed %}Gesloten{% else %}Open van {{ dag.opens }} tot {{ dag.closes }}{% endif %}{% if dag.reason %} — {{ dag.reason }}{% endif %}
  {%- endfor %}
card_mod:
  style:
    ha-markdown $: |
      /* Kop centreren (style-attribuut werkt niet, sanitizer stript het) */
      ha-markdown-element h2 {
        text-align: center;
      }
      /* Bullets en de standaard lijst-inspring weg: het icoon neemt die plek in */
      ha-markdown-element ul {
        list-style: none;
        padding-inline-start: 0 !important;   /* browser zet hier standaard 40px */
        margin-inline-start: 0 !important;
        margin: 0;
      }
      /* Alle tekstregels dezelfde smalle inspring: precies genoeg voor het icoon */
      ha-markdown-element p,
      ha-markdown-element li {
        padding-left: 26px;   /* 20px icoon + 6px lucht */
      }
      /* Icoon absoluut in die ruimte, dus buiten de tekstflow: geen inspringing */
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

De kop staat gecentreerd via `card_mod`. "Vandaag" toont "Gesloten" zodra de
sluitingstijd is gepasseerd, ook al staat er geen afwijking actief (de
`na_sluiting`-check vergelijkt het huidige tijdstip met `vandaag.closes`).
Datums worden via de `datum_nl`-macro in `dd-mm-jjjj`-notatie getoond. Elke
dag in de lijst krijgt nu een eigen, knipperend waarschuwingsicoon
(`mdi:alert-outline`) zodra die specifieke dag een `reason` heeft, in plaats
van één icoon bij een kop die af en toe wisselt — de bijbehorende CSS zorgt
ervoor dat het icoon los van de tekst staat, zodat regels zonder afwijking
niet inspringen.

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

### Voorbeeld: automatisering (waarschuw al één dag vooraf)

Dit is precies waarom er een aparte "reden morgen"-sensor bestaat: de
melding komt binnen zodra Cure de wijziging aankondigt, niet pas op de dag
zelf.

```yaml
automation:
  - alias: "Cure: waarschuwing voor afwijking morgen"
    trigger:
      - trigger: state
        entity_id: sensor.cure_afvalbeheer_eindhoven_milieustraat_acht_reden_morgen
    condition:
      - condition: template
        value_template: >
          {{ trigger.from_state.state == '' and trigger.to_state.state != '' }}
    action:
      - action: notify.notify
        data:
          title: "Milieustraat Acht"
          message: >
            Morgen wijkt de milieustraat af van de normale openingstijden:
            {{ trigger.to_state.state }}.
```

## Architectuur

Zie:

- ARCHITECTURE.md
- AGENTS.md

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

### v0.1.0

- Config Flow: pick a Cure municipality; add the same or a different
  municipality again if you want multiple devices.
- Options Flow: number of forecast days configurable (default 5), also
  changeable after installation.
- DataUpdateCoordinator fetches the chosen municipality's milieustraat page
  live.
- One sensor per milieustraat: current status (Open/Closed) and `today`/
  `upcoming` attributes for use in a markdown card.
- Home Assistant brand assets prepared (see `brands/`).

### v0.2.0

- Temporary deviations (heat protocol, renovation, closure) are parsed
  straight from the page and automatically adjust the sensor status/
  attributes.

### v0.3.0

- Two dedicated "reason" sensors per milieustraat (today/tomorrow) instead
  of a hidden attribute, so your automations can warn a day ahead of a
  deviation.
- New milieustraten that Cure adds to a municipality page appear
  automatically, without a restart. If a milieustraat permanently
  disappears, its sensors become `unavailable`; if it is still gone after a
  restart, Home Assistant itself offers a removal option.

### v0.3.1

- The brand logo is now served locally via the integration's own `brand/`
  folder (Home Assistant 2026.3+), with no external pull request needed.

### v0.4.0

- Diagnostics: a downloadable dump of the config entry and the current
  coordinator data, handy for bug reports.
- Update interval configurable via the Options Flow (5-1440 minutes,
  default 60), alongside the forecast-days setting.

### v0.5.0

- The milieustraat's address is now also available as an `address`
  attribute on the status sensor (it was already parsed, but never shown).
- Reconfigure flow: change the municipality of an existing integration via
  **Settings → Devices & Services → Cure Afvalbeheer → Configure**, without
  removing and re-adding it. Picking a different municipality first asks
  for explicit confirmation — all sensors and their history for the
  current municipality are replaced by sensors for the new one.
- Two new sensors per milieustraat, **"next open"** and **"next close"**
  (timestamp), so the next status change is directly usable in automations
  and on the dashboard instead of buried in an attribute.
- A visible repair notification in Home Assistant (**Settings → System →
  Repairs**) if the parser suddenly finds no milieustraat at all anymore,
  for example due to a change in the Cure website's markup.

See ROADMAP.md for what is still planned.

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

Milieustraat locations within a municipality are discovered automatically
from the page; no separate per-location configuration is needed.

## Using it on your dashboard

Each milieustraat gets five sensors:

- **`sensor.<device>_<milieustraat>`** — status `open`/`closed`, with
  `address`, `today` and `upcoming` (the configured forecast days) as
  attributes.
- **`sensor.<device>_<milieustraat>_reden_vandaag`** and
  **`..._reden_morgen`** — empty (`""`) if there is no deviation, otherwise
  the reason (`hitteprotocol`, `verbouwing`, `werkzaamheden` — these values
  are always Dutch, since that is what the integration itself produces).
- **`sensor.<device>_<milieustraat>_volgende_open`** and
  **`..._volgende_close`** — timestamp of the next time the milieustraat
  opens and closes respectively, within the configured forecast window
  (otherwise `unknown`).

Look up your own entity IDs via **Developer Tools → States** — the examples
below use those of "Milieustraat Acht" in Eindhoven
(`sensor.cure_afvalbeheer_eindhoven_milieustraat_acht`) for illustration.

### Example: markdown card

Requires the HACS frontend card
**[card-mod](https://github.com/thomasloven/lovelace-card-mod)** — HA's
markdown card strips the `style` attribute from HTML (sanitizer), so the
styling (centered heading, icon colour/animation) is applied here via
`card_mod` instead of inline.

The example below uses "Milieustraat Acht" in Eindhoven; adjust **two
spots** for your own situation:
1. The entity ID on the `{%- set sensor = ... -%}` line — replace
   `sensor.cure_afvalbeheer_eindhoven_milieustraat_acht` with your own
   sensor (look it up via Developer Tools → States).
2. The text between `<h2>` and `</h2>` — replace "Milieustraat Acht" with
   the name you want shown on the card.

```yaml
type: markdown
content: |
  {#- Bronsensor en attributen ophalen -#}
  {%- set sensor = 'sensor.cure_afvalbeheer_eindhoven_milieustraat_acht' -%}
  {%- set vandaag = state_attr(sensor, 'today') -%}
  {%- set upcoming = state_attr(sensor, 'upcoming') or [] -%}
  {#- Naam en hulpsensoren worden afgeleid van de bronsensor hierboven -#}
  {%- set volledig = state_attr(sensor, 'friendly_name') or '' -%}
  {#- Alles vóór het woord 'Milieustraat' weglaten (integratie- en apparaatnaam) -#}
  {%- set pos = (volledig | lower).find('milieustraat') -%}
  {%- set naam = volledig[pos:] if pos >= 0 else (volledig or 'Milieustraat') -%}
  {%- set s_open = states(sensor ~ '_volgende_open') -%}
  {%- set s_dicht = states(sensor ~ '_volgende_gesloten') -%}
  {#- Is de milieustraat op dit moment daadwerkelijk open? -#}
  {%- set nu_open = vandaag is not none and not vandaag.closed
        and vandaag.opens is not none and vandaag.closes is not none
        and now() >= today_at(vandaag.opens) and now() <= today_at(vandaag.closes) -%}
  {#- Sluitingstijd voorbij? Dan geldt vandaag als gesloten -#}
  {%- set na_sluiting = vandaag is not none and not vandaag.closed and vandaag.closes is not none and now() > today_at(vandaag.closes) -%}
  {#- Alleen de sensor die nu telt hoeft een geldig tijdstip te hebben; zo niet: regel weglaten -#}
  {%- set d_open = as_datetime(s_open, none) -%}
  {%- set d_dicht = as_datetime(s_dicht, none) -%}
  {%- set toon_teller = (d_dicht if nu_open else d_open) is not none -%}
  {#- Datum van yyyy-mm-dd naar dd-mm-yyyy -#}
  {%- macro datum_nl(d) -%}
  {%- set s = d | string -%}{{ s[8:10] }}-{{ s[5:7] }}-{{ s[0:4] }}
  {%- endmacro -%}
  {#- Aftellen naar een timestamp-sensor: de frontend doet dit alleen in entity-rijen, hier zelf rekenen -#}
  {%- macro aftellen(t) -%}
  {%- set d = as_datetime(t, none) -%}
  {%- if d is none -%}onbekend
  {%- else -%}
  {%- set sec = ((d - now()).total_seconds() | int, 0) | max -%}
  {%- set dg = (sec // 86400) | int -%}
  {%- set uu = ((sec % 86400) // 3600) | int -%}
  {%- set mm = ((sec % 3600) // 60) | int -%}
  {%- if dg > 0 -%}{{ dg }} {{ 'dag' if dg == 1 else 'dagen' }}{% if uu > 0 %} en {{ uu }} uur{% endif %}
  {%- elif uu > 0 -%}{{ uu }} uur{% if mm > 0 %} en {{ mm }} min{% endif %}
  {%- elif mm > 0 -%}{{ mm }} min
  {%- else -%}minder dan een minuut
  {%- endif -%}
  {%- endif -%}
  {%- endmacro -%}
  <h2>{{ naam }}</h2>

  **Vandaag:** {% if vandaag is none %}Onbekend{% elif vandaag.closed or na_sluiting %}Gesloten{% else %}Geopend van {{ vandaag.opens }} tot {{ vandaag.closes }}{% endif %}
  {% if toon_teller %}
  {% if nu_open %}**Sluit over:** {{ aftellen(s_dicht) }}{% else %}**Weer open over:** {{ aftellen(s_open) }}{% endif %}
  {% endif %}
  **Openingstijden de komende dagen:**
  {% for dag in upcoming %}
  - {% if dag.reason %}<ha-icon icon="mdi:alert-outline"></ha-icon>{% endif %}{{ datum_nl(dag.date) }}: {% if dag.closed %}Gesloten{% else %}Open van {{ dag.opens }} tot {{ dag.closes }}{% endif %}{% if dag.reason %} — {{ dag.reason }}{% endif %}
  {%- endfor %}
card_mod:
  style:
    ha-markdown $: |
      /* Kop centreren (style-attribuut werkt niet, sanitizer stript het) */
      ha-markdown-element h2 {
        text-align: center;
      }
      /* Bullets en de standaard lijst-inspring weg: het icoon neemt die plek in */
      ha-markdown-element ul {
        list-style: none;
        padding-inline-start: 0 !important;   /* browser zet hier standaard 40px */
        margin-inline-start: 0 !important;
        margin: 0;
      }
      /* Alle tekstregels dezelfde smalle inspring: precies genoeg voor het icoon */
      ha-markdown-element p,
      ha-markdown-element li {
        padding-left: 26px;   /* 20px icoon + 6px lucht */
      }
      /* Icoon absoluut in die ruimte, dus buiten de tekstflow: geen inspringing */
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

The heading is centered via `card_mod`. "Today" shows "Closed" once the
closing time has passed, even when no deviation is active (the
`past_closing` check compares the current time against `today.closes`).
Dates are shown in `dd-mm-yyyy` notation via the `format_date` macro. Every
day in the list now gets its own blinking warning icon (`mdi:alert-outline`)
whenever that specific day has a `reason`, instead of a single icon next to
a heading that occasionally switches — the accompanying CSS keeps the icon
separate from the text so lines without a deviation do not get indented.

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

### Example: automation (warn a day ahead)

This is exactly why a dedicated "reason tomorrow" sensor exists: the
notification comes in as soon as Cure announces the change, not only once
the day itself arrives.

```yaml
automation:
  - alias: "Cure: warn about a deviation tomorrow"
    trigger:
      - trigger: state
        entity_id: sensor.cure_afvalbeheer_eindhoven_milieustraat_acht_reden_morgen
    condition:
      - condition: template
        value_template: >
          {{ trigger.from_state.state == '' and trigger.to_state.state != '' }}
    action:
      - action: notify.notify
        data:
          title: "Milieustraat Acht"
          message: >
            Tomorrow the milieustraat deviates from its normal opening
            hours: {{ trigger.to_state.state }}.
```

## Architecture

See:

- ARCHITECTURE.md
- AGENTS.md

## Development

Uses:

- Python 3.13
- Ruff
- pytest
- Home Assistant development guidelines

## License

MIT
