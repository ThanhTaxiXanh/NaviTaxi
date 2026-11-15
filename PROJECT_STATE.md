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


## Phase 4 network consent follow-up
- Branch phase-4/strict-cellular-consent: worker explicitly checks actual Wi-Fi/Ethernet/Cellular transport even after WorkManager UNMETERED scheduling, so metering status cannot override explicit no-cellular preference.
- This fix does not create province geodata, legal speed-limit records or roadside sign coordinates. Final CI PASS: Python/SQLite 43607450905, Android build/unit/lint 43607450906, emulator API35 4/4 43607450907; PR #11 merged as 64ec5e6e5bca5e82808b201939873ca80f87dc33.


## Phase 4 trusted catalog gate — PR #13 (2026-11-14)
- Working branch: `phase-4/catalog-integrity-release-gates`; PR: https://github.com/ThanhTaxiXanh/NaviTaxi/pull/13.
- New Python/Android validators require a separately pinned SHA-256 over entire offline catalog JSON; no production pin or live catalog bundled.
- Android `OfflinePackageManager.startRemote` now takes only `TrustedOfflineCatalog` and package ID, no raw unapproved spec.
- Catalog release_sequence makes rollback/equal-sequence mutation detectable; no auto-download/version polling enabled.
- PMTiles metadata cannot claim it has verified speed limits or traffic sign coordinates. The real road DB remains ABSENT.
- Python/SQLite PR CI 43610420031 SUCCESS; Android compile/emulator PR gates tracked separately.
- Phase 4 remains IN PROGRESS / BLOCKED for approved geodata and field validation; Phase 5 NOT STARTED.


## Verified catalog / APK audit handoff — 2026-11-14 (supersedes PR #13 pending status)
- PR #13 https://github.com/ThanhTaxiXanh/NaviTaxi/pull/13 MERGED to main as `068c297e1df55466ba0adc50b05755192814087b`.
- Final head `468c49ae565225f7264d492360af665c639f5097`: Python/SQLite CI 43611161271 SUCCESS; Android assemble/JUnit/lint and built-APK road audit 43611161247 SUCCESS; Android API35 emulator 43611161298 SUCCESS.
- APK audit produced `apk-road-audit.json` and `apk-road-assets.zip` in artifact `phase4-apk-road-asset-audit` (artifact ID 14119833707), includes original asset files, source schema, manifest and SHA256SUMS; inventory hashes checked.
- APK internal: exactly five non-real assets (3 JSON styles 238/416/698 bytes; synthetic JSON manifest 525 bytes; synthetic PMTiles 462 bytes, SHA256 d9a53b380463498cc31fd59a30d00e07a2f3f32f9f894eefa7b796d20470de9c).
- PMTiles v3 header: 127 B, 1 addressed tile, root offset 127/25 B, metadata offset 152/245 B, tile bytes at offset 397/65 B; this is a synthetic drawing, NOT a road network.
- **Zero real speed limits and zero field-verified roadside sign coordinates.** No `road_intelligence.db` / other data DB shipped. Phase 4 remains IN PROGRESS with real map catalog/source approval and field proof BLOCKED; Phase 5 NOT STARTED.


## Phase 4 Road Intelligence independent dataset approval gate (PR #15)
- Branch `phase-4/road-intelligence-approval-gate`; PR https://github.com/ThanhTaxiXanh/NaviTaxi/pull/15.
- Android `RoadDatabaseApprovalGate.kt` checks the exact runtime `road_intelligence.db` SHA-256 against independently code-reviewed pins; `RoadIntelligenceApprovedPins.entries` is deliberately EMPTY. SQLite `-wal/-shm/-journal` sidecars are rejected.
- Separate approval booleans for legal speed-limit records and actual surveyed physical sign coordinates; without a matching approval the map repository returns empty GeoJSON and zero counts, even if DB metadata self-attests a license.
- Added offline `scripts/review_road_candidate.py` for SQLite v1, source evidence, geometry, WGS84, verification timestamps, RTree and SHA-256 audit; report never approves driver alerts.
- New synthetic-only JUnit/Python/API35 emulator tests; CI acceptance tracked in PR #15.
- No real source DB, no measured sign position and no legal speed record added. Phase 4 IN PROGRESS/BLOCKED for licensed release sources and phone field tests; Phase 5 NOT STARTED.


