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
