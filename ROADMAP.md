# Roadmap

## Vision

Build a high-quality Home Assistant integration for Cure Afvalbeheer.

The integration should provide reliable and up-to-date information about all Cure recycling centres (milieustraten), including temporary changes announced through the Cure website.

The project aims to follow the Home Assistant Integration Quality Scale and be suitable for publication through HACS.

---

# Version 1.0

## Core

- [x] GitHub repository
- [x] HACS structure
- [x] Config Flow
- [x] Logging
- [x] Parser framework
- [x] HTML fixture
- [x] Development environment

## Parser

- [ ] Parse all Eindhoven recycling centres
- [ ] Parse regular opening hours
- [ ] Parse addresses
- [ ] Parse today's opening hours
- [ ] Parse next opening/closing change

## Coordinator

- [ ] HTTP client
- [ ] DataUpdateCoordinator
- [ ] Update interval
- [ ] Error handling
- [ ] Retry logic

## Home Assistant

- [ ] Device
- [ ] Sensor
- [ ] DeviceInfo
- [ ] Diagnostics

---

# Version 1.1

- [ ] RSS integration
- [ ] Temporary closures
- [ ] Heat protocol
- [ ] Maintenance notices
- [ ] Additional attributes

---

# Version 1.2

- [ ] Dashboard helper attributes
- [ ] Markdown friendly output
- [ ] Manual refresh action
- [ ] Calendar style output

---

# Version 2.0

- [ ] Multiple Cure municipalities
- [ ] Additional entities
- [ ] Repairs
- [ ] Accepted waste types
- [ ] Maps
- [ ] Navigation

---

# Nice to have

- [ ] Diagnostics download
- [ ] Repairs history
- [ ] Statistics
- [ ] Configurable update interval
- [ ] Multiple languages