# Phase 4 – WorkManager durable PMTiles downloads

## Source mandate
Master Prompt section IV recommends WorkManager; section IX requires offline archive metadata/checksums/versions and download pause/resume/cancel/update/delete. Phase 4 core was already merged; this branch addresses durable scheduling independently of missing province data.

## Source code and policy
- app/src/main/java/vn/navitaxi/OfflineDownloadWorker.kt: CoroutineWorker + 2.12.0 API, foreground dataSync notification and progress.
- app/src/main/java/vn/navitaxi/OfflineWorkScheduler.kt: one unique work, persisted non-secret validated manifest and UUID, WorkManager network constraints; pause/resume/cancel.
- app/src/main/java/vn/navitaxi/OfflinePackageManager.kt: StateFlow tracks OS work progress and resumes watching after app restarts; existing demo install/delete maintained.
- app/src/main/java/vn/navitaxi/OfflinePackageTransfer.kt: HTTPS Range and strong ETag/If-Range, max size and storage headroom, WGS84-neutral manifest, full SHA256 and PMTiles v3 header validation, immutable old versions.
- app/src/main/AndroidManifest.xml: foreground service permission, FOREGROUND_SERVICE_DATA_SYNC and WorkManager SystemForegroundService dataSync type.
- No location permission, no GPS uploads, no paid Mapbox/Google API, no OSMF tile server offline bulk download.

## CI gates
- Python/SQLite/RTree/PMTiles provenance checks.
- Android assembleDebug, testDebugUnitTest including WorkManager Data input, lintDebug.
- Android API35 emulator MapLibre and offline UI synthetic install/delete as well as invalid WorkManager worker test.
- Inspect exact APK asset paths/bytes/sha256 for no real road/sign/speed database. Do not claim a real map based on synthetic MVT fixture.
- Merge only after all gates on the final head pass.

## Production limitations
- WorkManager is persistently scheduled but not guaranteed to run under user force-stop or all OEM battery and Android15 dataSync quotas. Emulator tests cannot establish 50 taxi drivers production reliability.
- No legal, signed-off 34-province downloadable PMTiles catalog exists, so no real remote transfers, recurring version checks or automatic updates are enabled.
- Road Intelligence table schema exists under data/road_intelligence/schema.sql but the APK has no source-backed road segments or physical sign coordinates.
- Verified speed km/h and roadside sign locations must be ingested from approved sources separately; do not manufacture them.

## Deep asset scan and ZIP
From repository root:
    python3 scripts/audit_road_assets.py --root . --out build/road-assets-report.json
    python3 scripts/audit_road_assets.py --root . --apk /path/to/source.apk --out build/apk-audit.json
    python3 scripts/package_road_data.py --root . --output build/road-asset-archive.zip

Source confidence must be assessed separately from the mere filename, and no APK path is invented when an input APK is unavailable.

## Official references
- WorkManager 2.12.0 release: https://developer.android.com/jetpack/androidx/releases/work
- Long-running foreground work: https://developer.android.com/develop/background-work/background-tasks/persistent/how-to/long-running
- WorkManager work state API: https://developer.android.com/reference/kotlin/androidx/work/WorkManager

## Verified acceptance evidence (2026-11-14)
- SQLite, PMTiles and source provenance: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43606534452 – PASS.
- Android assembleDebug/testDebugUnitTest/lintDebug: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43606534434 – PASS.
- Android Emulator API35: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43606534445 – 4/4 PASS, including invalid-manifest worker refusal without network.
- Code PR https://github.com/ThanhTaxiXanh/NaviTaxi/pull/9 merged to main e1fc7dc423bc96e02c6b44360e5c3a9729c7cfa1.
- Extracted debug APK bytes 60,285,140; SHA256 2f3492851a2596b20c64e2dea0910e8c4428bd863d143b8aac12bc132b2cd5ca.
- APK internal: assets/map_styles/offline_empty.json 238 B; assets/map_styles/osm_streets_experimental.json 416 B; assets/map_styles/pmtiles_synthetic.json 698 B; assets/pmtiles/synthetic_manifest.json 525 B; assets/pmtiles/synthetic_test.pmtiles 462 B (SHA256 d9a53b380463498cc31fd59a30d00e07a2f3f32f9f894eefa7b796d20470de9c).
- No authentic speed_kmh records, roadside sign coordinates or road intelligence SQLite/Realm file in the APK. Real 34-province navigation and automatic update catalog still BLOCKED; this is an API-level infrastructure acceptance, not field acceptance.


## Strict transport consent hardening
- Important distinction: WorkManager UNMETERED is a scheduling constraint, not a guarantee of Wi-Fi. Some cellular networks can be reported as non-metered.
- Persist the explicit allow_cellular boolean inside the durable WorkManager Data (false by default). Check actual ConnectivityManager NetworkCapabilities at worker execution: Wi-Fi or Ethernet always allowed, cellular only when the user enabled it. No Internet-capable transport => retry; do not consume mobile data.
- OfflineConnectionPolicy unit tests cover Wi-Fi, Ethernet, blocked cellular, explicitly allowed cellular and disconnected network. Regression must pass before merge.
