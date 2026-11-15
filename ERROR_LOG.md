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


## Phase 4 network consent audit
- Detected policy gap: Android WorkManager NetworkType.UNMETERED may include unmetered cellular; user has a separate cellular-download opt-in.
- Added actual active-network TRANSPORT_WIFI/ETHERNET/CELLULAR gate in the worker and persisted explicit allow_cellular=false by default. Awaiting CI validation.

- Phase4 cellular transport guard verified in final CI: 43607450905 (Python), 43607450906 (Android), 43607450907 (emulator 4/4). Merged PR #11 as 64ec5e6. No known current compilation blocker; production 34-province catalog and sign/speed data still unavailable.


## Phase 4 catalog security review — 2026-11-14
- Identified risk: `OfflinePackageManager.startRemote` accepted a caller-built package spec without requiring an independently approved catalog digest; Phase 4 PR #13 adds a trust-gated entrypoint. No caller in the existing Offline UI uses the production remote path.
- There is still no separately authenticated speed-limit database, roadside sign observation collection or licensed province release catalog. No production data was silently synthesized.
- Android validation of new code must be based on final-commit PR CI, not on previous Phase 4 emulator success.


## Phase 4 catalog verified CI closure
- All three checks on the final PR #13 head passed: 43611161271, 43611161247, 43611161298. No current catalog PR build-blocking failure. An intermediate CI run failed when manifest field was renamed before its test assertion was updated; final corrected tests passed.
- APK audit specifically rules out a packaged SQLite/Realm database of real sign coordinates or `speed_kmh` observations; source Kotlin mentions are schema/reader/test strings, not a hardcoded real-road coordinate dataset.
- Remaining safety concern for future Road Intelligence importer: mere nonempty license/source strings are insufficient as cryptographic/field verification. Use independent source approval and checksum before enabling any real-world speed alert.


## 2026-11-14 Phase 4 road approval review
- Risk discovered: `RoadIntelligenceRepository.read()` previously trusted presence of source/license metadata in any app-private SQLite file. Such metadata is self-attested and not independent evidence. Corrected via empty-by-default, SHA-pinned `RoadDatabaseApprovalGate` before queries.
- SQLite main-file hashing is insufficient when mutable WAL/journal sidecars exist; gate now rejects `-wal`, `-shm`, `-journal` unless a future signed immutable release design handles them explicitly.
- Candidate audit is structural only; an apparently clean DB is still NOT independent legal or physical field proof. No production sign/speed data is included.
- New Kotlin and Python tests must pass CI; see PR #15.


## Road Intelligence gate CI verified
- PR #15 code passed all required final-head workflows (Python 43614134722, Android 43614134733, Emulator 43614134877); merged as dd53c1a. No known build blocker from this change.
- Remaining limitations are *source, legal and field verification*, not a fixed compilation issue. No OSM maxspeed inference, fabricated sign positions, or driver speed alerts were enabled.
- Runtime DB sidecars intentionally fail closed; a future publisher must checkpoint the database and include only the independently approved immutable bytes.


## Phase 4 OSM PBF source audit (PR #17)
- Local development runtime lacks pyosmium and cannot reach PyPI; GitHub Actions installed pinned osmium 4.3.2 successfully and executed the binary-PBF regression test without skipping it (run 43617224402). No local 317MB Vietnam extract or Geofabrik live data was claimed.
- Main residual data risk: OSM maxspeed* strings have conditional/directional/advisory/mph semantics; OSM way traffic_sign tags are not surveyed sign points. Reference staging retains them unconverted, disables all alerts and forbids promoting to approved SQLite.
- APK audit run 43617224403 showed no production speed/sign DB; no compile failure in source-code run.

- PR #17 final CI had no build or PBF parser failure. Python 36/36 PASS (43617538573), Android build/unit/lint PASS (43617538560), merged 8b6d1f7. Remaining blockers are authentic source snapshots, legal/field validation and offline route/data distribution.


## Verified Vietnam OSM data reference QA results
- Raw OSM was actually parsed with pyosmium from dated Geofabrik PBF (PR #19), and data quality tool added (PR #20). No known Python or Android CI failures on final code head: Python 51/51 PASS 43625497790, Android PASS 43625497719.
- Remaining incomplete work is regulatory applicability, physical sign direction/position field evidence and safe production offline packaging, NOT a source parser or APK compilation error. No approval pin or driver safety alert has been enabled.


## PR #22 survey worklist negative-test correction (2026-11-15)
- First PR head Python CI run 43659783325 failed **one test assertion** for existing output: the generator correctly raised `ReviewQueueError` because the ZIP archive existed, but test expected only `FileExistsError`. No output was overwritten.
- Corrected test to accept either explicit fail-closed rejection; reran full Python tests SUCCESS 43659839106, Android build/unit/lint SUCCESS 43659839088 on commit `b220ea1121fb4ee4d070cd786ffaa1ce74418627`.
- Remaining blockers are missing true field surveys, legal applicability/vehicle class and accurate road geometry, not compilation failure. No automatic real speed, point or driver alert was added.

- PR #22 final-head CI acceptance confirmed: Python 60/60 tests SUCCESS 43660068830, Android assemble/unit/lint SUCCESS 43660068771, merged main 39cf3185ee91239c21ec0f6d57246e79ed006bf6. No unresolved code/build errors from this work.


## 2026-11-15 field/legal evidence audit open risks
- New evidence intake checks structural completeness, byte hashes, GPS numeric plausibility and official-source URL shape; it cannot authenticate human identity, true photo location, direction of application or definitive current Vietnamese legal interpretation. A mechanically ready item MUST remain unapproved pending independent review.
- Initial PR #24 Python CI caught unrecognized official Government Gazette host `congbao.chinhphu.vn`; URL allowlist corrected. After linking speed packets to physically evidenced signs, formerly isolated sign-negative tests needed to exclude dependent speed packets; regression expectations corrected. Final code-head 78/78 PASS 43661967753, Android PASS 43661967823; production data remains blocked.
- Real 2026-11-12 review ZIP and actual physical survey photos are not in the repository or Android APK; no live evidence review has been run.
