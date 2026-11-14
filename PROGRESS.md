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
- [x] Final branch head CI Android compile + unit + lint PASS: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43603204092; Emulator 2/2 PASS: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43603204072.
- [x] PR #5 merged into main as f401f03396431f58ddefd23c2ff87a37c039367f after all three checks passed.
- [ ] Real, licensed Vietnam road-vector PMTiles packages: BLOCKED until verified data extracts (Phase 5); NO geographic coverage claim.


## Phase 4 – Offline Manager (core verified, live source blocked)
- [x] Resumable HTTPS transport with Range/strong ETag/If-Range, persistent partial and cancel cleanup.
- [x] Strict package identity, version, source license, bytes/SHA256 and PMTiles v3 header gate; immutable old-version retention; no OSM bulk tile downloads.
- [x] Wired offline UI status, demo install/reverify/delete, transport pause/resume/cancel and Wi-Fi/cellular policy.
- [x] Python provenance PASS run 43604517491; Kotlin assemble/unit/lint PASS run 43604517429.
- [x] Android Emulator API35 3/3 PASS run 43604517455.
- [x] Code PR #7 merged main as 6fdbcfd.
- [x] WorkManager foreground dataSync download infrastructure verified in PR #9. [ ] Scheduled auto-update blocked: no approved catalog.
- [ ] Approved downloaded 34-province PMTiles/POI/routing packages: BLOCKED, no licensed external catalog.
- [ ] Speed limits and traffic sign coordinates: NO verified real-world source data.


## Phase 4 WorkManager follow-up – PR #9
- [x] WorkManager CoroutineWorker, durable package input and foreground dataSync architecture implemented.
- [x] Offline Manager remote path now uses WorkManager, persists job UUID/spec and reobserves OS work progress on activity restart.
- [x] Network constraints and controlled cancel/pause/resume, SHA256/Pmtiles header before activation; transfer mutex prevents cleanup race in same process.
- [x] Offline UI copy distinguishes fixture from real offline road downloads.
- [x] Unit test WorkManager Data round-trip, source validation, and emulator test invalid worker provenance authored.
- [x] Final branch head Python/SQLite PASS 43606534452, Android assemble/unit/lint PASS 43606534434, Emulator API35 4/4 PASS 43606534445.
- [x] PR #9 merged to main as e1fc7dc423bc96e02c6b44360e5c3a9729c7cfa1.
- [ ] Approved province catalog and real verified speed limit/sign locations: BLOCKED on authentic legally sourced input.


## Phase 4 strict network policy hardening
- [x] Identified UNMETERED vs Wi-Fi policy distinction.
- [x] Persist allow_cellular in worker input and check real active transport via NetworkCapabilities before requesting PMTiles bytes.
- [x] Added unit test for Wi-Fi/Ethernet/Cellular and default opt-out. CI acceptance pending.
- [ ] Merge policy hardening PR after Kotlin/JUnit/Lint and emulator pass.
