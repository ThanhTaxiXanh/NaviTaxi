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


## Phase 11 — private field-evidence ZIP
- Python standard-library-only pack+verify; no paid APIs, new Android
  dependencies, third-party imagery or road map data imported by this PR.
- Existing Geofabrik/OSM reference rows are © OpenStreetMap contributors,
  ODbL 1.0. The unverified source ZIP must retain source attribution and
  derived database reuse obligations.
- Actual field photos may contain faces, number plates or sensitive survey
  locations and may be copyright-protected. Keep bundles private, require
  legal author permission, independent provenance, explicit retention and
  controlled access; SHA256 and a supplied license string cannot grant rights.
  Neither GitHub CI nor the Android APK receives real photos or legal speeds.


## PR #27 private physical-sign photo minimization
- No new external code/data licenses or paid APIs. Python standard library
  alone; no new Android dependencies, third-party map layers or telemetry.
- Portable bundles cannot contain photographs not cited by a source field
  sign observation, cannot be written into the repository and must remain
  restricted private evidence. Still independently verify photographer
  rights, personal-data consent and ODbL reuse requirements before any
  release or transmission. SHA256 does not grant redistribution rights.


## PR #28 — optional physically surveyed GPX evidence
- New Python uses standard library `xml.etree.ElementTree` and existing
  SHA256/ZIP modules only, no billed API or new Android runtime dependency.
- A submitted GPX trace can reveal a collector's precise travelled
  coordinates and timestamps. Keep it as confidential field evidence,
  restrict access and redistribution, and document true creator rights,
  provenance and retention. A source URL or user-entered `license`
  string is not independent proof of legal permission.
- OSM/Geofabrik raw tagging and review queues remain © OpenStreetMap
  contributors ODbL-1.0. No GPS traces, photographs, source PBF, real
  speed/kmh entries or observed sign positions are checked into Git/Android.


## PR #29 case-scoped speed review — data and code rights
- Python standard library only; no new paid services, SDK libraries or
  Android APK dependencies. Review `case_id` is metadata, not speed law.
- Existing OpenStreetMap source and derivative worklists remain ODbL 1.0,
  © OpenStreetMap contributors; no source map attribution is removed.
- Actual GNSS routes and sign photographs may contain private locations,
  individuals or plates. Independent photographer consent, GPS ownership,
  field accuracy and governing legal texts still require human checking
  before any sharing, archiving or production authorization.


## 2026-11-15 — candidate SQLite/RTree QA scope
- Changes use only Python and SQLite standard-library mechanisms, with no new SDKs, commercial dependencies, third-party sign photographs, GPS surveys or external data distributions.
- Synthetic spatial checks carry no real-world road-sign or legal-speed claims. Original Geofabrik/OSM reference and derivative worklists remain ODbL-1.0 © OpenStreetMap contributors; real surveys, imagery and legal-source redistribution remain subject to independent review.


## 2026-11-15 — GPX quality parsing and field-source rights

- GPX 1.1 schema documentation is referenced for validation, not bundled as redistributable map data. Code uses the Python standard library, no paid API, new dependency or external service.
- Synthetic GNSS tests use invented coordinates/timestamps. No original GPX, sign photo, GPS data, legal ruling or external survey media is stored in Git or APK.
- Actual field GPS/photo rights, personal information, permissions and independent legal reviews remain prerequisites before any release approval. Raw OSM reference remains ODbL-1.0 © OpenStreetMap contributors.
