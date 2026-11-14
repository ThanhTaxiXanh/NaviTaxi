# Phase 2 MapLibre + OpenStreetMap acceptance

## Implemented scope
- MapLibre Native Android 13.7.1 OpenGL ES from Maven Central. BSD-2-Clause, version pinned for consistency.
- Fourth Android "Bản đồ" tab and Search-to-Map navigation.
- Compose AndroidView with MapView onCreate, onStart, onResume, onPause, onStop and onDestroy forwarding.
- Default MapLibre demonstration vector style (country-level example only).
- Explicit user-confirmed experimental street-level OSM raster tile mode.
- Empty offline map fallback does not falsely display invented roads.
- Read-only source-linked road segment and physical sign coordinates from optional verified local SQLite (none shipped).
- Android Internet and network-state permissions only; GPS location is not requested or sent.

## Tile policy and ethical limits
OSMF policy: https://operations.osmfoundation.org/policies/tiles/

- OSM standard raster tiles are available ONLY for interactive viewport experiments; not production/50 concurrent drivers.
- Do not bulk fetch, pre-download, prefetch cities or write tile download packages from OSM servers.
- User-Agent identifies NaviTaxi; cache behavior follows HTTP response and MapLibre defaults.
- Show OSM attribution visibly when displaying OSM roads.
- Demo country tiles: https://demotiles.maplibre.org/style.json are NOT street-level or production.
- Genuine offline PMTiles packaging and ownership is Phase 3.

## Tests and pending acceptance
- Python validation of both JSON map styles and Phase 0 SQL schema/archive.
- Android Gradle assembleDebug, testDebugUnitTest and lintDebug.
- Runtime Android emulator/device screenshot and no-crash test must confirm map actually renders, switch to empty-offline, leave/return, and map gestures.
- Android rendering must remain NOT VERIFIED until emulator/device evidence is collected.
- No legal speed limit or real traffic sign coordinates exist in Phase 2; tests must reject any claims otherwise.
