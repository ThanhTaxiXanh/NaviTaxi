# Licenses

NaviTaxi application code: license decision pending owner choice; until then do not assume a commercial-permissive grant.

Technology intended for evaluation (confirm exact version and distribution terms before integrating):
- Android SDK / AndroidX: license and redistribution terms to audit at dependency pin.
- MapLibre Native: open source, verify version and transitive notices at integration.
- OpenStreetMap geodata: ODbL 1.0, attribution and share-alike requirements may apply to derived databases.
- PMTiles: format specification; library licenses checked per implementation.
- SQLite: public-domain distribution, verify bundled variant.

No map tiles may be scraped from publicly hosted tile servers as a free bulk-download substitute. No commercial paid service or billing without express consent.


## Verified Phase 2 dependency / attribution notes
- org.maplibre.gl:android-sdk-opengl:13.7.1 — BSD-2-Clause; Maven Central source and notices: https://central.sonatype.com/artifact/org.maplibre.gl/android-sdk-opengl
- OpenStreetMap contributors map data — ODbL 1.0; visible attribution and derivative database obligations: https://www.openstreetmap.org/copyright
- OSMF raster tile infrastructure is NOT freely redistributable for bulk offline use: https://operations.osmfoundation.org/policies/tiles/
- Demo vector style (country boundaries) from MapLibre demotiles / Natural Earth; demonstration not licensed to imply street-grade coverage: https://github.com/maplibre/demotiles
- Exact transitive dependency licenses and notices still require final release audit; do not claim audited production license bundle.


## Phase 3 fixture and protocol
- Bundled 462-byte synthetic PMTiles/MVT grid was generated from code owned by NaviTaxi project and contains no third-party OSM map tiles; not licensed as a real road basemap.
- PMTiles v3 format is documented by Protomaps: https://github.com/protomaps/PMTiles/blob/main/spec/v3/spec.md.
- MapLibre Native PMTiles file:/// support: https://maplibre.org/maplibre-native/android/examples/data/PMTiles/.
- No OSMF tile-server contents were downloaded for offline packaging; no live cost or billing activated.


## WorkManager Phase 4
- androidx.work:work-runtime-ktx:2.12.0, Apache License 2.0 (official AndroidX stable release 2026-09-23): https://developer.android.com/jetpack/androidx/releases/work.
- androidx.work:work-testing:2.12.0 is limited to Android instrumented tests. Existing OkHttp transitive/runtime license unchanged.
- No third-party map tiles or paid map APIs have been activated in this work.
