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
Parser ──gebruikt──> parsers.py (openingstijden-regels)
    │            notices.py (parsing van vrije-tekst-afwijkingen)
    │            times.py   (kloktijden, gedeeld door beide)
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

Elke manier waarop een pagina níet binnenkomt - een foutstatus, een
geweigerde verbinding, een verlopen timeout - verlaat deze laag als één
`CureApiError`. De coordinator maakt daar Home Assistants "update failed"
van: een nette regel in het log in plaats van een traceback. De request
heeft een eigen timeout, want een hangende verbinding houdt anders de
update van de coordinator open zonder dat iemand daarbij gebaat is.

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
h3-naar-h1-fallback in `parser.py`, en `heading_with_text`/
`closure_notice_section` in `selectors.py`.

Kop-teksten worden nooit exact vergeleken wanneer Cure er variabele
onderdelen in zet. `closing_days_blocks` matcht daarom alleen op het woord
"Sluitingsdagen" en negeert het jaartal dat erachter staat: dat jaartal
wijzigt elk jaar en loopt in de praktijk soms achter op de werkelijkheid.
Datzelfde blok heeft geen eigen container - het deelt één prose-`div` met
de openingstijden - dus de inhoud wordt verzameld door vanaf de kop vooruit
te lopen tot de volgende kop van hetzelfde of een hoger niveau, in plaats
van via een `find_parent`.

