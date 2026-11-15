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


## Phase 4 catalog verifier
- No new external Android/runtime dependencies or paid services were added. Android uses platform org.json, java.net.URI and SHA-256; Python uses the standard library.
- Independently pinning metadata does not settle redistribution rights of the underlying PMTiles. Each real release must retain OSM ODbL notices and independently documented source/license approval.
- Candidate Vietnam OSM extracts: https://download.geofabrik.de/asia/vietnam.html. NOT copied or redistributed in this change.


## Phase 4 Road Intelligence approval gate
- Added only standard Python libraries and Android/JDK SHA-256, SQLite and Kotlin code, no new paid or external dependencies.
- Geofabrik/OSM data reuse is a separate ODbL licensing and derivative database redistribution decision; source attribution and legal/field verification must be documented before production ingestion. No PBF or third-party sign dataset was downloaded or bundled by this change.


## Phase 4 OSM PBF reference adapter (PR #17)
- Python-only pyosmium/osmium 4.3.2 uses BSD-2-Clause (https://pypi.org/project/osmium/), downloaded as CI dependency on GitHub Actions; no library is bundled in Android release.
- OSM source tags belong to OpenStreetMap contributors and are distributed under ODbL 1.0 (https://www.openstreetmap.org/copyright), requiring attribution and appropriate database derivative notices before redistribution.
- The only test output uses NaviTaxi synthetic XML fixture; real Geofabrik Vietnam PBF not downloaded or repackaged. No paid APIs/servers/billing added.


## Verified 2026-11-12 Vietnam OSM source receipt
- Actual dated source acquired in GitHub CI #43624034669 under OpenStreetMap ODbL 1.0; © OpenStreetMap contributors. Fixed source SHA256 ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed and publisher MD5 1f7716ad049551852fc281e969a000aa.
- No 332MB PBF shipped in GitHub artifacts, Git repo, or Android app. Derived reference-tag ZIP in ephemeral artifact 14124844201 retains ODbL source metadata and attribution; downstream ODbL database share-alike obligations require separate review.
- Real speed/sign tag data remains NOT legally or field-verified and does not authorize alerts.


## OSM derived review packets / PR #22
- The field survey and speed legal-review CSV queues preserve OSM original contributor tag values, objects and source provenance and are derived from `vietnam-261112.osm.pbf` (ODbL 1.0, © OpenStreetMap contributors). Retain attribution and comply with ODbL database sharing/derivative conditions when distributing review archives.
- Python script and regression tests use only standard-library modules and existing audit script. No additional paid service, map tile host, proprietary dataset, API or phone GPS permissions are introduced.
- Law research URL links to the official Government Gazette and creates NO automatic reproduction or relicensing of legal text. Legal applicability requires separate review.


## Phase 11 field/legal evidence intake
- Validator uses Python standard library only: no new dependencies, remote billing or external service.
- Existing OSM review ZIP remains derived from OpenStreetMap contributors under ODbL 1.0; a newly collected photo requires its own lawful provenance/license before dissemination. Photo/source licensing strings in audit packets are NOT independent license approval.
- No new real survey photos or derived map data redistributed in this PR. Future release requires ODbL/photographic permissions and independent human approval.


## Phase 11 conflict-quarantine patch
- Python standard-library-only change, no external libraries, API payments, added OSM material or private field-photo data. ODbL 1.0 responsibilities for existing OSM-derived review queues remain unchanged.
- Matching evidence/photo SHA256 is a tamper-evidence check, not a copyright grant or physical-location proof. Independent image/geodata license permission and accurate legal interpretation remain prerequisites to release.
