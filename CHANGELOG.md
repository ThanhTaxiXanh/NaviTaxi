# Changelog

## 0.0.1 — Phase 0 initial architecture (2026-11-14)
- Added provenance-first speed-limit and traffic-sign schema.
- Added source-data discovery and ZIP archival workflow with SHA-256 manifest.
- Added Python schema tests and GitHub Actions workflow.
- Defined Android modules, zero-cost guardrails and three reference UI contracts.

## 0.1.0-dev — Phase 1 working branch
- Added Kotlin Compose application, three reference layouts and persistent local preferences.
- Added voice-search Android intent and sample offline search with accents normalization.
- Added actual device storage readout and a truthful no-data offline status.
- Added verified-vs-unknown speed-limit contract; no synthetic real-world limits or sign locations.

- Debug Android APK built successfully in CI with unit and lint verification: run 43590922509, artifact ID 14111199844.


## 0.2.0-dev — Phase 2 MapLibre/OSM
- MapLibre Native 13.7.1 OpenGL ES integrated into Compose app and linked to Search.
- Street-level OSM raster style explicitly opt-in for manual viewport viewing; no bulk downloads.
- MapLibre demo vector map and honestly empty offline map style; visible provider attribution.
- Optional read-only sourced speed-limit segment and WGS84 sign overlay with tap to see coordinates and source.
- Unit tests added for provider restrictions, geographic bounds, speed provenance and no invented source records.
- Kotlin compiler/Compose plugin updated to 2.2.10; Android emulator integration test introduced.

- Phase 2 emulator MapLibre smoke test passed on API 35 (1/1), run 43593588383; PR #3 merged as 7d9809c. No production map/SLA/traffic intelligence claims.
