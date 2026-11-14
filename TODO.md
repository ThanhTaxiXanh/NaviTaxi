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
