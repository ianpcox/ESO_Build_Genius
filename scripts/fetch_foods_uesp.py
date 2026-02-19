"""
Fetch ESO food and beverage recipe names from UESP wiki category members (API).
Writes data/foods.json for use with ingest_food_potions.py.

UESP API: https://en.uesp.net/w/api.php
Categories: Online-Provisioning-Recipes-Food_Recipes, Online-Provisioning-Recipes-Beverage_Recipes

Usage:
  python scripts/fetch_foods_uesp.py
  python scripts/fetch_foods_uesp.py --out data/foods.json
"""
from __future__ import annotations

import argparse
import json
import os
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
DEFAULT_OUT = os.path.join(DATA_DIR, "foods.json")
UESP_API = "https://en.uesp.net/w/api.php"


def strip_online_prefix(title: str) -> str:
    if title.startswith("Online:"):
        return title[7:]
    return title


def fetch_category_members(category_title: str, limit: int = 500) -> list[dict]:
    out: list[dict] = []
    cmcontinue: str | None = None
    while True:
        params: dict = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category_title,
            "cmlimit": min(500, limit),
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        url = UESP_API + "?" + urlencode(params)
        req = Request(url, headers={"User-Agent": "ESO-Build-Genius/1.0"})
        with urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        members = data.get("query", {}).get("categorymembers") or []
        for m in members:
            title = m.get("title", "")
            if title.startswith("Online:") and "Recipe" not in title:
                out.append({"title": title, "name": strip_online_prefix(title)})
        if len(out) >= limit:
            break
        cont = data.get("continue", {})
        cmcontinue = cont.get("cmcontinue")
        if not cmcontinue:
            break
        time.sleep(0.2)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch food and beverage recipe names from UESP wiki.")
    ap.add_argument("--out", default=DEFAULT_OUT, help="Output JSON path")
    ap.add_argument("--limit", type=int, default=600, help="Max total recipes (default 600)")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    food_members = fetch_category_members("Category:Online-Provisioning-Recipes-Food_Recipes", limit=400)
    beverage_members = fetch_category_members("Category:Online-Provisioning-Recipes-Beverage_Recipes", limit=400)

    seen: set[str] = set()
    foods: list[dict] = []
    for i, m in enumerate(food_members + beverage_members, start=1):
        name = m["name"]
        if name in seen:
            continue
        seen.add(name)
        foods.append({
            "food_id": len(foods) + 1,
            "name": name,
            "duration_sec": 7200,
            "effect_text": "",
            "effect_json": None,
        })

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(foods, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(foods)} recipes to {args.out}")


if __name__ == "__main__":
    main()
