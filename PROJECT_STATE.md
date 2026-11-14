# Project state — 2026-11-14

- Repository: `ThanhTaxiXanh/NaviTaxi`
- Starting main SHA: `40f6c89b7e1027c3f64c552bfc0d2271dffc79d2` (originally README only)
- Phase: **0** (architecture and trustworthy road-data foundation)
- Build environment observed: OpenJDK 21, Kotlin CLI present; Android SDK/Gradle/AAPT2/Apksigner not detected in current runtime. GitHub Actions is the intended Android build environment.
- Data discovery: no APK, `assets/`, `res/raw`, `res/assets` or real source DBs existed in the initial GitHub repo. None can be claimed extracted.
- Three UI references examined: search, offline maps, settings. Implementation follows Phase 1; screenshot-perfect acceptance requires emulator/device comparison.
- Speed-limit/sign schema: `data/road_intelligence/schema.sql`; no authentic records imported.
- Exact prospective on-device asset: `app/src/main/assets/road_intelligence/road_intelligence.db` (NOT yet generated in repo).
- Local archive workflow: `scripts/audit_road_assets.py`, `scripts/package_road_data.py`.

## Work session closure rule
Read this file and [PROGRESS.md](PROGRESS.md) on every new session. Never mark Android app, PMTiles, road data coverage, or screenshots complete without real evidence.

## Verified Phase 0 CI

- Push CI passed: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43589361023.
- Tests: Python compilation, unittest SQLite schema/provenance/RTree, APK entry path audit and ZIP checksums; artifact created.
- PR: https://github.com/ThanhTaxiXanh/NaviTaxi/pull/1.

## Phase 1 current work

- Isolated working branch: `phase-1/android-ui-reference-screens`, PR #2: https://github.com/ThanhTaxiXanh/NaviTaxi/pull/2.
- Core Kotlin/Compose app and reference search/offline/settings pages added; Android CI is the build verification source.
- In-app maps/downloads/traffic overlays/speed-limit alarms have not been claimed functional without validated datasets and engines.
- Phase 0 merged on main as squash commit `5aabd8c79d444bbf261bcc5d78a2325a62565ceb` after GitHub Actions success.
