# Error log
- 2026-11-14: Initial repository contained only README.md, so there was no APK/embedded geo asset to deep scan. Status: BLOCKED ON SOURCE INPUT.
- 2026-11-14: Current local runtime lacks Android SDK, Gradle and APK packaging tools. Status: BLOCKED FOR LOCAL ANDROID BUILD; GitHub Actions environment planned.
- No real source-backed speed limit or traffic sign records have been found. Status: BLOCKED FOR DATA COVERAGE.
- CI: Phase 0 push workflow run 43589361023 succeeded; the PR-triggered workflow must be checked before merging.

- Phase 1 initial build workflow failed in `android-actions/setup-android@v3`: default deprecated SDK package `tools` could not be found. Corrected by pinning `ubuntu-24.04` and specifying `platform-tools`, `platforms;android-35`, `build-tools;35.0.0`. Rebuild pending.

- Phase 1 Android CI compiler identified missing `dp` import in MainActivity; fixed in commit 517c238d.
- Next compiler run detected preference property-setter JVM signature clashes; renamed method API `setX` to `updateX` and updated call sites in commit 9224e0b8.

- Phase 1 method collision fixed on commit 9224e0b8. Android compile, unit tests and lint all passed in CI run 43590922509. No known build-blocking error remains at that build head.
- Device UI launch/pixel-accuracy: NOT YET VALIDATED, tracked as pending quality work.


## Phase 2 build and runtime tracking (2026-11-14)
- MapLibre 13.7.1 Kotlin metadata 2.2 incompatible with old Kotlin 2.0.21 compiler: upgraded Kotlin Android and Compose plugins to 2.2.10; verified compiler success.
- Compose Lint warning-as-error on produceState assignment: replaced with remembered state + LaunchedEffect/IO.
- Emulator instrumentation test compile error on non-existent assertExists top-level import: import removed on 87d50aee. Emulator test needs a passing run before runtime acceptance.
- Outbound OSM tile URL is user-opt-in manual testing only; no production service suitable for 50 continuous drivers or offline packages yet.

- Phase 2 emulator test import error fixed on 87d50aee; final 43593588383 PASS (1/1). Prior compiler, lint and instrumentation failures fixed; no known current compile-blocking issue.


## Phase 3 – 2026-11-14
- Discovered MapLibre Android cannot directly read PMTiles from assets: asset:// source lacks byte-range support. Fixed by verified copy to private filesDir and native pmtiles://file:// URL.
- Python versions produce different gzip OS metadata bytes when mtime=0. First deterministic binary regeneration test failed; normalized gzip OS byte to 255 to match SHA-256 of the committed fixture; Phase 0/PMTiles tests later passed (run 43602874345).
- Real offline road datasets, legal speed restrictions and traffic sign positions are NOT provided. Do not fake these from the demo grid.
- Android emulator PMTiles 2/2 test passed on first phase3 commit. Subsequent code-free gzip and test changes still require final CI checks.

- Phase 3 Python gzip determinism mismatch fully corrected by fixing OS header to 255 in commit ff8ce525; latest CI 43603204053 passed. No active Phase 3 build blocker after 43603204092 / 43603204072. Real offline map input remains unavailable.


## Phase 4 – verification and external blockers
- Code PR #7 no active Kotlin/build failure. All three workflows passed on code head: Python/SQLite 43604517491; Android unit/build/lint 43604517429; Emulator 3/3 43604517455.
- BLOCKED: no licensed 34-province PMTiles/POI/routing source or vetted remote catalog; no legally verified speed limits or sign locations.
- NOT DONE: app-scoped downloader does not offer Android OS-resilient background WorkManager jobs and scheduled auto-updates. Partial file survives process restart but download must be restarted manually when catalog is supplied.
- No public OSM Foundation bulk tile downloads or network GPS transmission performed.


## WorkManager Phase 4 – pending final verification
- Initial CI run 43606081949 failed Kotlin compiler because a labelled return used a newline before Result.failure. Fixed after commit 20d6952; rerun required.
- Official AndroidX CoroutineWorker.onStopped is final: cancellation via coroutine completion/OkHttp timeout instead of overriding.
- No approved province PMTiles source or real speed/sign DB. Android background quotas and user force-stop behavior not claimed fully validated.

- WorkManager final Kotlin fix verified: CI Android 43606534434 and emulator 43606534445 (4/4 tests) both successful; PR #9 merged as e1fc7dc. Existing prior Phase4 note saying WorkManager NOT DONE refers to the older PR #7 and is superseded by this entry.
