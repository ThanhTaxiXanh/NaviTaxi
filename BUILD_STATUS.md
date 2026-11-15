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

## Phase 4 strict no-cellular hardening
- Code PR #11 https://github.com/ThanhTaxiXanh/NaviTaxi/pull/11 merged to main as 64ec5e6e5bca5e82808b201939873ca80f87dc33.
- Python/SQLite/PMTiles PASS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43607450905.
- Android debug compile/unit/lint PASS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43607450906.
- Android API35 emulator 4/4 PASS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43607450907.
- Actual branch debug APK 60,285,140 bytes SHA256 34fe6d504e1b492f29b39cfc3ea522a0d7053b03f875ff375d7742df9e580f61; exact PMTiles asset remains 462 bytes, sha256 d9a53b380463498cc31fd59a30d00e07a2f3f32f9f894eefa7b796d20470de9c.
- No real speed/sign DB, approved province PMTiles catalog or production background field validation. Phase 4 catalog/updates remains BLOCKED.


## Phase 4 independently pinned catalog — PR #13
- New Python/SQLite workflow PASSED: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43610420031.
- Android build/unit/lint: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43610420071 (verify final branch head before acceptance).
- Android API35 emulator including catalog verification: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43610420074 (verify final branch head before acceptance).
- No new real data, public release catalog, paid endpoint or speed/sign-coordinate DB in the app.


## PR #13 verified final head and APK archive (2026-11-14)
- Final PR code head `468c49ae565225f7264d492360af665c639f5097`, merged as main `068c297e1df55466ba0adc50b05755192814087b`.
- Python/SQLite `SUCCESS`: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43611161271.
- Android :app:assembleDebug/:app:testDebugUnitTest/:app:lintDebug + built APK audit `SUCCESS`: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43611161247.
- Emulator API35 `SUCCESS`: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43611161298.
- APK audit artifact `phase4-apk-road-asset-audit` ID 14119833707, ZIP SHA256 2a6d4352bef006261b11a47c6d19c1fc41d0afc334f733ab77fb90d7ed2303bb; inspected nested MANIFEST.json and verified hashes of 13 archived entries.
- APK asset paths and bytes: `assets/map_styles/offline_empty.json` 238, `assets/map_styles/osm_streets_experimental.json` 416, `assets/map_styles/pmtiles_synthetic.json` 698, `assets/pmtiles/synthetic_manifest.json` 525, `assets/pmtiles/synthetic_test.pmtiles` 462. NO true speed/sign DB, NO real province maps.
- Debug APK artifact ID 14120452033. Signed release build and actual taxi-driver field trials remain NOT DONE.


## PR #15 — independent Road Intelligence approval and candidate inspection
- Working branch `phase-4/road-intelligence-approval-gate`, PR https://github.com/ThanhTaxiXanh/NaviTaxi/pull/15.
- Checks required: Phase 0 Python/SQLite candidate data integrity + artifact report; Android assembleDebug/JUnit/lint + APK asset scan; API35 emulator test that unapproved synthetic speed/sign rows produce zero overlays.
- GitHub PR CI is the build source of truth; no local Android SDK/device road test is claimed.
- No new real road DB asset or observed physical sign coordinates. The old synthetic PMTiles 462-byte fixture remains the only offline tile content.


## Accepted PR #15, final-head CI and Road Intelligence artifact
- Commit `26d75df6c0751df89a060d0efc1e209ff65b5078`, merged main `dd53c1a43991f350ffa980091e4db1faabeddccf`.
- Phase 0 Python SQLite/source/coordinate/RTree audit: SUCCESS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43614134722.
- Android :app:assembleDebug :app:testDebugUnitTest :app:lintDebug and APK inventory: SUCCESS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43614134733.
- Android API35 instrumented smoke, unapproved SQLite signs/speed overlay refusal: SUCCESS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43614134877.
- Phase0 evidence artifact ID 14121745051 ZIP sha256 879a17910a724fbebedc6a637f9475badde2a38417b2e989b40450092958d3de; empty DB bytes 86,016, DB SHA256 87193a1b8af8fa2e17c56a2bb9f03c533378321335653590fefae2c8a91de584; `EMPTY_DATABASE`, 0 verified records.
- APK road-asset audit from Android workflow: five synthetic assets, archive hashes verified. Production release and physical taxi driving tests remain NOT DONE.


## PR #17 OSM reference-only source pipeline — code-head evidence
- Phase 0 / Python 3.12 / pyosmium 4.3.2 / SQLite: SUCCESS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43617224402; 36/36 unit tests including actual PBF conversion-and-reader, source tampering, sign-node vs way/relations, raw mph/conditional semantics and archive SHA256.
- Android assembleDebug/testDebugUnitTest/lintDebug and built-APK audit: SUCCESS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43617224403. No new Android source or runtime dependency.
- Source test reference artifact ID 14121689381 (GitHub artifact ZIP SHA256 8b6c4304cc55fefec8ef9af5222445d47b084630147e9fa6c4bca35f8618c2fb); contains original synthetic source hash, 1 speed way/2 sign nodes/1 sign way/1 sign relation; all false verification/alert flags.
- APK audit artifact 14122562328 (ZIP SHA256 ff2248af20f94a94946828f013e8b9aa8999926d0a9be62214938c97487a824d). Exact 5 APK assets: assets/map_styles/offline_empty.json (238 B); osm_streets_experimental.json (416 B); pmtiles_synthetic.json (698 B); assets/pmtiles/synthetic_manifest.json (525 B); synthetic_test.pmtiles (462 B). SHA256SUMS verified, no real speed/sign DB.
- PR #17 final head Python 43617538573 and Android 43617538560 PASSED, merged to main as 8b6d1f7ae9f995948364bdffcabf0208283a6c3d. This is only a verified test-data reference pipeline, NOT real legal speed/sign coverage.


