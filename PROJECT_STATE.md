# Project state — 2026-11-14

- Repository: `ThanhTaxiXanh/NaviTaxi`
- Starting main SHA: `40f6c89b7e1027c3f64c552bfc0d2271dffc79d2` (originally README only)
- Current phase: **4 — CORE VERIFIED / INTEGRATION BLOCKED**. Phase 0/1/2/3 and Phase 4 core code are merged.
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

## Phase 1 verified evidence

- Android CI passed at `691ddd94312e86b187b1680809b23f26fab2577e`: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43590922509.
- APK artifact ID `14111199844`, 16,416,125 bytes, SHA-256 `1b1824ecd27f4a7364ef38f7fbc85f6e8f803743144928f6c083be06947c7171`.
- Scope complete: Android Core skeleton, persistent settings, three reference-inspired navigation UI layouts and verifiable unknown/verified road-sign data models.
- Scope explicitly incomplete: pixel-perfect screenshot QA, map rendering, PMTiles/offline downloads, GPS, traffic sign datasets and speed warnings; follow corresponding phases.
- PR #2 merged into main as 501b46b611b7c1c73adf1eb4e03343fa4653b2e4. Phase 1 Android build passed, but pixel-perfect device screenshot QA remains Phase 15.


## Phase 2: branch and acceptance
- Branch: phase-2/maplibre-osm-road-data; PR #3 https://github.com/ThanhTaxiXanh/NaviTaxi/pull/3.
- MapLibre Native 13.7.1 OpenGL ES; Kotlin/Compose compiler plugin upgraded to 2.2.10.
- Default vector source: MapLibre World DEMO; manual opt-in OSM raster street viewport only (not production or offline tile host). Honest empty local map style.
- User-facing map search navigation, map zoom/gesture UI, labels of unknown speed/sign data.
- Optional private verified dataset location: <app-files>/road_intelligence/road_intelligence.db, currently NOT PRESENT. Source validation + physical coordinates are required; no fabricated records are included.
- Exact APK assets: app/src/main/assets/map_styles/offline_empty.json (238 bytes); app/src/main/assets/map_styles/osm_streets_experimental.json (416 bytes).
- Repo full tree scan: NO *.db, *.sqlite, *.realm, *.geojson, *.csv, *.pbf or *.pmtiles assets present.
- Python/SQLite provenance CI: PASS; Kotlin compile+unit+lint: PASS for phase 2 commit 518785a5, run https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43593357604.
- Android Emulator MapLibre startup/local style/exit smoke test PASSED: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43593588383 (1/1 instrumented test, API 35). Tile coverage and navigation NOT proven.
- Phase 2 PR #3 merged to main as 7d9809cd95e582d911697db96b9fe9215e9c16ee after CI success. Next: Phase 3 PMTiles local reading, legitimate data packages, checksum and Android device tests.


## Phase 3 – PMTiles v3 native offline reader (2026-11-14)
- Working branch: phase-3/pmtiles-native-offline; PR #5 https://github.com/ThanhTaxiXanh/NaviTaxi/pull/5.
- MapLibre Native 13.7.1 supports pmtiles://file:// and pmtiles://https://. Android PMTiles asset:// byte-range is NOT supported by the current SDK; copy a checksum-verified test archive from APK assets to private filesDir/offline_packages/synthetic_test.pmtiles.
- Synthetic test asset path inside APK: assets/pmtiles/synthetic_test.pmtiles (462 bytes; SHA-256 d9a53b380463498cc31fd59a30d00e07a2f3f32f9f894eefa7b796d20470de9c). Manifest: assets/pmtiles/synthetic_manifest.json. Offline style: assets/map_styles/pmtiles_synthetic.json.
- Source fixture generated by scripts/build_synthetic_pmtiles.py; validated by scripts/validate_pmtiles.py and tests/test_pmtiles_fixture.py. 1 MVT vector tile, 2 synthetic schematic cross lines (NOT REAL ROADS). No legal speed data, physical signs, GPS or POI packaged.
- Binary PMTiles v3 has 127-byte fixed header, one gzip root directory entry, gzip JSON metadata, gzip vector tile. Metadata vector layer demo_grid.
- Android store: app/src/main/java/vn/navitaxi/OfflinePmtilesStore.kt (SHA-256, structural validation, atomic private-copy activation).
- Map screen: user-selected PMTiles demo with clear synthetic data notice; other OSM/MapLibre sources unchanged.
- HTTP Range verification: scripts/pmtiles_range_probe.py and loopback test tests/test_pmtiles_range_probe.py. This does NOT create a real public tile service.
- Emulator MapLibre PMTiles smoke passed 2/2 on final Phase 3 head: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43603204072.
- Phase 3 final code PR #5 MERGED into main as f401f03396431f58ddefd23c2ff87a37c039367f. All three final-head workflows passed. Next: Phase 4 download/pause/resume/cancel/update with verified data. Do not call 34-province coverage complete.