## Verified Road Intelligence approval-gate handoff — 2026-11-14
- Code PR #15 https://github.com/ThanhTaxiXanh/NaviTaxi/pull/15 MERGED as main `dd53c1a43991f350ffa980091e4db1faabeddccf`.
- Final PR head `26d75df6c0751df89a060d0efc1e209ff65b5078`: Python/SQLite candidate/road audit PASS run 43614134722; Android assemble/JUnit/lint+APK scan PASS run 43614134733; API35 emulator PASS run 43614134877.
- Candidate audit evidence GitHub artifact ID 14121745051 (ZIP SHA-256 879a17910a724fbebedc6a637f9475badde2a38417b2e989b40450092958d3de). Empty canonical road DB = 86,016 bytes, SHA256 87193a1b8af8fa2e17c56a2bb9f03c533378321335653590fefae2c8a91de584; 0 sources/roads/signs. JSON status `EMPTY_DATABASE`, approval flags both FALSE.
- APK inventory on same final head: 5 synthetic assets, no approved road DB; archived file hashes match MANIFEST. `RoadIntelligenceApprovedPins.entries` remains empty; speed/sign overlays cannot be activated using only self-attested source/verification dates.
- Overall Phase 4 remains IN PROGRESS/BLOCKED (real lawful download catalog, device/OEM field proof). Phase 5 NOT STARTED. Real vehicle-applicable speeds and physical roadside sign coordinates remain 0 verified.


## Phase 4 OSM speed/sign reference-only staging — PR #17 (2026-11-14)
- Branch phase-4/osm-road-reference-staging; PR: https://github.com/ThanhTaxiXanh/NaviTaxi/pull/17.
- New scripts/extract_osm_road_reference.py streams local SHA-256-pinned .osm.pbf (BSD-2-Clause pyosmium 4.3.2) or .osm XML. It preserves raw maxspeed*/traffic_sign* tags, OSM object type/id/version/time and node-only original coordinate. Way/relation sign coordinates stay NULL.
- Reference-only outputs: JSONL speed/sign files, provenance/ODbL manifest, SHA256SUMS ZIP. No output under Android assets or approved SQLite, no legal speed_kmh inference, no physical-sign survey verification, no driving alerts.
- Code-head Python/SQLite run 43617224402: SUCCESS, all 36 tests including actual PBF parser test; Android assemble/unit/lint run 43617224403 SUCCESS. Final documentation-head verification still required before merging PR.
- Synthetic evidence artifact ID 14121689381 (ZIP SHA256 8b6c4304cc55fefec8ef9af5222445d47b084630147e9fa6c4bca35f8618c2fb): 1 speed-tag way, 2 sign-tag nodes, 1 sign-tag way, 1 sign-tag relation; ALL UNVERIFIED, no authoritative records.
- Built APK audit artifact ID 14122562328: exactly five synthetic assets (styles 238/416/698 B; manifest 525 B; PMTiles 462 B), and zero verified real sign/speed records.
- No Vietnam Geofabrik PBF was downloaded, imported, geocoded, or distributed. Phase 4 remains IN PROGRESS / BLOCKED on real lawful sources and field evidence; Phase 5 NOT STARTED.


## Verified OSM PBF reference pipeline handoff (2026-11-14)
- PR #17 https://github.com/ThanhTaxiXanh/NaviTaxi/pull/17 MERGED as main `8b6d1f7ae9f995948364bdffcabf0208283a6c3d`.
- Final PR head `95da2a517f29893e249e253754fcfe4530e54bc5`: Python/SQLite + pyosmium actual PBF test PASS 43617538573, Android assemble/JUnit/lint + APK audit PASS 43617538560.
- Source test artifact `phase0-road-data-evidence` includes JSONL/manifest/SHA256SUMS ZIP. Synthetic only: 1 tagged speed way, 2 tagged sign nodes, 1 tagged sign way, 1 tagged sign relation. All approval flags FALSE.
- Built APK asset audit still finds exactly 5 test-only assets and 0 real speed/sign records. Original absolute paths within APK and bytes are in BUILD_STATUS.md.
- Real Geofabrik Vietnam PBF was NOT downloaded or examined. Phase 4 remains IN PROGRESS/BLOCKED for lawful real datasets, catalog and field proof. Phase 5 NOT STARTED.