## Real Vietnam Geofabrik PBF source CI evidence — PR #19 merged
- PR #19 https://github.com/ThanhTaxiXanh/NaviTaxi/pull/19 MERGED main 8e9ad423100234b022506667b269f25d0a3df556. Post-merge Android build PASS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43624954395.
- Source-backed real Vietnam PBF workflow PASS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43624034669: full 332,558,874 B source, SHA256 ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed, MD5 1f7716ad049551852fc281e969a000aa. Actual PBF pyosmium parsing PASS.
- Source audit measured: 44,472 maxspeed-tagged highway ways, 810 tagged sign nodes, 1 tagged sign way, 0 tagged sign relations. All unverified.
- Python provenance/source tests PASS 43624034554, Android assembly/unit/lint and forensic APK audit PASS 43624034656.
- Actual source audit artifact ID 14124844201, outer ZIP sha256:42352c12807767bfbe7ae4af26a060ad156443e2b05411496f7b0c63d47a5370; nested reference archive SHA256 23bfbef5e6fdc63a2a5e268a04fafeaee837f6c83c1fa5a3b21894bf47094380; all 3 SHA256SUMS entries verified.
- APK forensic audit artifact ID 14125266676, archive sha256:a7813b05f51d502d003ac64872c75cd819d661eb73af48d687dd6528d76f0833; 5 synthetic assets exactly, and 0 approved real signs/speeds.
- Supplemental reference-only QA script/tests CI pending; no taxi field test or production legal sign/speed alerts claimed.


## PR #20 OSM reference QA acceptance — verified, 2026-11-15
- PR #20 merged as `68b8f3ba8cea94e982397e9797d8da3b9f348a35`.
- Final code head `f0a64e5fb8b3de097e8aea5231f0ca05882ff4e4`: Python/SQLite and source-integrity quality tests **51/51 PASS**, https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43625497790.
- Android assembleDebug/JUnit/lint plus APK road-asset audit PASS, https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43625497719.
- PR #19: real PBF source workflow 43624034669 SUCCESS, source SHA256 ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed. Full 333MB source NOT in app. 0 actual signed-off legal speeds/physical sign surveys.


## PR #22 Road Intelligence review-only field and legal queues
- Branch `phase-4/field-survey-review-queues`; PR https://github.com/ThanhTaxiXanh/NaviTaxi/pull/22.
- Code-head Python/SQLite with new negative tests PASS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43659839106. Phase0 artifact `phase0-road-data-evidence` ID 14140060222 (GitHub ZIP digest sha256:0bcdf9f7ebb316142cd7c2380fe8ab008f841c18e31aefcfc44e8d8f7283bfed) includes synthetic test-only CSV queue and SHA256SUMS ZIP.
- Android compile/unit/lint and APK road audit PASS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43659839088. No app Kotlin source/production DB changes.
- Real externally inspected reference worklist generated in this session: `NaviTaxi_Vietnam_2026-11-12_Field_Sign_Speed_Review_UNVERIFIED.zip` 1,170,686 B sha256:26891bd61d10cb6228f30db5201af275254832b0705a5c553731df7f24c7df7c; 44,472 speed review CSV rows and 811 sign candidate CSV rows; all reviewer evidence BLANK and approvals FALSE.
- Final PR #22 head 17acfac4e3c5c035abe2748b02351f2bf038ec1b: Python/SQLite 60/60 PASS 43660068830, Android compile/JUnit/lint/APK 43660068771 PASS. MERGED main 39cf3185ee91239c21ec0f6d57246e79ed006bf6. Phase 4 overall not production complete, Phase 5 not started.


## Phase 11 field/legal evidence intake branch — 2026-11-15
- Base main SHA e2a1fdd6b25233a42b91ab4d58cbbd5b485058a0 and successful Android push run 43660382929.
- Branch phase-11/field-evidence-intake-gate adds standard-library Python audit and synthetic regression tests. No Kotlin/Android APK data or dependency change.
- Code-head 32a2d7d2: new full Python suite **78/78 PASS** https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43661967753 ; Android assembleDebug/unit/lint and APK road asset scan PASS https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43661967823 . Final documentation-head CI still requires recheck.
- Real legally verified speed segment count: 0; physically field-surveyed approved sign count: 0; original review ZIP remains external.


## PR #25 Phase 11 review conflict quarantine (2026-11-15)
- Base main SHA 5c950d31147b672bc025ecbaf9b1c6b5222e7032, verified Android push CI 43662265877 SUCCESS.
- This branch changes Python evidence intake and synthetic-only tests, no Kotlin/APK runtime data or new dependencies. Code-head Python/SQLite 86/86 PASS at run 43664352656; Android assembleDebug/unit/lint and APK scan PASS at run 43664352607. Final documentation-head CI and post-merge main still require confirmation.
- No real law-approved speed record, physical sign coordinate or production road DB; Android approved SHA pin list remains EMPTY.
