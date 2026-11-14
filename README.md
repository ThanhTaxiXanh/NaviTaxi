# NaviTaxi

NaviTaxi is an Android-first, zero-mandatory-cost navigation project for taxi drivers in Viet Nam.

## Development status
- **Phase 0**: architecture, data provenance, road intelligence schema, asset audit, tests and CI.
- **Phase 1–18**: tracked in [TODO.md](TODO.md) and [PROJECT_STATE.md](PROJECT_STATE.md).
- Android application id: `vn.navitaxi`; planned release artifact: `NaviTaxi.apk`.

## Priorities
1. Accurate, source-attributed **speed limits and traffic sign coordinates**; unknown values remain unknown.
2. Kotlin Android, MapLibre + OpenStreetMap, offline PMTiles and local SQLite.
3. A faithful implementation of the three supplied reference screens: search, offline maps and settings.
4. No Google Maps, Mapbox paid endpoints, pay-per-use services, or unapproved location-data transmission.

## Road Intelligence (Phase 0 foundation)
```bash
python3 scripts/initialize_road_db.py --output build/road_intelligence.db
python3 -m unittest discover -s tests -v
python3 scripts/audit_road_assets.py --root . --out build/road-assets-report.json
python3 scripts/package_road_data.py --root . --output build/road-intelligence-archive.zip
```

Generated databases are **empty by design** until licensed, verifiable source datasets are imported. A blank database is not a claim that a road's speed limit has been mapped. A speed alert must never invent a legal limit.

Git workflow: one branch per phase, CI, PR targeting `main`, merge only after phase acceptance criteria have passed. See [ARCHITECTURE.md](ARCHITECTURE.md), [DATA_SOURCES.md](DATA_SOURCES.md), [LICENSES.md](LICENSES.md).

The original design references are user supplied PNG/JPEG images; they are not production maps, measurements, or legal speed-limit data.


## MapLibre / Android development (Phase 2)
The development branch adds a real MapLibre Native MapView, interactive controls and search-to-map navigation. This is still an experimental basemap, not a safe taxi navigation product. The OSM raster street view requires manual confirmation and cannot be used for bulk offline downloads.

Android debug CI: GitHub Actions, using Gradle 8.9, Kotlin 2.2.10 and MapLibre 13.7.1 OpenGL ES. Actual Android emulator MapView startup test is tracked separately. No live speed limits, traffic sign coordinates, routing, turn-by-turn navigation or PMTiles package has been shipped.

See docs/PHASE_2_ACCEPTANCE.md and docs/ROAD_INTELLIGENCE_MAP_CONTRACT.md.


## PMTiles native offline test (Phase 3)
- In the map tab select **PMTiles thử nghiệm**. The app verifies SHA-256 of a synthetic PMTiles v3 archive, copies it into private storage, then opens it via native MapLibre pmtiles://file://.
- The fixture has one MVT z0 tile with two schematic cross lines. It is deliberately NOT a real map and cannot be used for routing or speed/sign alerts.
- Rebuild and validate test data:
  python3 scripts/build_synthetic_pmtiles.py
  python3 scripts/validate_pmtiles.py
  python3 -m unittest discover -s tests -v
- Validate a lawful, self-hosted PMTiles server's HTTP Range support with:
  python3 scripts/pmtiles_range_probe.py https://your-operated-host/example.pmtiles
- To inspect and ZIP discovered source assets:
  python3 scripts/audit_road_assets.py --root . --out build/road-assets-report.json
  python3 scripts/package_road_data.py --root . --output build/road-intelligence-archive.zip
- Phase 4 will add package management; Phase 5 will add lawful province data. No real speed-limit/traffic-sign dataset is included.


## Phase 4 – Offline Package Manager core
- Offline tab now installs/revalidates/deletes only the bundled 462-byte synthetic PMTiles test tile, displaying its true local state.
- Transport accepts a vetted HTTPS .pmtiles specification with license/source/size/SHA256, supports resumable Range/ETag, pause/resume/cancel and atomic versioned installs. Tested using loopback-only MockWebServer. Production download URLs are NOT configured.
- Province/full-Vietnam download controls remain unavailable until licensed map packages and their manifests exist. No geographic road data or speed/sign coordinates have been imported.
- WorkManager/background resume and scheduled update metadata are still pending, so Phase 4 core is verified but the full offline product is BLOCKED.


### Phase 4 WorkManager background jobs
A WorkManager 2.12.0 CoroutineWorker now schedules future approved HTTPS PMTiles package downloads with network constraints, durable job IDs, progress restoration and foreground dataSync notification. The installer continues to require full SHA256, PMTiles v3 header and immutable version activation. No approved real map catalog exists, so the offline page still only installs/deletes a synthetic test grid. No legal speed data or surveyed sign coordinates are bundled.
