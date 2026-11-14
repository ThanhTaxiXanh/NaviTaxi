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


## 0.3.0-dev — Phase 3 PMTiles v3
- Added one deterministic, synthetic MVT tile in a valid PMTiles v3 archive, not real roads/signs.
- Added streaming SHA-256 package verification, strict PMTiles header guards and atomic copy to private app storage.
- Added Android-native MapLibre file-backed PMTiles source mode, visibly marked as synthetic and offline.
- Added PMTiles fixture regeneration, binary validator and local HTTP Range probe with tests.
- Added instrumentation smoke for opening PMTiles style without using OSM tile infrastructure.

- Phase 3 final PR #5 merged, main f401f03; Python/SQLite PASS run 43603204053, Android build/unit/lint PASS 43603204092, emulator 2/2 PASS 43603204072.


## 0.4.0-dev – Phase 4 core
- Added OfflinePackageTransfer for HTTPS byte-range resume, strong ETag/If-Range, full SHA256/v3 validation and atomic per-version install. Pause/resume/cancel and explicit delete semantics.
- Added OfflinePackageManager StateFlow transport coordination and network policy.
- Offline page now supports install/reverify/delete real embedded synthetic test fixture, accurate installed status and clear absence of production region catalog.
- Added MockWebServer range/corruption/update/URL unit tests, Android emulator smoke test. Code PR #7 merged as 6fdbcfd.
- Background WorkManager and real province datasets not shipped.


## 0.4.1-dev – WorkManager recovery
- Added WorkManager 2.12.0 durable approved download worker and foreground dataSync notification.
- Replaced app-only remote coroutine execution with OS-managed constrained requests and work status Flow; saved UUID for process re-creation.
- Serialized in-process cancellation/partial cleanup; reject URL query secrets in persisted specs and check free storage.
- Added WorkManager contract unit tests and invalid-provenance Android instrumentation test.
- No source speed limit or physical traffic sign coordinates; still no real province catalog.

- WorkManager phase4 follow-up completed with 3 successful final workflows (43606534452, 43606534434, 43606534445), merged as main e1fc7dc. Background field reliability and real licensed map catalogs remain unvalidated/blocked.
