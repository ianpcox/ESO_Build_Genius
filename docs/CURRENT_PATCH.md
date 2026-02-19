# Current patch – ESO Build Genius

**Target patch:** **Patch 48** (Update 48 – Seasons of the Worm Cult Part 2 and later incrementals).

All data ingest, build labels, and documentation in this project should align with Patch 48 unless otherwise noted. When Zenimax releases a new patch, update this file and re-run ingest with the new build label.

## Build label

- For **current live data** (Patch 48), use build label **`Update 48`** when running ingest scripts:
  - `ingest_sets_uesp.py --build-label "Update 48" [--replace]`
  - `ingest_skills_uesp.py --build-label "Update 48" [--replace]`
  - `populate_buff_grants_set_bonus.py --build-label "Update 48" [--replace]`
  - `ingest_xlsx.py --build-label "Update 48"` (if using xlsx for skills or Calculator)
- The schema seed creates a `Default` game build for backward compatibility; create an **Update 48** build by running any ingest with `--build-label "Update 48"`, or ensure `game_builds` has a row with `label = 'Update 48'` after `create_db`.

## Incrementals

Patch 48 has had incrementals (e.g. v11.2.7 Update 48 Incremental 2). For display you can use `game_builds.label` such as `Update 48 Incremental 2`; for ingest, UESP ESO Log (setSummary, skillCoef) typically reflects the latest live data, so **Update 48** is sufficient unless you need to distinguish incrementals.

## Skill counts (Patch 48)

We ingest **skillCoef** only (~7k abilities with valid damage/heal coefficients), **not** minedSkills (126k+). UESP [viewSkillCoef](https://esoitem.uesp.net/viewSkillCoef.php) reports “7083 skills with valid coefficients”; that is the same dataset. Scripts that use a large pagination cap (e.g. 999999) use it to mean “fetch all” – the actual skillCoef table is on the order of 7k rows. Verify your DB with `python scripts/check_skills_patch48.py`.

## Data files

- **xlsx files in data/:** The current files are **not** confirmed Update 48. **Damage Skills (Update 38_39_40).xlsx** contains sheet headers stating "Update 39" / "Update 39/40 (U41 Linked Below)". **Standalone Damage Modifiers Calculator** and **Harpooner's Wading Kilt Cheat Sheet** have no version in the filename. See **[data/XLSX_VERSION_NOTES.md](data/XLSX_VERSION_NOTES.md)** for details and how to re-source for Patch 48.
- **UESP ESO Log** (esolog.uesp.net) setSummary and skillCoef are maintained by the community and should reflect current live (Update 48) after each patch.

## References

- [Official patch notes (Update 48)](https://forums.elderscrollsonline.com/en/categories/patch-notes)
- [PATCH_SOURCES.md](PATCH_SOURCES.md) – per-patch resource pattern and ESOUI/API links.
