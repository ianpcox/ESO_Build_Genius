# ESO Build Genius – Addon mockup

This folder contains a **mockup of an ESO (Elder Scrolls Online) in-game addon** that would offer the same Build Genius experience (build form, equipment slots, Advisor, skill bar with scribing) inside the game client.

## Contents

| Path | Description |
|------|-------------|
| **ESOBuildGenius/** | Skeleton ESO addon (manifest, Lua, XML). Installable in `Documents/Elder Scrolls Online/live/AddOns/ESOBuildGenius/`. |
| **mockup/** | HTML mockup of the addon window. Open `mockup/index.html` in a browser to preview the in-game look. |

## ESO addon skeleton (ESOBuildGenius)

- **ESOBuildGenius.txt** – Addon manifest (Title, APIVersion, AddOnVersion, SavedVariables). Update `APIVersion` to match your game build (e.g. from [esoapi.uesp.net](https://esoapi.uesp.net/index.html)).
- **ESOBuildGenius.lua** – Main logic: creates the window from the XML template, close button, slash command `/buildgenius` to show/hide. No real data yet; full implementation would call the game API (e.g. GetUnitClassId, GetItemLinkSetInfo, skill/scribe APIs) or sync with an external Build Genius backend.
- **ESOBuildGenius.xml** – Window template: title bar, backdrop, content area. Matches ESO’s in-game style (ZO_ThinBackdrop, gold title).

**Install (for testing the skeleton):** Copy the `ESOBuildGenius` folder into your ESO AddOns directory (e.g. `Documents/Elder Scrolls Online/live/AddOns/`). Enable “ESOBuildGenius” in the addon list at character select. In-game, type `/buildgenius` to show or hide the empty window.

## HTML mockup

Open **mockup/index.html** in a browser to see a static preview of the addon window: Build dropdowns, 14 equipment slots, Advisor list, and a snippet of the skill bar with Focus/Signature/Affix. Styling uses ESO-like colors (dark backdrop, gold accents) and a single floating panel to mimic the in-game addon frame.

## Relationship to the rest of the project

- The **web UI** (`web/app.py` + `web/static/`) and **mobile app** (`mobile/`) talk to the same Flask API and database.
- A **real in-game addon** could either (1) use only the game’s Lua API (GetItemLinkSetInfo, abilities, scribing, etc.) and replicate recommendation logic in Lua, or (2) sync with an external Build Genius backend (e.g. export build from game, send to API, display recommendations in the addon). The current addon is a **mockup/skeleton** to show layout and structure; data and logic are not implemented.
- See [docs/UI_DESIGN.md](../docs/UI_DESIGN.md) for the full UI spec and [docs/DATA_SOURCES.md](../docs/DATA_SOURCES.md) for addon-as-data-source notes.