## Phase 4 real Vietnam speed/sign OSM snapshot acquired (2026-11-15)
- PR #19 https://github.com/ThanhTaxiXanh/NaviTaxi/pull/19 MERGED main `8e9ad423100234b022506667b269f25d0a3df556`. Main post-merge Android build 43624954395 SUCCESS.
- REAL Geofabrik Vietnam snapshot 2026-11-12 `vietnam-261112.osm.pbf` 332,558,874 bytes. SHA256 `ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed`, publisher MD5 `1f7716ad049551852fc281e969a000aa`.
- REAL PBF CI https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43624034669 PASS; source integrity + streaming PBF extracted EXACTLY 44,472 OSM speed-tagged ways, 810 OSM sign-tagged nodes, 1 sign-tagged way and 0 sign relations. This is OSM reference data ONLY; physical sign surveys: 0 verified; enforceable legal speed records: 0 verified.
- Audited 810 original OSM node coordinates, 68 ways with conditional speed tags, 276 with advisory, no mph variants in real snapshot. Not human-verified law/sign positions.
- GitHub source audit evidence artifact 14124844201 digest sha256:42352c12807767bfbe7ae4af26a060ad156443e2b05411496f7b0c63d47a5370; verified JSONL counts, nested archive SHA256SUMS and all approval flags FALSE.
- PR #19 final-head Python SQLite CI 43624034554 SUCCESS, Android compile/test/lint and APK asset deep scan 43624034656 SUCCESS. APK still 5 synthetic assets; no real `road_intelligence.db`, signed legal rules, surveyed physical signs or production alarms.
- Follow-up source quality audit in `scripts/audit_osm_reference_quality.py`, tests and docs; source reference-only staging remains separate from Android approval.
- **Phase 4 is STILL IN PROGRESS** (legally approved offline map catalog and field/OEM reliability blocked); Phase 5 NOT STARTED; Phase 11 Road Intelligence law/survey approval blocked.


## Verified Phase 4 real Vietnam source and separate QA — final handoff, 2026-11-15
- PR #19 merged as `8e9ad423100234b022506667b269f25d0a3df556`; actual 333MB source audit 43624034669, Python 43624034554 and Android 43624034656 all SUCCESS. Main postmerge Android build 43624954395 SUCCESS.
- PR #20 https://github.com/ThanhTaxiXanh/NaviTaxi/pull/20 merged as `68b8f3ba8cea94e982397e9797d8da3b9f348a35`. Final-head code Python provenance/OSM quality/SQLite tests **51/51 PASS** https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43625497790; Android build/JUnit/lint+APK asset deep scan PASS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43625497719.
- New `scripts/audit_osm_reference_quality.py` checks manifest vs exact file lengths/SHA256, source receipt, raw tag semantics, uniqueness, WGS84 node coords, NULL sign-way physical coordinate, unverified status and input tampering. Never computes legally approved speeds or field-surveyed signs.
- Actual OSM reference evidence remains: 44,472 speed-tagged ways, 810 sign-tagged nodes with original OSM point, 1 sign way; 0 independent legal speed validations, 0 physical sign surveys. Snapshot SHA256 `ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed`. Raw PBF is not shipped in APK.
- Phase 4 IN PROGRESS: approved lawful speed/sign data, on-device field surveys and province map release catalog are still BLOCKED. Phase 5 NOT STARTED. No driver warnings permitted from OSM reference-only data.


