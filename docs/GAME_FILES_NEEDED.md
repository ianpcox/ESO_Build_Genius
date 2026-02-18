# What game files we need from you

Your two paths are fixed locally. We use them via config; you don't copy whole folders.

- **Z:\The Elder Scrolls Online** – game installation
- **C:\Users\Ian\OneDrive\Documents\Elder Scrolls Online\live** – live folder (AddOns, SavedVariables)

---

## What we did

1. **Config** – Paths are read from `.env`. Copy `.env.example` to `.env` and set:
   - `ESO_INSTALL_PATH=Z:\The Elder Scrolls Online`
   - `ESO_LIVE_PATH=C:\Users\Ian\OneDrive\Documents\Elder Scrolls Online\live`
   Ingest and other scripts use `config.get_eso_live_path()` / `get_eso_install_path()` so they read directly from those folders. No copying of the full game or live folder is required.

2. **Optional copy script** – If you want a snapshot of addon export files inside the repo (e.g. for ingest that reads from `data/`):
   - Run your addon in-game so it writes to SavedVariables (e.g. Item Set Dumper).
   - Run: `python scripts/refresh_addon_data.py`
   - This copies only **specific addon output files** (e.g. `ItemSetDumper.lua`, `uespLog.lua`, `DataDumper.lua`) from `...\live\SavedVariables\` to `data/addon_export/`. So we don't copy the whole live folder, only the files we need for ingest.

---

## Do you need to run the copy script?

- **No** – If ingest scripts are written to read directly from `ESO_LIVE_PATH` (e.g. `...\live\SavedVariables\ItemSetDumper.lua`), then we never need to copy; we just use the paths from `.env`.
- **Yes (optional)** – If you want ingest to read from `data/addon_export/` (so the repo has a known snapshot and works without the game path), run `refresh_addon_data.py` after each addon export in-game. Then ingest reads from `data/addon_export/`.

---

## Summary

- Set **paths once** in `.env` (from `.env.example`). Those folders don't need to change.
- **No script is required** to copy the whole game or live folder; we read from the paths you set.
- **Optional:** Run `python scripts/refresh_addon_data.py` to copy only addon export files into `data/addon_export/` when you want a local snapshot for ingest.
