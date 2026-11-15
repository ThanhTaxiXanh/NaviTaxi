# Execution backlog (no phases may be silently skipped)

- Phase 0: DONE, CI passed and PR #1 merged.
- Phase 1: CORE DONE and PR #2 merged; accurate device pixel matching remains Phase 15.
- Phase 2: DONE for experimental renderer, consent/attribution and emulator smoke. PR #3 merged. Actual street-data completeness is NOT claimed.
- Phase 3: DONE for verifiable synthetic offline PMTiles demonstration (2/2 Android emulator tests) + checksum + HTTP Range probe; merged PR #5. Real geography remains Phase 5.
- Phase 4: CORE VERIFIED and merged PR #7; full phase INTEGRATION BLOCKED pending WorkManager/background delivery, signed-off catalog and scheduled updates. Cannot claim province package availability.
- Phase 5: 34-province metadata and national coverage with lawful geodata.
- Phase 6: GPS/compass, privacy and power profile.
- Phase 7: validated routing/navigation/taximeter.
- Phase 8: traffic-engine sourced traffic and stale-state UI.
- Phase 9: search and POI verified against local data.
- Phase 10: 3D data renderer.
- Phase 11: **road intelligence** with verified speed limits and sign coordinates: data import + spatial map matching + audible warnings + device tests.
- Phase 12: Vietnam Geographic Engine with sourced archival/legal materials.
- Phase 13: measurable performance.
- Phase 14: automated and device QA.
- Phase 15: screenshot layout/pixel tests on Android device sizes.
- Phase 16: signed NaviTaxi.apk build (requires signing decisions).
- Phase 17: installation and driving-safe tests.
- Phase 18: documentation and maintenance.

## Blockers
- No licensed geo speed/sign datasets present. Never fill gaps with guesses.
- No local Android SDK; use GitHub Actions and Android runner for build.
- Real 100% UI reproduction depends on matching device resolution and source graphic assets; do not claim it without screenshots and acceptance tests.


## Phase 4 active checks
- Validate PR #9 WorkManager/foreground service Kotlin compatibility, Android emulator launch and final APK manifest.
- Confirm no .db/.sqlite/.realm speed/sign assets or real sign locations are embedded.
- Add approved signed-off HTTPS PMTiles catalog before activating remote downloads or automatic version checks; no public OSM tile server bulk use.
- WorkManager can reschedule work on system stop, but user force-stop and Android 15 dataSync time limits require field testing.


## Phase 4 catalog continuation / PR #13
- Add independent catalog pinning before a trusted real PMTiles release is configured; pin must not be published by the same untrusted manifest.
- PR #13 adds the non-networking manifest validator and Android gate. Review full CI results before merge.
- Store verified installed release_sequence durably when a real approved catalog exists; define rollback policy for older installs without sequence.
- Test process death, changed ETag, missing storage and cross-process race under real Android conditions when source exists.
- Do not enable 34-province downloads or legal speed/sign warnings from OSM tag presence alone.


## Next work after accepted PR #13
- Phase 4 catalog verifier + APK asset audit: ACCEPTED infrastructure on main 068c297e; no production source approved.
- Prepare lawful, vetted OSM extract -> own PMTiles pipeline with source snapshot/ODbL review; obtain independent approval for catalog digest and release sequence persistence before enabling downloads.
- Prioritize Road Intelligence source survey/import plan with true WGS84 roadside sign observations and evidence, rather than using OSM way centroids or inferred speed limits.
- Run device/OEM process death, ETag-change, disk-full and connectivity loss tests; emulator passing is not field acceptance.
- Phase 5 remains NOT STARTED/BLOCKED until provenance and baseline catalog are approved.


## Road Intelligence acceptance queue after PR #15
- Verify and merge independent SHA-pinned road DB gate only after all three PR CI workflows pass; do not populate the approval allowlist from unreviewed SQLite.
- Source-gathering follow-up: legally usable Vietnam OSM snapshot and independent speed-sign ground surveys with WGS84 coordinates, sign_code, direction, applicability and observation date.
- Review OSM `traffic_sign` node-vs-way semantics; never derive a physical sign coordinate from the center of a road segment or assume an unsurveyed `maxspeed` is enforceable.
- Reconcile verified DB schema, provenance and checksum at publication. Keep 34-province offline catalog blocked without approved distribution/license chain.


## After verified PR #15 — next Road Intelligence work
- PR #15 secure SQLite source approval and candidate audit: VERIFIED infrastructure and merged. Do not repeat the gate unless a substantive flaw is found.
- Locate and lawfully extract Vietnam OSM tags (`maxspeed`, `traffic_sign`) into a reference-only staging inventory with SHA, original object IDs and source version; prevent tags from becoming legal alerts without separate reviewer evidence.
- Obtain real roadside sign coordinate surveys (WGS84 lat/lon, bearing, direction, road applicability and observed/verified timestamps) and vehicle-class-specific legal speed applicability.
- Review ODbL, independent source permissions and field QA before populating `RoadIntelligenceApprovedPins` with any real database SHA.
- Keep Phase 4 and Phase 5 blocked where real approved offline data and field tests are absent.


