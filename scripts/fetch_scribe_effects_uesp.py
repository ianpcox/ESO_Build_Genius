"""
Fetch the full scribing script catalog (Focus, Signature, Affix) from UESP wiki.

UESP page: https://en.uesp.net/wiki/Online:Scribing
UESP API: https://en.uesp.net/w/api.php
Parses wikitext tables under "=== Focus Scripts ===", "=== Signature Scripts ===",
"=== Affix Scripts ===" and extracts script display names from [[ON:...|Name]] links.

Writes data/scribe_effects.json for use with ingest_scribe_effects.py.

Usage:
  python scripts/fetch_scribe_effects_uesp.py
  python scripts/fetch_scribe_effects_uesp.py --out data/scribe_effects.json

Data sourcing: see docs/DATA_SOURCES.md (Recommendations: prefer addon/game source for scribing catalog when available; UESP for validation).
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
DEFAULT_OUT = os.path.join(DATA_DIR, "scribe_effects.json")
UESP_API = "https://en.uesp.net/w/api.php"
USER_AGENT = "ESO-Build-Genius/1.0 (https://github.com/)"

# Wikitext: table rows contain '''[[ON:Page|Display Name]]''' - we want Display Name.
SCRIPT_LINK_PATTERN = re.compile(r"'''\[\[ON:[^\]|]+\|([^\]]+)\]\]'''")


def fetch_page_wikitext(title: str = "Online:Scribing") -> str:
    """Get the latest revision wikitext of a UESP page."""
    params = {
        "action": "query",
        "titles": title,
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "format": "json",
    }
    url = UESP_API + "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    pages = data.get("query", {}).get("pages") or {}
    for page in pages.values():
        revs = page.get("revisions") or []
        if revs:
            content = revs[0].get("slots", {}).get("main", {}).get("*") or ""
            return content
    return ""


def extract_scripts_from_section(wikitext: str, section_header: str) -> list[str]:
    """Find a section by header and extract script names from table rows that use {{ESO Script Icon|...}}."""
    start = wikitext.find(section_header)
    if start == -1:
        return []
    rest = wikitext[start:]
    end = rest.find("\n==", 1)
    if end == -1:
        block = rest
    else:
        block = rest[:end]
    names: list[str] = []
    # Only consider lines that are script table rows (contain the icon template), to avoid picking up grimoire/quest links.
    for line in block.split("\n"):
        if "ESO Script Icon" not in line:
            continue
        for m in SCRIPT_LINK_PATTERN.finditer(line):
            name = m.group(1).strip()
            if name and name not in names:
                names.append(name)
    return names


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch scribing script catalog from UESP Online:Scribing")
    ap.add_argument("--out", default=DEFAULT_OUT, help="Output JSON path")
    ap.add_argument("--dry-run", action="store_true", help="Print extracted names only, do not write file")
    args = ap.parse_args()

    print("Fetching Online:Scribing from UESP...")
    wikitext = fetch_page_wikitext()
    if not wikitext:
        print("ERROR: No page content returned")
        raise SystemExit(1)

    focus = extract_scripts_from_section(wikitext, "===Focus Scripts===")
    signature = extract_scripts_from_section(wikitext, "===Signature Scripts===")
    affix = extract_scripts_from_section(wikitext, "===Affix Scripts===")

    print(f"Focus: {len(focus)} scripts")
    print(f"Signature: {len(signature)} scripts")
    print(f"Affix: {len(affix)} scripts")

    catalog = {
        "source": "https://en.uesp.net/wiki/Online:Scribing",
        "focus": [{"name": n} for n in focus],
        "signature": [{"name": n} for n in signature],
        "affix": [{"name": n} for n in affix],
    }

    if args.dry_run:
        for slot, names in [("Focus", focus), ("Signature", signature), ("Affix", affix)]:
            print(f"\n{slot}: {names}")
        return

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
