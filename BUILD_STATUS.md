# Build and tests

- Android APK: DEBUG APK BUILT in Phase 1 and Phase 2. Production release APK: NOT BUILT.
- Java: OpenJDK 21 detected.
- Kotlin CLI: present (local).
- Android SDK/Gradle/AAPT2/Apksigner: not detected locally.
- Python database unit tests: PASSED in GitHub Actions run 43589361023 (SQLite, source/coordinate validation, RTree triggers, embedded asset scan, archive checks).
- Evidence artifact: phase0-road-data-evidence, GitHub artifact ID 14110994349, SHA-256 faf217ca2ce3348854cbab950951039ad6e3b5f64465ad08b2a1f00960dd1abb.
- GitHub Actions workflow: `.github/workflows/phase0-road-data.yml`, https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43589361023.
- Android device UI/screenshot tests: NOT STARTED.

Acceptance policy: source creation != test pass; record GitHub Actions run, job result, artifact checksum and device model once available.

## Phase 1
- Android CI workflow: `.github/workflows/android-build.yml`.
- First attempt failed SDK installation (not a Kotlin compiler result); workflow fixed in follow-up commit.
- Original Phase 1 failures were fixed; verified compilation is documented below.

### Verified CI on Phase 1 head `691ddd94312e86b187b1680809b23f26fab2577e`
- **SUCCESS** GitHub Actions: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43590922509
- Tasks verified: `:app:assembleDebug`, `:app:testDebugUnitTest`, `:app:lintDebug`.
- Artifact: `NaviTaxi-debug-apk` ID `14111199844`.
- APK: `app-debug.apk`, 16,416,125 bytes; SHA-256 `1b1824ecd27f4a7364ef38f7fbc85f6e8f803743144928f6c083be06947c7171`.
- Android manifest and 4 DEX files inspected in downloaded artifact.
- Device launch/screenshot/install validation: **NOT TESTED**; defer to instrumented/device acceptance.
- Note: successful debug compilation is NOT a signed production `NaviTaxi.apk` release.


## Phase 2
- Android compile, unit tests and lint PASS: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43593357604 (commit 518785a5).
- Source/SQLite/ZIP tests PASS at same head through Phase 0 Road Data Integrity workflow.
- Debug APK contains native MapLibre libraries for arm64-v8a, armeabi-v7a, x86 and x86_64; no road/sign geodata asset.
- Runtime MapLibre emulator test PASSED (Android API 35; 1/1): https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43593588383.
- Google Play release and actual phone install: NOT TESTED.

- Latest accepted code head before squash: 87d50aeee5f2052b7b7b773be427797e542525dc; three required CI workflows passed.
- PR #3 merged on main as 7d9809cd95e582d911697db96b9fe9215e9c16ee.


## Phase 3 — PMTiles
- Synthetic PMTiles v3 fixture exactly 462 bytes, SHA-256 d9a53b380463498cc31fd59a30d00e07a2f3f32f9f894eefa7b796d20470de9c.
- Python PMTiles generation reproducibility, gzip header consistency, checksum tamper rejection and local HTTP Range test: PASS in current branch latest CI run 43602874345.
- Android API 35 Emulator initial PMTiles validation + MapLibre style rendering smoke: PASS (2/2) https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43602555868.
- Final head Android build, unit tests and lint PASSED: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43603204092. Final emulator 2/2 PASSED: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43603204072.
- No production APK, no 34-province PMTiles, no verified speed/sign data.

- Phase 3 code PR #5 merged: https://github.com/ThanhTaxiXanh/NaviTaxi/pull/5; main f401f03396431f58ddefd23c2ff87a37c039367f.
- Verified debug APK artifact ID 14116868765, app-debug.apk 59,685,344 bytes; SHA-256 d7da7d1a0dd982f2a956df6289dda22a0a872806a12292fe36724083cadbc727. APK asset PMTiles SHA-256 d9a53b380463498cc31fd59a30d00e07a2f3f32f9f894eefa7b796d20470de9c.


## Phase 4 – validated core
- Python/SQLite/PMTiles: SUCCESS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43604517491.
- Android assembleDebug + testDebugUnitTest (MockWebServer) + lintDebug: SUCCESS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43604517429.
- Android Emulator API35: 3/3 tests passed https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43604517455.
- GitHub artifact 14117896754: app-debug.apk size 59,718,112 bytes; SHA-256 7d1f6728914d474b3d97a5d61fae5ab15a10c1f01dce96e4853ac6853d95848a.
- PR #7 merged into main as 6fdbcfd3f6cace9220a93aec62c1b76130492d61.
- Production APK, real 34-province maps, speed/sign surveys, phone background/force-stop driving validation and automatic release checks remain NOT DONE. WorkManager queued-worker infrastructure now verified in PR #9.


## Phase 4 background WorkManager – PR #9
- WorkManager version 2.12.0 released 2026-09-23, minSdk24 and compatible with project minSdk26.
- Initial Python/SQLite pass 43606081873; initial Android build fail 43606081949 (corrected labelled return).
- Final head Android compile/JUnit/lint PASS 43606534434; Python/SQLite PASS 43606534452; Android Emulator 4/4 PASS 43606534445. PR #9 merged as e1fc7dc.
- Source test APK PMTiles synthetic only; no source-backed road speed/sign location databases.

- Actual debug APK 60,285,140 bytes; SHA256 2f3492851a2596b20c64e2dea0910e8c4428bd863d143b8aac12bc132b2cd5ca. GitHub Actions artifact ID 14118780517 on run 43606534434; exact APK paths assets/pmtiles/synthetic_test.pmtiles (462 bytes), assets/pmtiles/synthetic_manifest.json (525 bytes), three map_styles JSON files (238, 416, 698 bytes). No embedded source-backed road intelligence DB.
