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


## Phase 4 reviewed release catalog (not production-enabled)
`docs/PHASE_4_CATALOG_CONTRACT.md` defines an exact-byte SHA-256 pinned PMTiles catalog, strict source/license metadata and monotonic update/rollback decisions. Android remote scheduling now requires an approved `TrustedOfflineCatalog`. No approved production pin or catalog is configured, no automatic updates or 34-province downloads are available, and the app still has **zero verified physical traffic signs or road speed limits**.


### Latest accepted Phase 4 code
PR #13 (https://github.com/ThanhTaxiXanh/NaviTaxi/pull/13) is merged as main `068c297e`. Python/SQLite, Android build/unit/lint and API35 emulator all passed on final code head. Android CI now uploads a verifiable built-APK road asset inventory plus ZIP: there are five synthetic-only map assets, with **zero** verified legal speed records or roadside sign positions. Phase 4 is not fully complete, real downloads remain disabled, and Phase 5 has not started.


## Road Intelligence source approval (Phase 4 security prerequisite)
The map no longer accepts speed limits or physical sign positions merely because a local SQLite file contains source/license strings. `RoadDatabaseApprovalGate` requires independently pinned, code-reviewed SHA-256 bytes and separate approval for each domain. Its production pin list is deliberately EMPTY: **zero legal speed observations and zero surveyed traffic-sign coordinates are present**. Candidate SQLite inspection (not approval) is described in `docs/ROAD_INTELLIGENCE_APPROVAL_GATE.md`. See PR #15 and CI; Phase 4 remains blocked on authentic geodata and field proof.


### Road Intelligence verification evidence (PR #15)
Independent SQLite speed-limit and physical sign coordinate approval gate was merged as `dd53c1a`. Python/SQLite, Android build/unit/lint and API35 emulator all passed on the final PR code. The generated canonical DB and APK inventory both contain **zero source-verified speed limits and zero surveyed traffic signs**; the release allowlist is intentionally empty. This is a verified safety foundation, NOT functional speed-limit alerts.


### Phase 4 OSM road reference-only importer (PR #17)
A Python script can stream locally supplied, SHA-256-pinned .osm or .osm.pbf files, retain original OSM maxspeed and traffic_sign tags, and produce JSONL/manifest/SHA256SUMS ZIP under build/. Android never treats this as approved legal speeds or physical signs. The current CI artifact is a SYNTHETIC test only; no actual Vietnam extract, real legal limit, sign survey or 34-province map is included. See docs/ROAD_INTELLIGENCE_OSM_REFERENCE.md.

- Reference-only OSM/PBF ingestion pipeline PR #17 merged to main `8b6d1f7`; Python 36/36 PASS (including actual binary PBF test), Android build/unit/lint PASS. **No legally verified real road speeds or physical roadside sign positions** have been imported; see `docs/ROAD_INTELLIGENCE_OSM_REFERENCE.md`.


### Actual Vietnam OSM speed/sign reference audit (Phase 4)
PR #19 acquired and SHA256-verified a real, fixed-date Geofabrik Vietnam OSM snapshot (2026-11-12, 332,558,874 B). It measured **44,472** speed-tagged OSM road ways, **810** sign-tagged OSM nodes and **1** sign-tagged way, all reference-only. See `docs/VIETNAM_OSM_SPEED_SIGN_AUDIT_2026_11_12.md` for exact source hash, downloaded artifact, origin, raw-tag distributions, sign coordinates and limitations. **ZERO** independently validated legal speed records or field-surveyed physical sign positions are enabled in the APK.

- Real source QA script `scripts/audit_osm_reference_quality.py` has been merged in PR #20; 51/51 Python tests and Android CI PASS. OSM candidate counts are transparent evidence only; legal-speed and field-survey approval remain blocked.


### Road sign field-survey and legal speed review worklists (Phase 4)
The project now has a source-hash-gated review-queue generator for independently audited Vietnam OSM data. From 44,472 speed-tagged OSM ways and 811 sign-tagged objects, it produces separate CSVs with original source identifiers, optional **UNVERIFIED** node coordinates and blank fields for genuine field survey and current legal analysis. Source: ODbL-1.0 © OpenStreetMap contributors. All approval/alert statuses FALSE; no Android DB or speed warning is enabled. See `docs/ROAD_INTELLIGENCE_FIELD_REVIEW_WORKLISTS.md` and PR #22.
