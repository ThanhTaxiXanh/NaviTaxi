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

- Phase 4 stricter network transport consent: save explicit allow_cellular flag, check actual connectivity transport at worker runtime (unmetered cellular blocked by default). Code PR #11 merged as 64ec5e6 after green 43607450905/906/907 CI.


## 0.4.2-dev — Phase 4 pinned catalog integrity (PR #13)
- Added Python/Android offline PMTiles catalog validators with independent SHA-256 pin and non-secret source metadata.
- Prevented unpinned callers from scheduling remote downloads through OfflinePackageManager.
- Added monotonic release_sequence and rollback/equal-sequence conflict detection; no version polling or production release has been activated.
- Forbid PMTiles catalog claims of legally verified speed limits and physical traffic sign positions.
- Added Python/Android test cases and source-provenance documentation. Real 34-province data remains blocked.


## 0.4.2-dev — accepted Phase 4 catalog guard / audit
- Code PR #13 MERGED to main as 068c297e1df55466ba0adc50b05755192814087b after Python, Android and emulator CI passed on final head (43611161271 / 43611161247 / 43611161298).
- New Actions APK forensic inventory and ZIP with SHA256SUMS, JSON shape and SQLite/PMTiles structural inspection. The synthetic asset inventory was inspected; no real speed/sign dataset found.
- Catalog integrity, provenance and anti-rollback gates accepted **as infrastructure only**. Licensed 34-province maps and surveyed road signs remain unavailable; no automatic production updates enabled.


## 0.4.3-dev — candidate data QA and fail-closed Road Intelligence (PR #15)
- Introduced independently pinned SHA-256 approval for complete SQLite speed/sign datasets; approved scopes separate legal speed-limit observations from physical roadside sign coordinates.
- Rejected unapproved SQLite/WAL/journal overlays; source/license strings alone cannot turn on verified map data.
- Added candidate data audit for schema v1, SQLite/RTree and coordinates, explicit `CANDIDATE_REQUIRES_INDEPENDENT_FIELD_REVIEW` status. No automatic approval or map source download.
- Added Kotlin JUnit, Android API35 instrumentation and Python negative tests plus CI report artifact.
- Authentic legally verified signs/speed records remain unavailable; Phase 4 not fully complete.


## 0.4.3-dev — verified Road Intelligence gate accepted
- PR #15 MERGED: https://github.com/ThanhTaxiXanh/NaviTaxi/pull/15 as dd53c1a43991f350ffa980091e4db1faabeddccf.
- Python candidate/audit 43614134722, Android build/lint/unit 43614134733 and API35 emulator 43614134877 all PASS at final code head.
- Independent road DB hash pin and per-domain speed/sign approval enforce fail-closed map overlays. Candidate report cannot turn on alerts; no real map or source-backed sign/speed data introduced.


## 0.4.4-dev — OSM raw road reference staging (PR #17)
- Added local SHA-pinned streaming OSM XML/PBF reader, preserving raw maxspeed and traffic_sign tags, original IDs and source provenance; no automatic legal km/h interpretation or inferred physical sign coordinates.
- Added reference-only JSONL/manifest/SHA256SUMS ZIP and safeguards against Android asset/SQLite ingestion.
- CI pinned BSD-2-Clause pyosmium 4.3.2, added XML/PBF and archive negative regression tests. Code head Python 36/36 PASS (43617224402), Android assemble/unit/lint PASS (43617224403).
- No production map catalog, Geofabrik input file, approved real-road speeds or physical sign observations added; Phase 4 remains open.

- PR #17 code accepted and merged on 2026-11-14 as `8b6d1f7ae9f995948364bdffcabf0208283a6c3d` after final-head Python 43617538573 and Android 43617538560 successful CI. Reference staging is tested infrastructure; actual 34-province speed/sign mapping remains blocked.


## 0.4.5-dev — Real dated Vietnam OSM source provenance and reference QA
- PR #19 MERGED as 8e9ad423100234b022506667b269f25d0a3df556: bounded, provenance-checked acquisition of 2026-11-12 fixed-date Geofabrik Vietnam OSM PBF (332,558,874 B; SHA256 ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed).
- Real CI source run 43624034669 PASS: 44,472 speed-tagged OSM ways and 811 sign-tagged OSM objects (810 nodes + 1 way); none legally or physically field verified. Original source bytes not shipped.
- Added follow-up independent JSONL/receipt/sign-coordinate/raw-speed QA and regression tests; release restrictions remain false by default. Phase 4 and field verification remain blocked.


## 0.4.5-dev accepted source-audit handoff
- PR #20 merged as `68b8f3ba8cea94e982397e9797d8da3b9f348a35` after final-head 51/51 Python tests PASS 43625497790 and Android build/unit/lint + APK audit PASS 43625497719.
- The published source evaluation contains original Geofabrik Vietnam 2026-11-12 PBF SHA and measured raw `maxspeed` / `traffic_sign` candidates. Strict quality analysis still permits **ZERO** legally verified speed or physically surveyed sign alerts.


## 0.4.5-dev – field survey and legal speed review worklists (PR #22)
- Added `scripts/build_road_review_queues.py` to generate manifest/SHA256SUMS-pinned OSM legal-speed and field-sign review CSV queues from already audited reference, without production approval.
- Preserves original OSM type/ID/version, raw tag strings and unverified node coordinates; sign-tag way/relation never gains fabricated coordinates. All survey/legal/evidence inputs blank and no driver alerts.
- Hardened CSV raw string cells against spreadsheet formula injection and blocked output into Android/verified road assets.
- New synthetic-only regressions and CI review evidence; Python 43659839106 and Android 43659839088 PASS on code head after correcting one negative-test expectation.
- Current official speed research link: 74/2026/VBHN-TT-BXD (15 September 2026), **not** an auto-applied legal maxspeed table. Real sign/speed approvals still zero.

- Review queue implementation PR #22 merged to main `39cf3185ee91239c21ec0f6d57246e79ed006bf6` after final-head Python (60/60, 43660068830) and Android build/lint (43660068771) PASS. Real-snapshot CSV survey and speed legal-review packet remains UNVERIFIED; no driver alerts enabled.


## 0.4.6-dev — Phase 11 field/legal evidence intake gate (pending CI)
- New scripts/review_road_field_evidence.py validates SHA256-pinned survey review ZIP and separately collected photo/GPS/road/legal evidence with fail-closed detailed record reasons; no OSM-derived legal speed or sign point.
- Synthetic negative tests and docs/ROAD_INTELLIGENCE_EVIDENCE_INTAKE.md added; no new Android runtime code, APK data, third-party packages or allowlist pins.
- Every mechanical result explicitly has zero approved records and disabled driver alerts. Code-head Python 78/78 PASS (43661967753), Android build/unit/lint/APK audit PASS (43661967823). Final doc-head CI and merge pending.


## 0.4.7-dev — Phase 11 conflict quarantine (PR #25, pending CI)
- Field evidence audit now quarantines BOTH sides of duplicate sign/source/photo/point and conflicting speed scope; speed reviews citing any rejected sign are also rejected.
- Sign and speed must have the same independent geometry SHA, correct direction/way and chronological field survey. Law review checks cannot predate observation; optional legal expiry rejected if obsolete.
- Reject untrusted driver/DB approval fields in input; no real GPS/speed data or Android trust pins added. New synthetic regressions; code-head Python 86/86 PASS (run 43664352656) and Android build/unit/lint/APK audit PASS (43664352607). Final documentation-head CI pending.