## Phase 4 – verified resumable package manager core (2026-11-14)
- Code PR #7 https://github.com/ThanhTaxiXanh/NaviTaxi/pull/7 merged as 6fdbcfd3f6cace9220a93aec62c1b76130492d61.
- New Kotlin: app/src/main/java/vn/navitaxi/OfflinePackageTransfer.kt, OfflinePackageManager.kt.
- Updated app/src/main/java/vn/navitaxi/OfflineScreen.kt and app/build.gradle.kts.
- New tests app/src/test/java/vn/navitaxi/OfflinePackageTransferTest.kt and app/src/androidTest/java/vn/navitaxi/OfflineManagerSmokeTest.kt.
- Download transport: approved HTTPS package spec with immutable id/version, expected size and SHA-256, legal provenance; HTTP Range + strong ETag/If-Range; pause retains partial, resume validates byte range, cancel discards partial, corrupt file never activated, new version retains prior file.
- Wi-Fi/mobile transport gate; public OSM tile and MapLibre demo hosts prohibited for bulk downloads.
- App UI can install, reverify and delete ONLY the existing synthetic PMTiles fixture. No verified 34-province catalog, true road/speed/sign datasets or production offline navigation.
- Python/SQLite provenance PASS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43604517491.
- Android assemble/unit/lint PASS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43604517429.
- Android API 35 emulator 3/3 PASS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43604517455.
- APK debug 59,718,112 bytes SHA256 7d1f6728914d474b3d97a5d61fae5ab15a10c1f01dce96e4853ac6853d95848a.
- Remaining Phase 4: long-term device/OEM background reliability validation and a licensed, signed-off remote catalog/version discovery/update scheduling. WorkManager infrastructure now built and emulator tested; no live approved source.


## Phase 4 WorkManager continuation, 2026-11-14
- Branch: phase-4/workmanager-durable-downloads; PR #9 https://github.com/ThanhTaxiXanh/NaviTaxi/pull/9.
- AndroidX WorkManager 2.12.0 durable approved PMTiles transfers; source files app/src/main/java/vn/navitaxi/OfflineDownloadWorker.kt and OfflineWorkScheduler.kt.
- App now reobserves work ID/progress after process recreation using WorkManager Flow. Long-running downloads declare foreground dataSync service; Wi-Fi-only is WorkManager UNMETERED, mobile requires explicit opt-in.
- WorkManager Data stores only approved non-secret source/version/license/size/SHA256; no GPS coordinates. Reuses Phase 4 streaming ETag/Range and PMTiles v3 integrity gate. Query-string credentials prohibited.
- Synthetic APK asset only: assets/pmtiles/synthetic_test.pmtiles, 462 bytes. No real speed-limit/sign-location records, no legally sourced 34-province catalog; automated release checks blocked.
- WorkManager code verified on final PR head (Python/SQLite 43606534452, Android build/unit/lint 43606534434, Android Emulator API35 4/4 43606534445). PR #9 merged into main as e1fc7dc423bc96e02c6b44360e5c3a9729c7cfa1. Full Phase 4 remains blocked on real catalog/field proof.

- Real APK audit on Phase 4 WorkManager branch: 60,285,140 bytes, SHA256 2f3492851a2596b20c64e2dea0910e8c4428bd863d143b8aac12bc132b2cd5ca. APK contains exactly five assets (4 JSON + 462-byte synthetic PMTiles) and no .db/.sqlite/.realm records or physical traffic sign dataset.
