# Phase 0 acceptance criteria

1. Repository branch is isolated; main unchanged before PR.
2. Source DB schema can be built from scratch using \`python3 scripts/initialize_road_db.py\`.
3. Tests prove foreign-key provenance, geospatial bounds, RTree behavior and empty-data startup.
4. Asset scan actually examines \`assets/\`, \`res/raw/\`, \`res/assets/\`, recursively all Android modules and raw candidate file types; absence is recorded explicitly.
5. ZIP script archives discovered source assets plus schema with individual SHA-256; absence is reported, not lied about.
6. No coordinates, legal limits or externally sourced data are invented.
7. GitHub Actions run succeeds before merge, with run URL recorded in PR.
8. The UI reference specification maps all three screenshots into action/test states, but Phase 0 does **not** claim the UI was implemented.
