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


## 2026-11-14 candidate source evaluation (not ingested/approved)
- Geofabrik lists the Vietnam OpenStreetMap extract `vietnam-latest.osm.pbf`: https://download.geofabrik.de/asia/vietnam.html . It is a potential zero-fee source to process into first-party PMTiles with ODbL obligations; NO file was downloaded, checked, redistributed or approved in this PR.
- `maxspeed=*` ways are volunteered map tags, not a verified survey of current legal limits. `traffic_sign=*` may describe a way's affected section rather than a roadside physical coordinate; node tagging and direction evidence are needed. See https://wiki.openstreetmap.org/wiki/Key:maxspeed and https://wiki.openstreetmap.org/wiki/Key:traffic_sign.
- Real speed_kmh records: 0 verified; real sign WGS84 coordinates: 0 verified. Any proposed import must preserve source snapshot/hash/license, observation date, geometry and field verification separately.
- `scripts/validate_offline_catalog.py` and Android `OfflineCatalogVerifier` validate *package release metadata*, not traffic laws or physical sign locations. No production catalog pin exists.


## Phase 4 Road Intelligence candidate provenance (2026-11-14)
- Geofabrik https://download.geofabrik.de/asia/vietnam.html lists a Vietnam OSM PBF extract. Source candidate only; no raw bytes/checksum acquired, no geographic data, speed records or roadside sign coordinates imported in PR #15.
- OSM `maxspeed`, `maxspeed:forward`, `maxspeed:conditional` and `maxspeed:advisory` differ in direction, time and legal applicability. Unverified tags cannot become approved on-road speed warnings: https://wiki.openstreetmap.org/wiki/Speed_limits.
- OSM `traffic_sign` can be a node (potential real-world position) or a way (a section rather than a physical sign location): https://wiki.openstreetmap.org/wiki/Key:traffic_sign. No road centroid may be misrepresented as a sign coordinate.
- New candidate inspection command: `python3 scripts/review_road_candidate.py --db /path/to/candidate.sqlite --out build/road-candidate-report.json`. Even a structurally clean candidate keeps `driver_speed_alerts_allowed=false` and `physical_sign_alerts_allowed=false` until separate field/legal review and code-reviewed approval pin.
- Canonical source-backed table path remains `data/road_intelligence/schema.sql`; runtime DB `<filesDir>/road_intelligence/road_intelligence.db` is NOT PRESENT/APPROVED. Physical sign locations: 0 verified; site-specific legal speed observations: 0 verified.


## OSM source staging / PR #17 (2026-11-14)
- Geofabrik Vietnam PBF catalog: https://download.geofabrik.de/asia/vietnam.html ; intended locally supplied source URI: https://download.geofabrik.de/asia/vietnam-latest.osm.pbf . This is an external source candidate only; the file was NOT fetched or inspected in this PR.
- New scripts/extract_osm_road_reference.py requires exact source SHA256 and records original OSM node/way/relation ID, version, timestamp, raw maxspeed* / traffic_sign* values and source URI/ODbL attribution.
- Real source records imported: 0. Real physical sign locations field verified: 0. The only populated reference archive is an explicitly synthetic CI fixture with no legal/physical verification.
- Original sign node lat/lon remains an unverified OSM point; sign way/relation has no physical coordinate. Conditional/advisory/mph speed strings stay raw, never translated to legal speed_kmh.
- No OSMF public tile service downloads, no source DB SHA approval, no MapScreen verified overlay changes. Canonical schema remains data/road_intelligence/schema.sql and the trusted DB list remains empty.


## Source evidence update: REAL Vietnam Geofabrik dated PBF (2026-11-12)
- SOURCE ACQUIRED in a single GitHub Actions run 43624034669. URL https://download.geofabrik.de/asia/vietnam-261112.osm.pbf, exact size 332558874 B, SHA256 ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed and publisher MD5 1f7716ad049551852fc281e969a000aa.
- ODbL-1.0 © OpenStreetMap contributors. Source raw PBF NOT stored in Git/APK or artifact. Derived tag/coordinate reference rows archived with source/manifest checksum and ODbL attribution in GitHub artifact 14124844201 (retention 14d).
- Measured from actual PBF: 44,472 OSM ways with raw speed-related tags; 810 OSM sign-tagged nodes (all with syntactically valid OSM source coordinates), 1 tagged way, 0 sign relations. Exactly 68 speed ways include conditional tags; 276 advisory.
- OSM coordinates are only mapping nodes, NOT field-surveyed positions of actual roadside signs; a sign-tagged way is not a physical sign point. OSM `maxspeed=50` etc are tag strings, NOT date/class/direction-specific legal road speed limits. Real independently verified driver speed/sign records remain **0**.
- Detailed inventory, exact paths, artifacts and legal blockers: docs/VIETNAM_OSM_SPEED_SIGN_AUDIT_2026_11_12.md.


