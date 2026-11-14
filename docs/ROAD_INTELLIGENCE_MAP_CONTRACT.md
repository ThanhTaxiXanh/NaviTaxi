# Road Intelligence speed/traffic sign coordinate contract

## Exact paths
- Canonical schema: data/road_intelligence/schema.sql
- Prospective verified APK asset (NOT PRESENT): app/src/main/assets/road_intelligence/road_intelligence.db
- Runtime read-only DB (NOT PRESENT): <application-internal-files>/road_intelligence/road_intelligence.db
- Reader: app/src/main/java/vn/navitaxi/RoadIntelligenceRepository.kt
- Display: app/src/main/java/vn/navitaxi/MapScreen.kt

## SQLite tables
- data_sources(source_id, provider, source_uri, license, acquired_at, checksum_sha256, dataset_version)
- road_segments(segment_pk, segment_id, osm_way_id, direction, vehicle_class, speed_kmh, geometry_geojson, min_lon, max_lon, min_lat, max_lat, source_id, observed_at, verified_at)
- traffic_signs(sign_pk, sign_id, sign_code, latitude, longitude, bearing_degrees, direction, related_segment_id, source_id, observed_at, verified_at)
- road_segments_rtree and traffic_signs_rtree are spatial indexes.

Sign coordinates use WGS84 decimal degrees; map GeoJSON uses [longitude, latitude]. Data must have a license and verifiable provenance; unknown speed must remain unknown. Merely seeing a sign does not establish which lane or direction it controls.

## Reproduce asset search and ZIP archiving
Commands from the repository root:

    python3 scripts/audit_road_assets.py --root . --out build/road-assets-report.json
    python3 scripts/audit_road_assets.py --root . --apk /path/to/source.apk --out build/source-apk-audit.json
    python3 scripts/package_road_data.py --root . --apk /path/to/source.apk --output build/road-sign-speed-assets.zip

Use --apk only when an actual, lawfully inspectable APK is supplied. Report paths are relative to the APK root (e.g. assets/road/signs.sqlite). The ZIP bundles the original files, manifest, SHA256SUMS and canonical SQL schema. No real road/sign data currently exists in the NaviTaxi repository.

Future Phase 11: verify checksum/version/source license and coordinates, atomically import datasets, filter by viewport, map-match speed by direction, and only then enable verified-speed and sign warnings.


## Phase 4 source approval requirement, accepted PR #15
- Reader now refuses arbitrary app-private `road_intelligence.db` even if `data_sources` self-reports a source/license and timestamps. `RoadDatabaseApprovalGate` requires the SHA-256 of the exact immutable DB to match a separately code-reviewed pin and independently enabled speed/sign scope. Current pin list is empty.
- `scripts/review_road_candidate.py` produces a candidate-only JSON structure/count/WGS84/RTree/source check; it never approves legal limits or physical signs. See `docs/ROAD_INTELLIGENCE_APPROVAL_GATE.md`.
- API35 emulator PASS 43614134877 plus Python PASS 43614134722 / Android build PASS 43614134733. Production speed/sign records: 0 verified, no APK DB file and no GPS data transmitted.
