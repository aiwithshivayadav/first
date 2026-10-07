#!/usr/bin/env python3
"""Merge Stayconnect PDF rates with researched hotel details and emit
website-ready files: data/hotels.json, data/hotels.csv, data/HOTELS.md and index.html.

Usage: python3 tools/build_hotels.py"""
import csv
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "data" / "research"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data"
OUT.mkdir(parents=True, exist_ok=True)

rates = json.loads((RESEARCH / "contract_rates.json").read_text())

def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


research = {}
for f in sorted(RESEARCH.glob("group_*.json")):
    for h in json.loads(f.read_text()):
        research[norm(re.sub(r"\s*\([^)]*\)", "", h["pdf_name"]))] = h


def slugify(s: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


# Contract names to keep as-is where research could only find a sibling/parent property.
OFFICIAL_OVERRIDE = {
    "Silver Shell Grand": "Silver Shell Grand",
}

hotels = []
missing = []
for i, r in enumerate(rates["hotels"], start=1):
    key = norm(r["name"])
    d = research.get(key)
    if d is None:
        # tolerant match: research pdf_name may differ in punctuation / suffix
        cands = [k for k in research if k.startswith(key[:10]) or key.startswith(k[:10])]
        d = research[cands[0]] if len(cands) == 1 else None
    if d is None:
        missing.append(r["name"])
        d = {}
    hotels.append(
        {
            "id": i,
            "slug": slugify(r["name"]),
            "name": r["name"],
            "official_name": OFFICIAL_OVERRIDE.get(r["name"]) or re.sub(r"\s*\([^)]*\)\s*$", "", d.get("official_name") or r["name"]).strip(),
            "also_known_as": (lambda m: m.group(0) if m else None)(re.search(r"\([^)]*\)\s*$", d.get("official_name") or "")),
            "category": r["category"],
            "star_rating": d.get("star_rating"),
            "area": (re.split(r"\s*[(,]", d["area"])[0].strip() if d.get("area") else None),
            "area_detail": d.get("area"),
            "address": d.get("address"),
            "rates": {
                "currency": "INR",
                "dbl_cp": r["dbl_cp"],
                "dbl_map": r["dbl_map"],
                "basis": rates["basis"],
                "validity": rates["validity"],
            },
            "distance_to_beach": d.get("distance_to_beach"),
            "distance_from_dabolim_airport_km": d.get("distance_from_dabolim_airport_km"),
            "distance_from_mopa_airport_km": d.get("distance_from_mopa_airport_km"),
            "distance_from_thivim_station_km": d.get("distance_from_thivim_station_km"),
            "total_rooms": d.get("total_rooms"),
            "room_types": d.get("room_types") or [],
            "amenities": d.get("amenities") or [],
            "check_in": d.get("check_in"),
            "check_out": d.get("check_out"),
            "dining": d.get("restaurant_or_dining"),
            "website": d.get("website"),
            "phone": d.get("phone"),
            "google_rating": d.get("google_rating"),
            "google_review_count": d.get("google_review_count"),
            "ota_rating": d.get("tripadvisor_or_ota_rating"),
            "description": d.get("description"),
            "highlights": d.get("highlights") or [],
            "nearby_attractions": d.get("nearby_attractions") or [],
            "sources": d.get("sources") or [],
            "research_confidence": d.get("confidence"),
            "research_notes": d.get("notes"),
        }
    )

dataset = {
    "meta": {
        "source": rates["source"],
        "provider": rates["provider"],
        "currency": rates["currency"],
        "rate_basis": rates["basis"],
        "meal_plans": rates["meal_plans"],
        "validity": rates["validity"],
        "blackout_dates": rates["blackout_dates"],
        "notes": rates["notes"],
        "hotel_count": len(hotels),
    },
    "hotels": hotels,
}
(OUT / "hotels.json").write_text(json.dumps(dataset, indent=2, ensure_ascii=False))

# ---------- CSV ----------
cols = [
    "id", "slug", "name", "official_name", "category", "star_rating", "area", "address",
    "rate_dbl_cp_inr", "rate_dbl_map_inr", "distance_to_beach",
    "distance_from_dabolim_airport_km", "distance_from_mopa_airport_km",
    "distance_from_thivim_station_km", "total_rooms", "room_types", "amenities",
    "check_in", "check_out", "dining", "website", "phone", "google_rating",
    "google_review_count", "ota_rating", "description", "highlights",
    "nearby_attractions", "research_confidence", "research_notes",
]
with (OUT / "hotels.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(cols)
    for h in hotels:
        w.writerow([
            h["id"], h["slug"], h["name"], h["official_name"], h["category"], h["star_rating"],
            h["area"], h["address"], h["rates"]["dbl_cp"], h["rates"]["dbl_map"],
            h["distance_to_beach"], h["distance_from_dabolim_airport_km"],
            h["distance_from_mopa_airport_km"], h["distance_from_thivim_station_km"],
            h["total_rooms"], " | ".join(h["room_types"]), " | ".join(h["amenities"]),
            h["check_in"], h["check_out"], h["dining"], h["website"], h["phone"],
            h["google_rating"], h["google_review_count"], h["ota_rating"], h["description"],
            " | ".join(h["highlights"]), " | ".join(h["nearby_attractions"]),
            h["research_confidence"], h["research_notes"],
        ])

# ---------- Markdown ----------
def md_val(v):
    return "—" if v in (None, "", []) else str(v)

lines = ["# Stayconnect Hotels – Goa Contract Rates & Hotel Profiles", ""]
lines += [
    f"Source: {rates['source']}  ",
    f"Validity: {rates['validity']}  ",
    f"Basis: {rates['basis']}. CP = breakfast; MAP = breakfast + dinner. All rates in INR.",
    "",
    "## Blackout / supplement dates",
    "",
]
lines += [f"- {b['name']}: {b['dates']}" for b in rates["blackout_dates"]]
lines += ["", "## Rate summary", "", "| # | Hotel | Category | Area | DBL CP | DBL MAP |", "|---|---|---|---|---|---|"]
for h in hotels:
    lines.append(f"| {h['id']} | {h['official_name']} | {h['category']} | {md_val(h['area'])} | ₹{h['rates']['dbl_cp']:,} | ₹{h['rates']['dbl_map']:,} |")
lines += ["", "## Hotel profiles", ""]
for h in hotels:
    lines += [f"### {h['id']}. {h['official_name']}", ""]
    if h["official_name"] != h["name"]:
        lines.append(f"*Listed in contract as:* {h['name']}  ")
    if h.get("also_known_as"):
        lines.append(f"*Also known as:* {h['also_known_as'].strip('()')}  ")
    lines += [
        f"**Category:** {h['category']}" + (f" ({h['star_rating']}★)" if h["star_rating"] else "") + "  ",
        f"**Area:** {md_val(h['area'])}  ",
        f"**Address:** {md_val(h['address'])}  ",
        f"**Contract rate (per room/night, double):** CP ₹{h['rates']['dbl_cp']:,} · MAP ₹{h['rates']['dbl_map']:,}  ",
        f"**Beach:** {md_val(h['distance_to_beach'])}  ",
        f"**Airports:** Dabolim {md_val(h['distance_from_dabolim_airport_km'])} km · Mopa {md_val(h['distance_from_mopa_airport_km'])} km  ",
        f"**Rooms:** {md_val(h['total_rooms'])} · {md_val(', '.join(h['room_types']))}  ",
        f"**Amenities:** {md_val(', '.join(h['amenities']))}  ",
        f"**Dining:** {md_val(h['dining'])}  ",
        f"**Check-in / out:** {md_val(h['check_in'])} / {md_val(h['check_out'])}  ",
        f"**Ratings:** Google {md_val(h['google_rating'])}" + (f" ({h['google_review_count']} reviews)" if h["google_review_count"] else "") + f" · {md_val(h['ota_rating'])}  ",
        f"**Website:** {md_val(h['website'])}  ",
        f"**Phone:** {md_val(h['phone'])}  ",
        "",
        md_val(h["description"]),
        "",
    ]
    if h["highlights"]:
        lines += ["**Highlights:**"] + [f"- {x}" for x in h["highlights"]] + [""]
    if h["nearby_attractions"]:
        lines += ["**Nearby:**"] + [f"- {x}" for x in h["nearby_attractions"]] + [""]
    lines += [f"*Research confidence:* {md_val(h['research_confidence'])}" + (f" — {h['research_notes']}" if h["research_notes"] else ""), ""]
(OUT / "HOTELS.md").write_text("\n".join(lines))

# ---------- HTML catalogue ----------
E = html.escape

def chips(items, cls="chip"):
    return "".join(f'<span class="{cls}">{E(str(x))}</span>' for x in items)

cards = []
for h in hotels:
    stars = "★" * int(h["star_rating"]) if h["star_rating"] else ""
    rating = ""
    if h["google_rating"]:
        rating = f'<span class="rating">G {h["google_rating"]}' + (f' <small>({h["google_review_count"]:,})</small>' if h["google_review_count"] else "") + "</span>"
    dist = []
    if h["distance_to_beach"]:
        dist.append(f"🏖 {E(h['distance_to_beach'])}")
    if h["distance_from_dabolim_airport_km"]:
        dist.append(f"✈ Dabolim {h['distance_from_dabolim_airport_km']} km")
    if h["distance_from_mopa_airport_km"]:
        dist.append(f"✈ Mopa {h['distance_from_mopa_airport_km']} km")
    link = f'<a href="{E(h["website"])}" target="_blank" rel="noopener">Official site</a>' if h["website"] else ""
    cards.append(f"""
<article class="card" data-cat="{E(h['category'])}" data-area="{E(h['area'] or '')}" data-name="{E(h['official_name'].lower())}" data-cp="{h['rates']['dbl_cp']}" id="{E(h['slug'])}">
  <header>
    <div>
      <span class="cat">{E(h['category'])}</span> <span class="stars">{stars}</span>
      <h3>{E(h['official_name'])}</h3>
      <p class="area">📍 {E(h['area'] or 'Goa')}{(' · ' + E(h['address'])) if h['address'] else ''}</p>
    </div>
    {rating}
  </header>
  <div class="rates">
    <div><span class="lbl">Room + Breakfast (CP)</span><span class="price">₹{h['rates']['dbl_cp']:,}</span></div>
    <div><span class="lbl">Breakfast + Dinner (MAP)</span><span class="price">₹{h['rates']['dbl_map']:,}</span></div>
    <small>per room / night · double sharing · base category</small>
  </div>
  <p class="desc">{E(h['description'] or '')}</p>
  <p class="dist">{' · '.join(dist)}</p>
  <div class="chips">{chips(h['highlights'], 'chip hi')}</div>
  <details>
    <summary>Rooms, amenities &amp; nearby</summary>
    <p><b>Rooms:</b> {E(str(h['total_rooms']) + ' rooms · ' if h['total_rooms'] else '')}{E(', '.join(h['room_types']) or '—')}</p>
    <div class="chips">{chips(h['amenities'])}</div>
    <p><b>Dining:</b> {E(h['dining'] or '—')}</p>
    <p><b>Check-in / out:</b> {E(h['check_in'] or '—')} / {E(h['check_out'] or '—')}</p>
    <p><b>Nearby:</b> {E('; '.join(h['nearby_attractions']) or '—')}</p>
    <p class="meta">{' · '.join(x for x in [link, E(h['phone']) if h['phone'] else ''] if x)}</p>
  </details>
</article>""")

areas = sorted({h["area"] for h in hotels if h["area"]})
cats = ["3 Star", "4 Star", "Beach Hotel"]
blk = "".join(f"<li><b>{E(b['name'])}</b>: {E(b['dates'])}</li>" for b in rates["blackout_dates"])
page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Goa Hotel Rates</title>
<meta name="description" content="Stayconnect Hotels contract rates for 36 hotels in North Goa with hotel profiles, amenities and distances.">
<style>
:root{{--bg:#f6f8fb;--card:#fff;--ink:#14213d;--muted:#5b6478;--line:#e3e8f0;--accent:#1d3b6e;--gold:#c9a24a;--chip:#eef2f8}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#0f141c;--card:#171e29;--ink:#e8edf5;--muted:#9aa5b8;--line:#2a3443;--accent:#8db2ec;--gold:#e0bd63;--chip:#222c3a}}}}
:root[data-theme="dark"]{{--bg:#0f141c;--card:#171e29;--ink:#e8edf5;--muted:#9aa5b8;--line:#2a3443;--accent:#8db2ec;--gold:#e0bd63;--chip:#222c3a}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:24px 16px}}
h1{{margin:0 0 4px;font-size:1.7rem}}.sub{{color:var(--muted);margin:0 0 20px}}
.toolbar{{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}}
.toolbar input,.toolbar select{{padding:9px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink);font:inherit}}
.toolbar input{{flex:1 1 220px}}
.notice{{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--gold);border-radius:10px;padding:12px 16px;margin:0 0 18px}}
.notice ul{{margin:6px 0 0;padding-left:20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:10px}}
.card header{{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}}
.card h3{{margin:2px 0 4px;font-size:1.1rem}}
.cat{{font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:var(--accent);font-weight:700}}
.stars{{color:var(--gold);font-size:.85rem}}
.area{{margin:0;color:var(--muted);font-size:.85rem}}
.rating{{background:var(--chip);border-radius:999px;padding:4px 10px;font-size:.8rem;white-space:nowrap;font-weight:600}}
.rates{{display:grid;grid-template-columns:1fr 1fr;gap:8px;background:var(--chip);border-radius:10px;padding:10px 12px}}
.rates small{{grid-column:1/-1;color:var(--muted)}}
.rates .lbl{{display:block;font-size:.72rem;color:var(--muted)}}.price{{font-weight:700;font-size:1.15rem}}
.desc{{margin:0}}.dist{{margin:0;color:var(--muted);font-size:.85rem}}
.chips{{display:flex;flex-wrap:wrap;gap:6px}}.chip{{background:var(--chip);border-radius:999px;padding:3px 10px;font-size:.78rem}}.chip.hi{{border:1px solid var(--line);background:transparent}}
details{{border-top:1px solid var(--line);padding-top:8px;font-size:.9rem}}summary{{cursor:pointer;color:var(--accent);font-weight:600}}
details p{{margin:8px 0}}.meta a{{color:var(--accent)}}
.count{{color:var(--muted);font-size:.85rem}}
footer{{margin-top:28px;color:var(--muted);font-size:.85rem;border-top:1px solid var(--line);padding-top:14px}}
</style>
</head>
<body>
<div class="wrap">
<h1>Goa Hotel Contract Rates</h1>
<p class="sub">{len(hotels)} hotels across North Goa · {E(rates['validity'])} · per room per night, double sharing</p>

<div class="notice"><b>Standard rates do not apply on:</b><ul>{blk}</ul>
<small>CP = room with breakfast · MAP = room with breakfast and dinner · Supplements may apply on festivals, weekends and special dates · Subject to availability and final confirmation.</small></div>

<div class="toolbar">
  <input id="q" type="search" placeholder="Search hotel name…">
  <select id="cat"><option value="">All categories</option>{''.join(f'<option>{E(c)}</option>' for c in cats)}</select>
  <select id="area"><option value="">All areas</option>{''.join(f'<option>{E(a)}</option>' for a in areas)}</select>
  <select id="sort"><option value="list">Sort: contract order</option><option value="cp-asc">Price: low to high</option><option value="cp-desc">Price: high to low</option><option value="name">Name A–Z</option></select>
</div>
<p class="count" id="count"></p>

<section class="grid" id="grid">{''.join(cards)}</section>

<footer>Bookings &amp; enquiries: {E(rates['provider']['name'])} · {E(rates['provider']['phone'])} · {E(rates['provider']['email'])} · {E(rates['provider']['website'])}</footer>
</div>
<script>
const grid=document.getElementById('grid'),cards=[...grid.children],q=document.getElementById('q'),cat=document.getElementById('cat'),area=document.getElementById('area'),sort=document.getElementById('sort'),count=document.getElementById('count');
function apply(){{
  const s=q.value.trim().toLowerCase();let n=0;
  cards.forEach(c=>{{const ok=(!s||c.dataset.name.includes(s))&&(!cat.value||c.dataset.cat===cat.value)&&(!area.value||c.dataset.area===area.value);c.style.display=ok?'':'none';if(ok)n++;}});
  const v=sort.value,arr=[...cards];
  if(v==='cp-asc')arr.sort((a,b)=>a.dataset.cp-b.dataset.cp);else if(v==='cp-desc')arr.sort((a,b)=>b.dataset.cp-a.dataset.cp);else if(v==='name')arr.sort((a,b)=>a.dataset.name.localeCompare(b.dataset.name));
  arr.forEach(c=>grid.appendChild(c));count.textContent=n+' of '+cards.length+' hotels';
}}
[q,cat,area,sort].forEach(el=>el.addEventListener('input',apply));apply();
</script>
</body>
</html>"""
(ROOT / "index.html").write_text(page)

print(f"Wrote {len(hotels)} hotels to {OUT}")
if missing:
    print("NO RESEARCH MATCH FOR:", missing)
low = [h["official_name"] for h in hotels if h["research_confidence"] == "low"]
print("Low confidence:", low)
