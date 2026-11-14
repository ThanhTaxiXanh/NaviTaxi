# Phase 4 – Offline Manager core acceptance

## Implemented and verified
- Strict approved package specification: identity/version, expected bytes, full SHA-256, license/source and HTTPS PMTiles path.
- OkHttp binary stream handles initial HTTP 200/206, strong ETag with Range/If-Range, validated Content-Range/total, controlled stop and resume. On lost validator, discard partial and start from zero; no partial is activated as a map.
- Full PMTiles v3 structural header and SHA-256 must pass before renaming a versioned file. Existing installed versions remain intact during an update. Explicit cancel discards only its partial file; delete targets only the selected package.
- App-scoped StateFlow manager enforces Wi-Fi/ethernet or explicit mobile permission. No GPS permission or OSM standard tile mass downloads.
- Offline UI can install/verify/delete local synthetic package; real province download controls intentionally disabled without an approved catalog.
- Test-only dependency MockWebServer 4.12.0, Apache-2.0, https://central.sonatype.com/artifact/com.squareup.okhttp3/mockwebserver/4.12.0

## CI evidence
- Python SQLite/PMTiles tests: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43604517491 PASS.
- Android compile, unit tests with Range resume from byte 128, checksum rejection and update retention, lint: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43604517429 PASS.
- Android emulator API35 3/3 native map + offline page install/reverify/delete: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43604517455 PASS.
- Source PR https://github.com/ThanhTaxiXanh/NaviTaxi/pull/7 merged as 6fdbcfd.

## Not yet done
- No real road-map/province source catalog, PMTiles package manifests, POI/routing packages, sign coordinates or verified speed limits.
- No WorkManager/foreground/background job, notifications or periodic updates. Download only runs with the app process alive; partial data survives and can resume with same approved spec.
- NO claim of completed 34-province coverage, navigation, legally verified signs/speed warnings or full Phase 4 acceptance. Continue independent Phase 4 reliability work before moving to Phase 5.
