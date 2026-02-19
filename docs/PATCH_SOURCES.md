# Per-patch documentation (Zenimax / ESOUI)

**Current live patch:** **Patch 48** (Update 48). Use build label **`Update 48`** for ingest. See [CURRENT_PATCH.md](CURRENT_PATCH.md).

For each patch, Zenimax and the addon community publish a consistent set of documents. Use these to create or label `game_builds` rows and to trigger re-ingest when a new patch goes live.

## Per-patch resource pattern

For every update you typically have:

| Resource | Description | Example (11.2.0) |
|----------|-------------|------------------|
| **Update name** | Official patch title | ESO 11.2.0 "Season of the Wormcult Part 2" |
| **Dates** | PTS first hit; live date | September 15th, 2025 (PTS); October 27th, 2025 (live) |
| **Features and fixes** | High-level summary | [elderscrollsonline.com news](https://www.elderscrollsonline.com/en-us/news/post/68671) |
| **Patch notes** | Full patch notes (forums) | [PTS Patch Notes v11.2.0](https://forums.elderscrollsonline.com/en/discussion/683115/pts-patch-notes-v11-2-0) |
| **API patch notes** | Addon API changes (attachment) | [ESOUI attachment](https://www.esoui.com/forums/attachment.php?attachmentid=1892&d=1757966271) |
| **API TXT documentation** | Full API text dump (attachment) | [ESOUI attachment](https://www.esoui.com/forums/attachment.php?attachmentid=1891&d=1757966271) |
| **ESOUI topic** | Forum thread for the patch | [ESOUI showthread](https://www.esoui.com/forums/showthread.php?t=11431) |

## URLs (templates)

- **Features:** `https://www.elderscrollsonline.com/en-us/news/post/{id}`
- **Patch notes (official):** `https://forums.elderscrollsonline.com/en/categories/patch-notes` then select thread (e.g. `.../discussion/683115/pts-patch-notes-v11-2-0`)
- **API patch notes / API TXT:** ESOUI attachment URLs (e.g. `https://www.esoui.com/forums/attachment.php?attachmentid={id}&d={timestamp}`)
- **ESOUI patch topic:** `https://www.esoui.com/forums/showthread.php?t={thread_id}`

## ESOUI attachments (login)

Some ESOUI attachments (e.g. API patch notes, API TXT documentation) may require you to be logged in. **Do not store ESOUI credentials in this repository.**

- Use **environment variables** (e.g. `ESOUI_USERNAME`, `ESOUI_PASSWORD`) for any script that downloads attachments, or
- Use a **local config file** that is listed in `.gitignore` (e.g. `config/local.env` or `secrets/esoui.txt`) and never committed.

Scripts that fetch ESOUI attachments should read credentials from the environment or from that local file and must not hardcode or log passwords.

## Using this for ESO Build Genius

Per [DATA_SOURCES.md](DATA_SOURCES.md) Recommendations: use **Zenimax API TXT** and **patch notes** to set and validate `game_builds.label` and `api_version`.

1. **Create a `game_builds` row** when a new patch is announced or goes live: set `label` (e.g. `Update 48` or `Update 11.2.0 "Season of the Wormcult Part 2"`) and optionally `api_version` when you have it (e.g. from the API TXT or UESP).
2. **Patch notes** – use for “what changed” and to label builds; link from your app or docs if desired.
3. **API patch notes / API TXT** – use to detect API version and function/skill changes; can drive or validate ingest (e.g. skill names, IDs).
4. **Re-ingest** – after live date, run your set/skill ingest for the new `game_build_id` (e.g. `ingest_sets_uesp.py --build-label "Update 48"`).

You can maintain a small table or JSON file (e.g. `data/patch_registry.json`) that maps patch name → dates, forum links, and attachment IDs so scripts can fetch the right URLs per patch.
