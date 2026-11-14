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
