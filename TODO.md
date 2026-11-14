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
