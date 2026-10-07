# Stayconnect Hotels – Goa Hotel Catalogue

Website-ready data and a preview page for the 36 North Goa hotels in the
Stayconnect Hotels "Goa Per Night Contract Rates" sheet (valid till
31 March 2027).

## What is here

| Path | Use it for |
|---|---|
| `index.html` | Stand-alone catalogue page (search, filter by category/area, sort by price). Open it directly in a browser or host it as-is. |
| `data/hotels.json` | Full structured dataset: rates, meal plans, blackout dates, and a profile for every hotel (address, area, rooms, amenities, distances, ratings, description, highlights, sources, research confidence). Import this into a CMS or front end. |
| `data/hotels.csv` | Same data flattened to one row per hotel for spreadsheets, WordPress/WooCommerce importers, Airtable, etc. |
| `data/HOTELS.md` | Human-readable review document: rate table plus a profile per hotel with research notes. Read this to approve/edit content before publishing. |
| `data/research/contract_rates.json` | The rates, meal plans, validity and blackout dates transcribed from the PDF. |
| `data/research/group_*.json` | Raw web-research output per hotel (with the source URLs used). |
| `tools/build_hotels.py` | Rebuilds the three `data/` outputs and `index.html` from the research files. |

## Rate basis (from the contract sheet)

- Per room per night, double sharing, base category room, INR.
- **DBL CP** = room with breakfast. **DBL MAP** = room with breakfast and dinner.
- Standard rates do not apply on: Gandhi Jayanti weekend (2–5 Oct),
  Dussehra (20–24 Oct), Diwali (8–15 Nov), New Year (22 Dec 2026 – 5 Jan 2027).
- Supplements may apply on festivals, weekends and special dates. Subject to availability and final confirmation.

## Online market rate column

Every hotel also carries an **online market rate**: the public per-night price for a standard
double room seen on booking sites (MakeMyTrip, Goibibo, Booking.com, Agoda, Expedia, EaseMyTrip,
Tripadvisor and others) when researched on 7 October 2026. The dataset stores a typical "from"
price plus the lowest and highest figures seen, each with its source site, in `market_rate`
(JSON) and the `market_rate_*` columns (CSV). USD prices were converted at 84 INR per USD and
are flagged in the notes.

Online prices change daily and vary by date, room type and taxes, so treat them as indicative.
No online price was found for Aira Beach Resort, Sibaya Courtyard (newly opened) and
Holitel Calangute (sold as a group/wedding venue, not on OTAs).

## Before you publish

Each hotel carries a `research_confidence` (high / medium / low) and `research_notes`.
Five hotels are **low** confidence and should be confirmed with the supplier before going live:
Goveia Grand, Aira Beach Resort, Silver Shell Grand, Holitel Calangute, Surf House Beach Resort.
Several others are flagged where the star rating on booking sites differs from the contract category
(for example SinQ Party Hotel, Verano, Calux Joia Do Mar, Vagator Downtown, SinQ Anvaya).

No hotel photos are included. Source images from the properties directly or from the official
sites listed in the `website` field.

## Rebuild

```bash
python3 tools/build_hotels.py
```

Edit the JSON files under `data/research/` (for example to correct an address or add a phone
number), then rerun the script to regenerate `data/hotels.json`, `data/hotels.csv`,
`data/HOTELS.md` and `index.html`.
