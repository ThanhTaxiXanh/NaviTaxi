# NaviTaxi Architecture / Phase 0

## Android layers (planned for Phase 1 onward)
- \`app\` — Kotlin Android application (\`vn.navitaxi\`), search/offline/settings/drive UI.
- \`core:domain\` — transport-independent road restrictions, road signs, data provenance, GPS and route models.
- \`core:data\` — local SQLite, storage metadata, geo indexes and verified import adapters.
- \`feature:road-intelligence\` — speed lookup, location-aware sign proximity, stale/missing-data status.
- \`feature:search\` — address/place/POI search and driver shortcuts.
- \`feature:offline\` — region package lifecycle and checksums.
- \`feature:settings\` — explicit local settings for GPS, alerts and map display.
- \`feature:map\` — MapLibre and PMTiles reading *only when device-tested*.
- \`feature:navigation\` — routing and taximeter, subject to validation.

These are bounded contexts, not a false claim that all modules already exist.

## Road intelligence data contract
Canonical speed and traffic sign assets have **mandatory provenance**:
\`data_source -> road_segments / traffic_signs\`. Speeds are integers in km/h, never inferred from the type of road as if legally verified. Signs have WGS84 latitude/longitude, direction if known, sign code and evidence source. A missing speed or traffic-sign observation must display \`Không có dữ liệu\` rather than a fabricated warning.

GeoJSON and JSON ingest must validate CRS (WGS84), geometry, plausible coordinates, duplicates, source attribution, copyright/license, and update age. Matching sign positions and segment limits to a GPS location requires direction of travel, data confidence and map-matching uncertainty checks. Do not use false precise matches.

## Storage and offline data
A future Android asset can be generated at:
\`app/src/main/assets/road_intelligence/road_intelligence.db\`.
The present canonical schema is:
\`data/road_intelligence/schema.sql\`.
The DB's RTree indices support sign-radius and road-bbox queries. The DB is seeded EMPTY until a licensed, identified dataset is provided. Use SQLite transactions and immutable versioned packages with SHA-256 checksums.

Never bundle private location traces. Never claim dynamic live traffic without a permitted working source.

## Maps/routing
MapLibre Native Android + OpenStreetMap for display; PMTiles as official vector-tile package. PMTiles Android range reader requires a real instrumented test before marking complete. Offline route graph must match package version and cross provincial boundaries; Valhalla evaluated before OSRM. The 34-province catalog must use the legal administrative boundaries effective 2025-07-01 and be independently verified, not invented.

## UI from reference images
1. Search: NaviTaxiMap header, voice/search, Address/Place/POI, category shortcuts, recents, driver suggestions, results and preview.
2. Offline: storage, region/whole-country toggle, province search/suggestions, progress and pause/resume/cancel, updates, Wi-Fi/cellular switches.
3. Settings: light/dark, voice volume/profile, map style/3D/traffic, GPS modes, speed alert/lane guidance, POI density.
The iPhone screenshots are **visual references** only; Android system navigation and aspect ratio will differ. Interactive actions must be connected to real state; never use mock downloads labeled real.

## Git/CI
Each phase uses \`phase-N/<topic>\`, opens a PR against \`main\`, and merges after evidence. Phase 0 Python sqlite/unittest checks run in GitHub Actions. Later phases need Android build + instrumented tests and evidence before accepting APK claims.

## Legal & privacy
OSM is ODbL: display attribution and ensure compatible redistribution obligations for derivative databases. No user's precise location may be transmitted to outside services without explicit consent.