## Next tasks after OSM reference-only staging
- PR #17 independently pinned OSM reference extractor: CI PASSED and MERGED. Do not label this reference tooling as validated Vietnam road coverage.
- Secure a lawful Vietnam Geofabrik snapshot with source URL, size, timestamp, ODbL review and exact SHA-256; run the streaming extractor only into build/reference staging, not Android assets.
- Report genuine candidate counts from that actual PBF only after parsing; keep OSM tags separate from the verified SQLite/RTree and speed/sign map overlays.
- Validate each applicable legal speed by travel direction, vehicle class, date and signs; field-confirm the physical WGS84 sign location and orientation before proposing an independently approved database pin.
- Phase 4 approved PMTiles catalog, OTA version storage, process-death and field/OEM reliability remain blocked; Phase 5 NOT STARTED.


## Next tasks after REAL Vietnam OSM snapshot audit (PR #19)
- Raw Vietnam OSM source obtained and hashed; do NOT call 44,472 OSM-tagged ways legal speed observations or 810 OSM node coordinates field-surveyed physical traffic signs.
- PR #20 OSM source data QA accepted, 51/51 Python tests PASS 43625497790, Android PASS 43625497719; merged main 68b8f3ba8cea94e982397e9797d8da3b9f348a35. Do not re-enable any unverified legal speed or physical sign alert.
- Independently source applicable Vietnamese road law, vehicle type/direction, dated physical sign surveys and reliable WGS84/bearing evidence before populating production `RoadDatabaseApprovalGate` pins.
- Review ODbL derivative data distribution and preserve upstream object provenance/attribution. Do not publish unverified source as a driver speed/sign overlay.
- Phase 4 real licensed 34-province PMTiles map packages, scheduler OEM/background road tests remain blocked. Phase 5 NOT STARTED.


## Next after OSM review worklist generation
- PR #22 source-pinned survey/legal worklists ACCEPTED and MERGED as 39cf3185ee91239c21ec0f6d57246e79ed006bf6 (Python 43660068830, Android 43660068771 PASS).
- Prioritize real-world legal verification for 44,472 speed-tag way **candidates**, checking current 74/2026/VBHN-TT-BXD and applicable amendments, road geometry, class, direction, vehicle, conditional applicability and actual posted signs. A numeric `maxspeed` tag is not site-specific law.
- Survey 810 original OSM node-point **candidates** with physical GPS survey, sign code, facing, date, road relation, photo evidence/hash, review and lawful provenance. A tagged OSM way has no physical sign point.
- Reassess 654 unknown-type sign tags; do not interpret `traffic_sign=yes` as speed sign or infer physical location; obtain source geometry before matching raw speed-way IDs to road segments.
- Do not set `RoadIntelligenceApprovedPins` or enable alerts before separate legal and field evidence review, source license review and device tests. Approved real speed/sign counts remain zero.


## After field/legal evidence intake implementation (2026-11-15)
- PR #24 code-head 78 Python and Android build/unit/lint/APK checks passed. Verify final documentation-head CI and merge only if green.
- Obtain original SHA256-pinned 1,170,686-byte review ZIP and private physical surveys/photos. Do not treat OSM nodes as measured sign positions.
- Independently validate real sign WGS84/bearing, photo, direction and road geometry; independently validate actual vehicle/date-specific legal speed and posted sign relation.
- Mechanical READY_FOR_HUMAN_REVIEW does not imply verified sign/speed. Separately review ODbL and publisher permissions, create only scrutinized SQLite/RTree data, code-review any future exact SHA pin and field-test actual driver warnings.


## After conflict quarantine PR #25
- Code-head Python and Android gates passed on PR #25; verify final docs-head CI and merge only on green checks; confirm post-merge main.
- Obtain legitimate field measurement/photographic evidence of sign position, orientation and actual applicability, plus legal vehicle/date/direction review. No OSM tag is approved by this tooling.
- Keep 811 OSM sign objects, 44,472 OSM speed-way review entries in UNVERIFIED state, all real verified counts ZERO, release pins empty, Phase 4 IN PROGRESS and Phase 11 alerts BLOCKED.


## Phase 11 private field-sign/speed evidence archival
- Verify CI on PR #26, fix any synthetic test failures, merge only if Python/SQLite
  and Android assemble/unit/lint/APK road-asset audit green; check post-merge main run.
- Private operators must independently obtain the expected unverified real queue ZIP
  (SHA256 26891bd61d10cb6228f30db5201af275254832b0705a5c553731df7f24c7df7c)
  and lawfully collect original GPS/photo/road/law evidence to create a local archive.
  No such original private materials are in Git.
- Require a human legal check and real sign-location/direction survey before proposing
  any domain-specific, separately approved SQLite release digest. Do not infer speeds
  from OSM maxspeed and do not turn on alerts before verified release and on-device tests.