## Independent sign/speed worklist evidence (2026-11-15)
- Real snapshot source from prior PR: `vietnam-261112.osm.pbf` size 332,558,874 B SHA256 `ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed`, Geofabrik OSM ODbL 1.0. OSM tag inventory is reference-only.
- New field review queues (PR #22): 811 sign objects = 810 original OSM nodes with **unverified** source coordinates and 1 sign-tagged way with NO physical point. Type triage 654 unknown, 156 specific raw tagged nodes, one way. Source speed-tag way list 44,472 (41,356 plain integers NOT legally verified, 2,924 lacking main maxspeed, 192 directional/conditional/advisory).
- Verified physical sign points: 0. Verified legally enforceable site-specific speed records: 0. Survey dates/GPS accuracy/bearing, photographic evidence SHA, reviewer, vehicle class, direction and legal clauses are intentionally blank.
- Official Government Gazette reference for HUMAN legal research: https://congbao.chinhphu.vn/van-ban/van-ban-hop-nhat-so-74-2026-vbhn-tt-bxd-470578/68818.htm (`74/2026/VBHN-TT-BXD`, dated 2026-09-15). It consolidates regulations on speed/safe distance, **not** a certified map of where any OSM speed tag applies. Original `38/2024/TT-BGTVT` effective 2025-01-01; verify later changes and context.
- Real CSV files remain outside Android APK, not a source DB and not approved for navigation alerts.


## 2026-11-15 evidence intake contract
- New scripts/review_road_field_evidence.py consumes the existing 2026-11-12 real Vietnam UNVERIFIED review queue ZIP when separately provided with exact SHA256 26891bd61d10cb6228f30db5201af275254832b0705a5c553731df7f24c7df7c. It never downloads OSM tiles or calls paid APIs.
- Independent survey evidence JSON and photo bytes are distinct external private inputs. No real survey JSON/photos added to Git. Mechanical test uses only synthetic fixtures. Real approved legal km/h records: 0; approved measured physical sign coordinates: 0.
- Legal official references remain 74/2026/VBHN-TT-BXD and 38/2024/TT-BGTVT; no automatic speed inference from either or OSM.


## 2026-11-15 evidence conflict quarantine
- Existing Geofabrik Vietnam dated source: vietnam-261112.osm.pbf (332,558,874 bytes), SHA256 ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed, ODbL-1.0, reference-only. The original unverified review ZIP SHA256 26891bd61d10cb6228f30db5201af275254832b0705a5c553731df7f24c7df7c is NOT present in the repository/APK.
- Enhanced evidence checker now detects repeated sign photo SHA, duplicate source IDs and same code/point, road geometry mismatches, incompatible field and law times; this is mechanical screening, not field/legal verification.
- Unverified queue: 811 sign candidates, 44,472 speed-way candidates; verified legal speeds 0; approved physical sign coordinates 0; no Android road DB or driver warnings.


## 2026-11-15 portable evidence bundle (PR #26)
- Original real unverified review queue expected SHA256
  26891bd61d10cb6228f30db5201af275254832b0705a5c553731df7f24c7df7c
  (1,170,686 bytes) is NOT present in Git or APK. Operators supply it locally;
  the new archive stores those *unchanged* reviewed-source bytes, never the
  original 332,558,874-byte PBF.
- Source PBF dated 2026-11-12 SHA256
  ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed
  © OpenStreetMap contributors ODbL-1.0. All 811 sign objects and 44,472
  speed-tag ways are UNVERIFIED reference candidates; law/field-approved counts ZERO.
- ZIP structure documented at docs/ROAD_INTELLIGENCE_PRIVATE_EVIDENCE_BUNDLE.md.
  Per-member photo/packet/source SHA256, external whole-ZIP SHA and independent
  re-audit are tamper-evidence measures, not real-world truth or approval.


## PR #27: referenced-photo-only evidence bundles
- Existing UNVERIFIED Geofabrik Vietnam OSM PBF SHA256
  ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed
  (2026-11-12, ODbL-1.0 © OpenStreetMap contributors) remains external.
- Original queue ZIP expected SHA256
  26891bd61d10cb6228f30db5201af275254832b0705a5c553731df7f24c7df7c
  is likewise outside Git/APK. No real source photos/GPS measurements
  have been inserted into tests, scripts, assets, or any approval pin.
- Portable ZIP inventory now must match photographic evidence IDs exactly:
  every archived photo path comes from the independent packet's
  sign_evidence[*].photo.path; unreferenced photo content fails review.
  Valid-looking filenames/checksums do not establish genuine field surveying.


## Optional original GNSS GPX sign-coordinate evidence — PR #28
- `gps_track` within independently collected sign evidence may cite a
  separately owned original GPX 1.1 file and its exact SHA256, source URI,
  path and license. Validation compares an actual recorded WGS84 track,
  route or waypoint sample to the survey point and observation time.
  Missing optional GPX is not falsely labeled GNSS-verified; supplied bad
  GNSS data fails. GPS trace bytes are never downloaded from OSM or generated.
- New private archive records exact `tracks/<relative>.gpx` source bytes,
  file SHA256, optional track count and independently replayed audit.
  Check photographer and GPS collector source permissions before sharing.
- Real `vietnam-261112.osm.pbf` size 332,558,874 SHA256
  ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed
  ODbL-1.0 reference-only; original unverified queue ZIP expected SHA256
  26891bd61d10cb6228f30db5201af275254832b0705a5c553731df7f24c7df7c
  still outside repo. 811 sign objects / 44,472 speed ways unverified;
  **0** physical roadside sign coordinates and **0** enforceable legal
  speed values independently approved.