## Phase 4 OSM field survey and legal speed review queues — PR #22 (2026-11-15)
- Branch `phase-4/field-survey-review-queues`, PR https://github.com/ThanhTaxiXanh/NaviTaxi/pull/22.
- New `scripts/build_road_review_queues.py` consumes separately hash-audited OSM speed/sign JSONL; emits 811 physical-sign REVIEW candidates (810 OSM nodes and one way with no coordinate) and 44,472 legal-speed REVIEW way IDs, **not** speed limits or surveyed signs.
- Original snapshot SHA: `ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed`. Review ZIP on this session's mounted real reference source: 1,170,686 bytes, SHA256 `26891bd61d10cb6228f30db5201af275254832b0705a5c553731df7f24c7df7c`; internal SHA256SUMS verified.
- Sign triage: 654 unknown type, 156 specific raw tags requiring field survey, one way with no physical point. Speed way triage: 41,356 plain numeric raw tags (still not legal), 2,924 without main maxspeed, 192 conditional/directional/advisory tags.
- Both CSVs leave all reviewer, position survey and legal-evidence columns blank; all statuses PENDING_INDEPENDENT_REVIEW, approvals FALSE. This does not create/import `road_intelligence.db`, or modify the empty Android source approval pin list.
- Current legal research reference: official Government Gazette `74/2026/VBHN-TT-BXD` dated 2026-09-15, https://congbao.chinhphu.vn/van-ban/van-ban-hop-nhat-so-74-2026-vbhn-tt-bxd-470578/68818.htm ; NOT a per-road speed mapping or automatic rule.
- Code-head CI after one test expectation correction: Python/SQLite 43659839106 SUCCESS; Android assemble/unit/lint/APK 43659839088 SUCCESS. Final PR docs-head acceptance/merge pending. Phase 4 IN PROGRESS; Phase 5 NOT STARTED; 0 real driver-approved speeds and field-signed signs.


## Verified field-sign and legal-speed worklist handoff — 2026-11-15
- PR #22 https://github.com/ThanhTaxiXanh/NaviTaxi/pull/22 MERGED as main `39cf3185ee91239c21ec0f6d57246e79ed006bf6`.
- Final PR head `17acfac4e3c5c035abe2748b02351f2bf038ec1b`: Python/SQLite/source review worklists 60/60 PASS run 43660068830; Android build/JUnit/lint/APK audit PASS run 43660068771.
- Synthetic test evidence artifact ID `14140060222` from code-head run 43659839106 includes mock-only CSV queue/checksum ZIP; PR final-head run 43660068830 also accepted. No real PBF re-downloaded.
- Real source review queue archive separately generated and verified: `NaviTaxi_Vietnam_2026-11-12_Field_Sign_Speed_Review_UNVERIFIED.zip` 1,170,686 B sha256 `26891bd61d10cb6228f30db5201af275254832b0705a5c553731df7f24c7df7c`. Source snapshot SHA `ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed`.
- Sign object triage: 654 unknown code, 156 specific OSM tag needing physical field survey, 1 way without point. Speed way triage: 41,356 unverified plain numeric, 2,924 without primary maxspeed, 192 complex/directional/conditional. All 45,283 review rows have blank reviewer/evidence and approval FALSE.
- Source legal research portal: 74/2026/VBHN-TT-BXD (official consolidated circular, 2026-09-15), not per-way legal speed proof. No field signs actually surveyed and 0 legal speed records approved.
- Phase 4 remains IN PROGRESS/BLOCKED (licensed real PMTiles/catalog and field/OEM evidence). Phase 5 NOT STARTED. Phase 11 driver warnings not enabled.


## 2026-11-15 Phase 11 independent evidence intake continuation (PR pending CI)
- Main starting commit e2a1fdd6b25233a42b91ab4d58cbbd5b485058a0. Current work branch `phase-11/field-evidence-intake-gate`.
- Added scripts/review_road_field_evidence.py and synthetic-only tests to mechanically screen separately collected photo/GPS/sign/road/vehicle/law review packets against an exact SHA256-pinned review ZIP.
- No new physical surveys, accepted legal-road-speed records, SQLite source DB or Android SHA pin. Driver alerts remain explicitly disabled and reported approved counts remain ZERO. PR #24 code-head 32a2d7d2 CI verified: Python/SQLite 78/78 PASS (43661967753), Android build/JUnit/lint/APK audit PASS (43661967823). Final documentation-head CI and merge must still be checked.


## Phase 11 sign/speed evidence conflict quarantine (PR #25; CI pending)
- Base main SHA 5c950d31147b672bc025ecbaf9b1c6b5222e7032; implementation branch phase-11/conflicting-field-evidence-quarantine.
- Any repeated sign source ID, physical sign point/code or image SHA now quarantines all implicated entries and related speed reviews. Matching sign/road geometry and observation order required; legal date checks hardened.
- Exact archived OSM reference queues remain unapproved: 811 sign candidates, 44,472 speed ways, zero verified real speeds/sign locations. RoadIntelligenceApprovedPins still empty and Android driver alerts blocked.
- PR #25 Python/Android acceptance and post-merge main CI must be verified before claiming completion.
