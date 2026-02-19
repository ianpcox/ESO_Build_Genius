"""
Fetch ESO potion names from UESP wiki page Online:Potions (MediaWiki API).
Writes data/potions.json for use with ingest_food_potions.py.

Potion tables on the wiki list names like "Sip of Health", "Essence of Magicka", etc.
We extract unique names and assign duration_sec=47.5, cooldown_sec=45 (typical for
crafted potions). The first three entries match the seed: Essence of Weapon Power,
Essence of Spell Power, Essence of Health (with effect_text for build compatibility).

Usage:
  python scripts/fetch_potions_uesp.py
  python scripts/fetch_potions_uesp.py --out data/potions.json
"""
from __future__ import annotations

import argparse
import json
import re
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
DEFAULT_OUT = os.path.join(DATA_DIR, "potions.json")
UESP_API = "https://en.uesp.net/w/api.php"
POTIONS_PAGE = "Online:Potions"

# Match seed so potion_id 1,2,3 stay meaningful for recommended_builds
SEED_POTIONS = [
    {"potion_id": 1, "name": "Essence of Weapon Power", "duration_sec": 47.5, "cooldown_sec": 45,
     "effect_text": "Restore Health, Magicka, Stamina; Major Brutality, Major Sorcery, Major Savagery", "effect_json": None},
    {"potion_id": 2, "name": "Essence of Spell Power", "duration_sec": 47.5, "cooldown_sec": 45,
     "effect_text": "Restore Health, Magicka, Stamina; Major Prophecy, Major Sorcery, Major Savagery", "effect_json": None},
    {"potion_id": 3, "name": "Essence of Health", "duration_sec": 47.5, "cooldown_sec": 45,
     "effect_text": "Restore Health, Magicka, Stamina", "effect_json": None},
]


def fetch_page_wikitext(title: str) -> str:
    params = {
        "action": "query",
        "titles": title,
        "prop": "revisions",
        "rvprop": "content",
        "format": "json",
    }
    url = UESP_API + "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "ESO-Build-Genius/1.0"})
    with urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    pages = data.get("query", {}).get("pages") or {}
    for page in pages.values():
        revs = page.get("revisions") or []
        if revs and "*" in revs[0]:
            return revs[0]["*"]
    return ""


def extract_potion_names(wikitext: str) -> set[str]:
    names: set[str] = set()
    # Table rows: ||rowspan=N|Potion Name or ||rowspan=N|{{icon|...}}||rowspan=N|Potion Name
    for m in re.finditer(r"\|\|rowspan=\d+\|([A-Za-z][^|{}\n]+?)(?=\n|\|\|)", wikitext):
        name = m.group(1).strip()
        if "{{" not in name and "}}" not in name and len(name) > 2:
            names.add(name)
    # Item Link: {{Item Link|Potion Name|quality=|id=...}}
    for m in re.finditer(r"\{\{Item Link\|([^|]+)\|", wikitext):
        name = m.group(1).strip()
        if len(name) > 2:
            names.add(name)
    return names


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch potion names from UESP wiki Online:Potions")
    ap.add_argument("--out", default=DEFAULT_OUT, help="Output JSON path")
    args = ap.parse_args()

    out_path = os.path.join(ROOT_DIR, args.out) if not os.path.isabs(args.out) else args.out
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    print("Fetching Online:Potions from UESP ...")
    wikitext = fetch_page_wikitext(POTIONS_PAGE)
    if not wikitext:
        print("Failed to fetch page content.", file=__import__("sys").stderr)
        raise SystemExit(1)

    names = extract_potion_names(wikitext)
    # Seed names we want first (already in SEED_POTIONS)
    seed_names = {p["name"] for p in SEED_POTIONS}
    others = sorted(names - seed_names)
    # Build list: seed three first, then rest with potion_id 4, 5, ...
    potions = list(SEED_POTIONS)
    for i, name in enumerate(others, start=len(SEED_POTIONS) + 1):
        potions.append({
            "potion_id": i,
            "name": name,
            "duration_sec": 47.5,
            "cooldown_sec": 45,
            "effect_text": "",
            "effect_json": None,
        })

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(potions, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(potions)} potions to {out_path}")


if __name__ == "__main__":
    main()
