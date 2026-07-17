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
- [ ] Diagnostics

## Other

- [x] Home Assistant brand assets prepared for `home-assistant/brands`

---

# v0.2.0 (done)

- [x] Heat protocol detection (adjusted hours + end date)
- [x] Temporary closures / renovations (explicit closing date, or a list of
      specific closed dates)
- [x] Deviation reason exposed as a sensor attribute
- [x] No separate RSS feed needed - deviations are parsed from the same
      milieustraat page that is already fetched

---

# Next up

- [ ] Diagnostics
- [ ] Calendar-style output
- [ ] Manual refresh action
- [ ] Configurable update interval
- [ ] Repairs / accepted waste types / maps / navigation
- [ ] Multiple languages

---

# Nice to have

- [ ] Diagnostics download
- [ ] Repairs history
- [ ] Statistics
