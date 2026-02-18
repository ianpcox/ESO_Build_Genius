"""
Copy addon export files from ESO live SavedVariables to data/addon_export/.
Run this after using an addon in-game that dumps sets/skills (e.g. Item Set Dumper).
Uses ESO_LIVE_PATH from .env (see .env.example).
"""
import shutil
import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "addon_export"

# Addon SavedVariables we care about (filename without path)
ADDON_FILES = [
    "ItemSetDumper.lua",
    "uespLog.lua",
    "DataDumper.lua",
]

def main():
    try:
        from config import get_eso_live_path
    except ImportError:
        sys.path.insert(0, str(ROOT))
        from config import get_eso_live_path

    live = get_eso_live_path()
    if not live:
        print("ESO_LIVE_PATH is not set or path does not exist.")
        print("Copy .env.example to .env and set ESO_LIVE_PATH to your ESO live folder.")
        sys.exit(1)

    saved = live / "SavedVariables"
    if not saved.is_dir():
        print(f"SavedVariables folder not found: {saved}")
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0
    for name in ADDON_FILES:
        src = saved / name
        if src.is_file():
            shutil.copy2(src, OUT_DIR / name)
            print(f"Copied {name}")
            copied += 1

    if copied == 0:
        print("No addon export files found. Install and run an addon that writes to SavedVariables")
        print(f"(e.g. Item Set Dumper), then run this script again. Looked in: {saved}")
        print(f"Looked for: {ADDON_FILES}")
    else:
        print(f"Done. {copied} file(s) in {OUT_DIR}")


if __name__ == "__main__":
    main()
