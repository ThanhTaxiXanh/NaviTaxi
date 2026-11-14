# Progress

## Phase 0 — architecture and asset/data provenance
- [x] Master Prompt read, three visual refs examined and empty GitHub repository inspected.
- [x] Road intelligence schema, data-source contract, scanning/archiving tooling and Python tests authored.
- [x] GitHub Actions Python compile, SQLite, provenance, archive tests and artifact upload all succeeded: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43589361023.
- [x] Phase 0 PR #1 merged into main (verified): https://github.com/ThanhTaxiXanh/NaviTaxi/pull/1.

## Phase 1 — Core Android
- [x] Create Kotlin project and Android CI.
- [x] Implement baseline interactive Search / Offline Maps / Settings screens.
- [x] Build debug APK in CI. Device screenshot/pixel verification deferred; see Phase 15.

## Phase 1 implementation (work in progress)
- [x] Kotlin Android project, Gradle and Android Actions build workflow authored.
- [x] Three Compose pages and NaviTaxi brand created, with search and persisted local settings.
- [x] Explicit unknown/verified speed-limit data contract created.
- [x] Android :app:assembleDebug, :app:testDebugUnitTest and :app:lintDebug passed with verified APK artifact: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43590922509.
- [ ] Device screenshots compared against three user references (Phase 15 pixel QA; NOT claimed exact).
- [x] Phase 1 PR #2 merged to main as 501b46b.


## Phase 2 — MapLibre + OSM (ongoing)
- [x] Native MapLibre OpenGL ES dependency; Kotlin 2.2.10 compiler alignment.
- [x] Map tab, search-to-map action, camera zoom/gestures and lifecycle callbacks in Compose.
- [x] Default limited vector demo; explicit OSM street test consent with app User-Agent and visible attribution; empty offline source.
- [x] Source-linked road/speed limit and physical traffic sign GeoJSON visual layers gated on optional local SQLite.
- [x] WGS84 bounds/speed provenance validation and marker-tap coordinates/source text.
- [x] Phase 0 schema/asset Python checks green, Kotlin app build/lint/unit tests succeeded at 518785a5, CI 43593357604.
- [x] Emulator API 35 MapLibre startup, empty style switch, exit no-crash test PASS: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43593588383.
- [x] PR #3 merged into main as 7d9809c after 3 green CI workflows.


## Phase 3 — PMTiles and synthetic offline test
- [x] Deterministic PMTiles v3/MVT synthetic fixture and SHA-256 JSON manifest authored, no real road/sign data invented.
- [x] MapLibre Native pmtiles://file:// source with verified copy from APK assets to app-private filesDir; guard bad headers and checksums.
- [x] MapLibre screen demonstrates offline fixture, with explicit "synthetic" and unknown speed/sign notices.
- [x] HTTP Range probe and loopback mock test authored (no third-party tile-server bulk requests).
- [x] Android emulator opened PMTiles demo in early Phase 3 smoke test (2/2) https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43602555868.
- [x] Python/SQLite/provenance/PMTiles tests PASS after gzip determinism fix https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43602874345.
- [ ] Verify latest Android compile + unit + lint on current head and final emulator smoke run.
- [ ] Merge Phase 3 PR #5 to main only after all CI gates pass.
- [ ] Real, licensed Vietnam road-vector PMTiles packages: BLOCKED until verified data extracts (Phase 5); NO geographic coverage claim.
