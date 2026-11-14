# Data sources and evidence policy

| Domain | Current state | Planned lawful source | Validation |
| --- | --- | --- | --- |
| Road network | NOT INGESTED | OpenStreetMap extracts (ODbL) | source snapshots, attribution, geometry |
| Speed limits | NO VERIFIED RECORDS | OpenStreetMap `maxspeed` tags supplemented by independently licensed legal/sign surveys | value type/unit, source URL, direction, last verified |
| Traffic signs | NO VERIFIED RECORDS | OpenStreetMap `traffic_sign` or licensed survey GeoJSON | physical WGS84 lat/lon, sign code, direction, source and timestamp |
| Offline vector map | NOT INGESTED | licensed OSM data -> PMTiles | checksum, metadata, renderer proof |
| Local legal defaults | NOT INGESTED | official Vietnamese traffic law, date-specific applicability | legal citation and vehicle/road class; never infer site-specific signage |
| Province catalog | NOT INGESTED | official 34 provinces effective 2025-07-01 | boundaries and metadata source |
| Live traffic | NOT INGESTED | lawful provider under acceptable terms | staleness and consent |

A data source's URL and license must be recorded before its content can be shipped. OSM tags may be incomplete or outdated, so `maxspeed` cannot be silently promoted to authoritative law. A posted sign location is **not** the same as a road line centroid. No real coordinates or limits are asserted in this phase.


## Phase 2 map tile status
- MapLibre demonstration vector-country style: https://demotiles.maplibre.org/style.json. Pure demonstration, no real street-level navigation guarantee, not a 50-driver backend.
- Explicit manual OSM streets: https://tile.openstreetmap.org/{z}/{x}/{y}.png; proper user agent/visible OSM attribution, interactive viewport only. Policy: https://operations.osmfoundation.org/policies/tiles/; bulk/offline downloading forbidden.
- No imported OSM GeoJSON, extracts, PMTiles, speed limits or sign coordinates. The database remains empty/not bundled.
- Offline-safe future provider: licensed OSM extract processed to own PMTiles under Phase 3.


## Phase 3 synthetic PMTiles source
- Internal test-only origin: scripts/build_synthetic_pmtiles.py in this repository (self-created schematic, no OSM extract, no public tile-server data).
- Canonical asset: app/src/main/assets/pmtiles/synthetic_test.pmtiles (462 bytes, SHA-256 d9a53b380463498cc31fd59a30d00e07a2f3f32f9f894eefa7b796d20470de9c).
- Manifest: app/src/main/assets/pmtiles/synthetic_manifest.json; all is_real_map, has_verified_speed_limits and has_verified_signs flags FALSE.
- MVT vector layer "demo_grid" with 2 artificial cross lines at global z0, NO road names, geographic routes, speed limits or traffic sign coordinates.
- Native PMTiles remote HTTP range protocol can target lawful, operator-hosted HTTPS URLs in future, but NO external paid provider, endpoint or package has been configured.
- Real offline 34-province licensed OSM extracts and verified local speed/sign datasets remain BLOCKED/NOT INGESTED.
