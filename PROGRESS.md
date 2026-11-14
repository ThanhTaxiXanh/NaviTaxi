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
- [x] Phase 4 policy PR #11 merged to main 64ec5e6: Python/SQLite PASS 43607450905, Android build/JUnit/Lint PASS 43607450906, emulator 4/4 PASS 43607450907.


## Phase 4 catalog and source-provenance gating — PR #13
- [x] Authored pinned SHA-256 catalog approval contract, strict release/URL/license/size metadata gates in Python and Android.
- [x] Added monotonic integer release sequence (rollback/equivocation rejection) instead of comparing version strings.
- [x] Changed OfflinePackageManager remote entrypoint to require a validated TrustedOfflineCatalog, without enabling any live map source.
- [x] Added Python catalog negative tests (no pin, duplicate/extra fields, unsafe URLs, fake speed/sign verification, rollback); CI 43610420031 PASS.
- [ ] Android compile, unit, lint and API35 new instrumentation verification on final PR head.
- [ ] Production approved catalog, original Vietnam PBF approval/processing, actual verified road speed/sign coordinates: BLOCKED on legitimate source and field evidence.


## Phase 4 trusted catalog and APK scan — verified closure (2026-11-14)
- [x] PR #13 merged main 068c297e1df55466ba0adc50b05755192814087b after FINAL HEAD checks.
- [x] Python/SQLite/source audit: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43611161271 PASS.
- [x] Android assembleDebug/testDebugUnitTest/lintDebug plus APK JSON/SQLite/PMTiles deep scan and ZIP archive: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43611161247 PASS.
- [x] Android emulator API35 including catalog negative tests: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43611161298 PASS.
- [x] Actual APK audit artifact 14119833707 inspected: exact five synthetic assets, 0 verified speed/sign records, checksum manifest matches archived files.
- [ ] Real signed-off PMTiles catalog, release-sequence persistence for real installs, 34-province geodata, source-backed speed/sign DB and vehicle-road tests: still BLOCKED/NOT DONE.


## Phase 4 Road Intelligence integrity continuation (PR #15)
- [x] Identified fail-open provenance weakness: arbitrary SQLite rows joined to nonempty source/license strings could appear as "verified".
- [x] Authored separately pinned DB SHA and domain-specific speed/sign approval gate, rejecting unhashed SQLite journal sidecars.
- [x] Reader now suppresses unapproved road/sign overlays and requires observation plus verification dates on eligible rows.
- [x] Authored offline candidate SQLite integrity/coordinate/RTree report without generating approvals.
- [x] Added synthetic-only regression tests (Kotlin unit, API35 instrumentation, Python) and GitHub artifact collection.
- [x] PR #15 acceptance on final-head Python/SQLite, Android build/lint/JUnit and API35 emulator verified; details in closure section below.
- [ ] Verified real speed_kmh/physical sign coordinates: BLOCKED (no approved legal/field evidence).


## Phase 4 road candidate source and gate — ACCEPTED CI (PR #15)
- [x] PR #15 merged main `dd53c1a43991f350ffa980091e4db1faabeddccf`.
- [x] Python/SQLite candidate audit, field metadata and RTree negative cases PASS: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43614134722.
- [x] Kotlin Android JUnit, lint and assembleDebug PASS: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43614134733.
- [x] Android API35 emulator new untrusted-source rejection test and existing map/offline tests PASS: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43614134877.
- [x] Test artifact 14121745051 inspected: SQLite 86,016 B, 0 row sources/roads/signs, both alert flags FALSE. APK audit only five synthetic assets.
- [ ] Field-verified source road speeds, physical sign lat/lon, real-map downloadable PMTiles/POI/routing and on-road reliability are BLOCKED; Phase 4 not fully accepted.


## Phase 4 reference-only OSM road/tag staging (PR #17)
- [x] Implemented local .osm/.osm.pbf streaming with mandatory full SHA-256, original IDs/tags and an ODbL provenance manifest.
- [x] Preserved raw mph/conditional/advisory values, with no assumed legal speed_kmh; traffic_sign ways/relations never acquire invented physical coordinates.
- [x] Added reference-only JSONL and ZIP with SHA256SUMS, non-overwrite behavior and failure cleanup; rejected output to production Android/road DB assets.
- [x] Python/SQLite CI 43617224402: 36/36 PASS, including actual binary PBF fixture read; Android build/unit/lint 43617224403 PASS on code head.
- [x] APK audit on code head confirms 5 test-only map assets, no real Road Intelligence database.
- [ ] PR #17 final-head CI and merge; do not declare entire Phase 4 finished.
- [ ] Real Vietnam OSM snapshot acquired/licensed/hashed and independently verified speed/sign data: BLOCKED/NOT INGESTED.