Een kop wordt gezocht op tekst, niet op exacte gelijkheid:
`heading_with_text` neemt eerst de kop die exact klopt, dan een kop die
ermee begint, dan een kop die hem bevat - zodat "Openingstijden
milieustraat" gevonden wordt zonder dat "Afwijkende openingstijden" hoger
op de pagina het van de echte kop wint. `lines_under_heading` levert
vervolgens de regels van dat kop-blok, tot de volgende kop van hetzelfde
of een hoger niveau. Die grens is er niet voor de sier: de openingstijden
en de sluitingsdagen delen één container, en zonder die grens zou een
gedateerde regel uit de sluitingsdagen ("Zaterdag 26 december: 10:00 tot
14:00") als de reguliere zaterdag geboekt worden.

Als één regel telt een `p`, een `li` of een `tr`. Een regel-per-regel-lijst is
inhoud, geen opmaak: Cure kan hem van paragrafen naar een opsomming of een
tabel verplaatsen zonder er een woord aan te veranderen. Van geneste
elementen levert het buitenste de regel, anders zou dezelfde tekst dubbel
langskomen.

De nieuwsbanner die op elke gemeentepagina staat, levert twee soorten tekst
op: `news_heading` geeft de redactionele kop erboven, `news_item_texts` de
titel van elk nieuwsbericht eronder. Dezelfde aankondiging staat in beide,
maar telkens anders geformuleerd, dus de een is leesbaar op momenten dat de
ander dat niet is. Diezelfde banner-kop begint net zo vaak met "Let op!" als
een sluitingsmelding; daarom slaat de fallback van `closure_notice_section`
het nieuwsblok over: een kop over aangepaste openingstijden als sluiting
lezen beweert precies het tegenovergestelde van wat er staat.

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

De datum waartegen relatieve datums gelezen worden komt van de coordinator
mee (`dt_util.now().date()`), niet van de machine: Home Assistant heeft een
eigen tijdzone, en die hoeft niet die van de server te zijn. Anders zou
rond middernacht de datum waarop de meldingen geparst zijn kunnen
verschillen van de datum waarop de entiteiten ze toepassen.

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

Voor de openingstijden geldt dezelfde regel apart: leveren de locaties wél
op maar zonder openingstijden, dan blijven de laatst bekende tijden per
locatie staan en gaat er een reparatie-melding aan. Lege openingstijden
zouden namelijk gelezen worden als "de hele week gesloten" - precies wat
een echt gesloten milieustraat ook oplevert, en daarmee het enige foute
antwoord dat een bezoeker niet van een goed antwoord kan onderscheiden.

---

# Entiteiten

Entiteiten doen nooit netwerkverzoeken.

Entiteiten lezen alleen data uit de coordinator.

Daarnaast volgen ze de klok: elke minuut schrijven ze hun state opnieuw.
Elke waarde die ze leveren gaat namelijk over *nu* - is het op dit moment
open, wat is de reden van vandaag, wanneer gaat het weer open - terwijl de
coordinator alleen afgaat als hij de pagina opnieuw ophaalt, standaard eens
per uur. Zonder eigen tik zou een sensor dus nog lang na openingstijd
"gesloten" melden. Herberekenen kost niets (geen I/O, geen netwerk) en Home
Assistant legt geen geschiedenis vast voor een waarde die niet veranderd
is.

---

# Openingstijden

`parsers.py` leest de regels onder de kop "Openingstijden". Anders dan de
meldingen hebben die een vaste vorm - een dag-label, een waarde - maar
binnen die vorm wordt alles ruim gelezen, want juist de bewoording van het
label en de leestekens tussen de tijden wijzigt Cure zonder aankondiging.

Het label mag een dag zijn ("Maandag"), een afkorting ("Ma"), een reeks
("Maandag t/m vrijdag", die elke dag ertussen oplevert), een opsomming
("Zaterdag en zondag") of de feestdagen. Voor die laatste is het woord
"feestdag" het enige dat telt, zodat "Zon & Feestdagen", "Zon- en
feestdagen" en "Zondag en feestdagen" alle drie dezelfde regel zijn. Een
label dat niets van dit alles is, levert niets op: liever een regel
overslaan dan hem onder de verkeerde dag boeken.

De waarde is een tijdreeks of een woord voor gesloten, en waar die waarde
begint is wat de regel in tweeën knipt. De dubbele punt die Cure achter de
dag zet is er namelijk niet altijd - in een tabel staan label en waarde in
losse cellen - maar staat hij er wél vóór de waarde, dan is hij de
scheiding, zodat er niets van het label in de waarde meeglipt.

Een sluitingswoord wint van een tijdreeks in dezelfde regel, net zoals een
sluiting in `schedule.py` wint van een tijden-aanpassing.

Een regel die alsnog niet te lezen blijkt, wordt overgeslagen met een
waarschuwing in het log in plaats van de hele update mee te nemen: de
overige zes dagen zijn nog prima bruikbaar.

---

# Times

`times.py` bevat wat `parsers.py` en `notices.py` allebei over kloktijden
moeten weten: hoe uur en minuut gescheiden worden, hoe de twee kanten van
een reeks gescheiden worden, en het omzetten van een geschreven tijd naar
één "HH:MM"-waarde (met afwijzing van onmogelijke tijden). Het staat apart
zodat beide lagen niet uiteen kunnen lopen over welke schrijfwijze ze
accepteren.

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

Het hitteprotocol wordt aangekondigd voor een periode, en Cure schrijft die
periode elke keer anders op: "tot en met donderdag 16 juli", "van 13 t/m 15
Augustus", "13 tot en met 15 Augustus". `parse_relative_date_range` leest
daarom zowel een periode met beide uiteinden als eentje met alleen een
einddatum, en accepteert "tot en met", "t/m" en "tot" als scheiding. Staat
de maand alleen achter de einddatum, dan leent de begindatum die; komt het
begin daarmee ná het einde uit, dan ligt het een maand eerder - of een jaar,
als het zelf een uitgeschreven maand heeft. Dat een maandnaam achter de
einddatum verplicht is, is precies wat tijden buiten de deur houdt: in "van
08:00 tot 14:00" volgt er geen.

Noemt de tekst helemaal geen periode, dan telt één losse datum als die ene
dag, en "vandaag" als vandaag - dat laatste alleen voor de banner-kop, die
per definitie actueel is. In een nieuwsbericht uit het archief staat
"vandaag" er immers nog steeds terwijl de dag allang voorbij is; daarvoor
geeft `parser.py` `current=False` mee. Herkend wordt op "hitte" in plaats
van het hele woord, omdat dezelfde aankondiging als "hitteprotocol",
"hitte-protocol" en "hittegolf" langskomt - dat alleen levert nooit een
melding op, want zonder leesbare periode én leesbare tijd komt er niets uit.

Een aankondiging die maar één kant van de tijden noemt ("sluiten vandaag om
14:00 uur") wordt net zo goed gelezen als een volledige reeks; de andere
kant blijft dan de reguliere tijd.

De begindatum wordt vastgelegd in de melding, zodat een banner die vooruit
geplaatst wordt pas geldt zodra de hitte er is. Duurt de gelezen periode
langer dan `_MAX_HEAT_PROTOCOL_DAYS`, dan levert de melding niets op: een
hitteprotocol beslaat een reeks warme dagen, geen maanden. Dat vangt vooral
de banner op die na afloop blijft staan - de einddatum daarvan wordt als die
van volgend jaar gelezen, en zonder die grens zou de integratie maandenlang
aangepaste tijden tonen.

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

Datums worden in elke gangbare schrijfwijze gelezen: uitgeschreven ("6
april 2026"), afgekort ("6 apr 2026") en in cijfers ("06-04-2026",
"6/4/2026"). Bij een datum in cijfers moet het jaartal voluit staan - met
twee cijfers zou een huisnummer of een tijd te makkelijk voor een datum
doorgaan.

Een sluitingsmelding leest zijn datums op drie manieren, van stelligst naar
minst stellig: de datum achter een "Datum sluiting"-label (waarbij alleen de
tekst direct achter dat label meetelt, zodat een datum verderop in de
melding niet voor de sluitingsdatum wordt aangezien), een lijst gedateerde
regels, of de periode waarvoor de sluiting geldt. In die lijst blijft de
weekdag verplicht: die onderscheidt een opsomming van sluitingsdatums van
een datum die terloops in de omringende tekst voorkomt. Het jaartal erachter
is optioneel, want Cure laat het even vaak weg als staan.

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

Er is een tweede melding van dezelfde soort voor locaties die wél gevonden
worden maar zonder openingstijden. Beide melden hetzelfde soort probleem -
de opmaak is veranderd - en beide blijven staan zolang de integratie op
laatst bekende gegevens terugvalt, zodat verouderde data nooit stilzwijgend
voor actueel doorgaat.

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
Parser ──uses──> parsers.py (opening hours lines)
    │          notices.py (free-text deviation parsing)
    │          times.py   (clock times, shared by both)
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

Every way in which a page fails to arrive - a bad status, a refused
connection, a timeout - leaves this layer as one `CureApiError`. The
coordinator turns that into Home Assistant's "update failed": a plain line
in the log rather than a traceback. The request carries a timeout of its
own, since a hanging connection would otherwise hold the coordinator's
update open to nobody's benefit.

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
h3-to-h1 fallback in `parser.py`, and `heading_with_text`/
`closure_notice_section` in `selectors.py`.

Heading text is never compared in full where Cure puts a variable part in
it. `closing_days_blocks` therefore matches on the word "Sluitingsdagen"
alone and ignores the year behind it: that year changes annually and, in
practice, sometimes lags behind reality. That same block has no container
of its own - it shares one prose `div` with the opening hours - so its
content is collected by walking forward from the heading until the next
heading of the same or a higher level, rather than through a `find_parent`.

A heading is looked up by its text rather than by exact equality:
`heading_with_text` takes the heading that matches exactly, else one that
starts with the wanted text, else one that merely contains it - so
"Openingstijden milieustraat" is found without "Afwijkende openingstijden"
higher up the page beating the real heading to it. `lines_under_heading`
then returns that heading's own lines, up to the next heading of the same
or a higher level. That boundary earns its keep: the opening hours and the
closing days share one container, and without it a dated line from the
closing days ("Zaterdag 26 december: 10:00 tot 14:00") would be filed as
that Saturday's regular hours.

A line is a `p`, an `li` or a `tr` alike. A line-per-line list is content,
not layout: Cure can move it from paragraphs into a bullet list or a table
without changing a word of it. Of nested elements the outermost owns the
line, or the same text would come round twice.

The site-wide news banner yields two kinds of text: `news_heading` returns
the editorial heading above it, `news_item_texts` the title of every news
item below it. The same announcement appears in both, worded differently
each time, so one stays readable at moments the other does not. That same
banner heading opens with "Let op!" as often as a closure notice does,
which is why `closure_notice_section`'s fallback skips the news block:
reading a heading about adjusted hours as a closure would state the exact
opposite of what it says.

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

The date relative dates are read against comes from the coordinator
(`dt_util.now().date()`) rather than from the machine: Home Assistant has a
time zone of its own, which need not be the server's. Around midnight the
date the notices were parsed against could otherwise differ from the date
the entities apply them on.

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

The opening hours follow the same rule on their own: where the locations do
come back but without any hours, the last known hours per location stay in
place and a repair notification goes up. Empty hours would otherwise read
as "closed all week" - exactly what a genuinely closed recycling centre
produces too, and so the one wrong answer a visitor cannot tell apart from
a right one.

---

# Entities

Entities never perform network requests.

Entities only read data from the coordinator.

They follow the clock as well, rewriting their state every minute. Every
value they produce is about *now* - is it open at this moment, what is
today's reason, when does it next open - while the coordinator only fires
when it fetches the page again, once an hour by default. Without a tick of
their own a sensor would still report "gesloten" well after opening time.
Recomputing costs nothing (no I/O, no network), and Home Assistant records
no history for a value that has not changed.

---

# Opening hours

`parsers.py` reads the lines under the "Openingstijden" heading. Unlike
the notices these have a fixed shape - a day label, a value - but within
that shape everything is matched loosely, because the wording of the label
and the punctuation between the times are exactly what Cure changes
without warning.

The label may be a day ("Maandag"), an abbreviation ("Ma"), a range
("Maandag t/m vrijdag", which yields every day in between), a list
("Zaterdag en zondag") or the public holidays. For the last of those the
word "feestdag" is all that counts, so "Zon & Feestdagen", "Zon- en
feestdagen" and "Zondag en feestdagen" are one and the same line. A label
that is none of these yields nothing: skipping a line beats filing it
under the wrong day.

The value is a time range or a word meaning closed, and where that value
begins is what splits the line in two. The colon Cure writes behind the
day is not always there - a table puts label and value in separate cells -
but where it does stand in front of the value it is the separator, so none
of the label slips into it.

A word for being shut beats a time range on the same line, the same way a
closure beats an hours adjustment in `schedule.py`.

A line that turns out to be unreadable after all is skipped with a warning
in the log rather than taking the whole update with it: the other six days
are still perfectly usable.

---

# Times

`times.py` holds what `parsers.py` and `notices.py` both need to know
about clock times: how hour and minute are separated, how the two ends of
a range are separated, and how a written time becomes one "HH:MM" value
(rejecting impossible ones). It sits on its own so the two layers cannot
drift apart on which spellings they accept.

---

# Notices

`notices.py` extracts temporary deviations (heat protocol, closures,
renovations, the closing days around public holidays) from free Dutch text
found on the recycling centre page.

Contains no BeautifulSoup/HTML code and no Home Assistant imports - it only
takes plain strings and returns a `Notice` (or `None` when the text does not
match a recognised pattern). `parser.py` is the only caller: it selects the
relevant heading/body text via `selectors.py` and hands it to `notices.py`.

A heat protocol is announced for a period, and Cure writes that period
differently every time: "tot en met donderdag 16 juli", "van 13 t/m 15
Augustus", "13 tot en met 15 Augustus". `parse_relative_date_range`
therefore reads both a period written out with both of its ends and one
carrying only an end date, and accepts "tot en met", "t/m" and "tot" as the
separator. Where the month is written behind the end date only, the start
date borrows it; where that puts the start behind the end, it lies a month
(or, with a month of its own written out, a year) earlier. Requiring a
month name behind the end date is exactly what keeps times out of this: in
"van 08:00 tot 14:00" none follows.

Where the text names no period at all, one lone date counts as that single
day, and "vandaag" ("today") as today - the latter only for the banner
heading, which is current by definition. In an archived news item that word
still stands there long after the day has passed, so `parser.py` passes
`current=False` for those. Matching is on "hitte" rather than the whole
word, since the same announcement turns up as "hitteprotocol",
"hitte-protocol" and "hittegolf" - which on its own never produces a
notice, as without both a readable period and a readable time nothing comes
out.

An announcement naming only one side of the times ("sluiten vandaag om
14:00 uur") is read just as well as a full range; the other side then keeps
the regular time.

The start date is recorded on the notice, so a banner put up in advance
takes effect only once the heat arrives. When the period read comes out
longer than `_MAX_HEAT_PROTOCOL_DAYS`, the announcement yields nothing at
all: a heat protocol covers a spell of hot days, not months. That mainly
catches the banner left standing after the heat has passed - its end date
is then read as next year's, and without that limit the integration would
show adjusted hours for months on end.

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

Dates are read in every spelling in common use: written out ("6 april
2026"), abbreviated ("6 apr 2026") and in numbers ("06-04-2026",
"6/4/2026"). A date in numbers has to carry its year in full - with two
digits a house number or a time would pass for a date too easily.

A closure notice reads its dates in three ways, from most definite to
least: the date behind a "Datum sluiting" label (where only the text right
behind that label counts, so a date further along cannot be mistaken for
the closure date), a list of dated entries, or the period the closure runs
for. In that list the weekday stays required: it is what separates a list
of closing dates from a date mentioned in passing in the surrounding prose.
The year behind it does not, since Cure leaves it out as often as not.

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

A second notification of the same kind covers locations that are found but
come back without opening hours. Both report the same kind of problem - the
layout has changed - and both stay up for as long as the integration is
falling back on last known data, so stale data is never silently passed off
as current.

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
