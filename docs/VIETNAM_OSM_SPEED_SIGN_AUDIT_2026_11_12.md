# 2026-11-12 Vietnam OSM speed and traffic-sign reference evidence

## Actual, independently inspected source bytes

- Provider/index: https://download.geofabrik.de/asia/vietnam.html
- Snapshot URL: https://download.geofabrik.de/asia/vietnam-261112.osm.pbf
- Source file size: **332,558,874 bytes**.
- Full-file SHA-256: **ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed**.
- Publisher MD5 sidecar: **1f7716ad049551852fc281e969a000aa** (matched real downloaded bytes).
- License: ODbL-1.0, © OpenStreetMap contributors; derivative database obligations apply.
- GitHub Actions: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43624034669 (SUCCESS, actual PBF streamed with pyosmium 4.3.2).
- Evidence artifact name: `phase4-real-vietnam-osm-reference-NOT-VERIFIED`, GitHub artifact ID **14124844201**, outer ZIP digest **sha256:42352c12807767bfbe7ae4af26a060ad156443e2b05411496f7b0c63d47a5370**.
- Actual reference-only nested ZIP SHA-256:
  **23bfbef5e6fdc63a2a5e268a04fafeaee837f6c83c1fa5a3b21894bf47094380**.
- Local inspection of downloaded GitHub artifact verified nested `SHA256SUMS` for all 3 payload files, manifest counts against every JSONL line, and that no candidate declares driver alerts.

## Real source tag counts (not physical/legal verification)

| OSM source object type/tag | Measured records |
| --- | ---: |
| Highways/ways with any `maxspeed*` candidate tag | **44,472** |
| Sign-tagged OSM nodes | **810** |
| Sign-tagged ways | **1** |
| Sign-tagged relations | **0** |
| Sign-tagged nodes with a geometrically valid original OSM point | **810** |
| Sign-tagged nodes missing usable WGS84 original point | **0** |
| Road ways with conditional speed tags | **68** |
| Road ways with advisory speed tags | **276** |
| Road ways containing an `mph` raw speed value | **0** |

Raw `maxspeed` value distribution (NOT legally confirmed speed limits):
`50` 13,079; `60` 10,652; `80` 5,560; `90` 4,186;
**2,924** speed-tag ways have no primary `maxspeed` field; `40` 2,488;
`30` 1,479; `120` 1,410; `100` 1,162; `20` 1,025.

Raw `traffic_sign` values include `yes` **649**, `maxspeed` **91**,
`city_limit` **15**, and 5 variants without a primary `traffic_sign`
key. A generic `yes` does not identify a physical roadside sign or its
regulatory meaning. These are volunteer-sourced OSM tags, NOT field surveys.

**Zero** legally approved real speed-limit segments and **zero** field-surveyed
physical sign coordinates are currently shipped or permitted for warnings.
The real source contains 810 **OSM node points**, not independently surveyed
real-world sign coordinates. The single sign-tagged way is not converted to a
point. No speed is applied based on OSM tags.

## Exactly where source data and audits live

Original input on CI runner: `build/geofabrik-vietnam-source/vietnam-261112.osm.pbf`
(temporary; **not committed or bundled in APK**).

- `build/geofabrik-vietnam-source/receipt.json` – original size, source URI,
  publisher MD5, calculated SHA-256 and negative approval flags.
- `build/vietnam-osm-reference-only/speed_way_candidates.jsonl` – exact raw
  speed-tag way provenance and values.
- `build/vietnam-osm-reference-only/traffic_sign_candidates.jsonl` –
  sign-tag node/way/relation provenance, node WGS84 reference coordinate only.
- `build/vietnam-osm-reference-only/manifest.json` – record counts and
  each derivative file length/SHA-256.
- `build/vietnam-osm-reference-only.zip` – JSONL/manifest and `SHA256SUMS`.
- `build/vietnam-osm-reference-summary.json` – summary with verification false.

## Production APK forensic scan after source ingestion change

Run https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43624034656
SUCCESS; APK artifact `phase4-apk-road-asset-audit` id **14125266676**.
All archived APK-source checksums were verified.

Exactly 5 test-only APK assets, none a real Road Intelligence database:

| Inside APK | Size (bytes) |
| --- | ---: |
| `assets/map_styles/offline_empty.json` | 238 |
| `assets/map_styles/osm_streets_experimental.json` | 416 |
| `assets/map_styles/pmtiles_synthetic.json` | 698 |
| `assets/pmtiles/synthetic_manifest.json` | 525 |
| `assets/pmtiles/synthetic_test.pmtiles` | 462 |

No `assets/road_intelligence/road_intelligence.db`, `.realm`,
`.sqlite`, speed-limit records or physically surveyed sign points were
found. Data source ingestion works **outside Android** and the production
`RoadDatabaseApprovalGate` pin list remains empty.

## Extra independent review gate (PR #20)

`scripts/audit_osm_reference_quality.py` verifies file size and SHA-256,
source receipt vs manifest SHA/URI/size, exact JSONL candidate counts,
unique original OSM object identity, valid WGS84 node points, and the
requirement that way/relation signs have null physical coordinates.
It rejects injected `speed_kmh`, claims of legal/physical verification,
and corrupted or duplicate records. It reports raw tag distributions,
**never approves any legal speed or physical sign**.

## Remaining mandatory blockers

- Field surveys of actual physical sign WGS84 positions, direction and time.
- Source-specific Vietnamese legal speed limits based on road class, vehicle
  class, direction, posted signage and verification date.
- Human/independent approval of distinct speed and sign domains and exact
  database release SHA (code-reviewed allowlist).
- ODbL compliance and safe release packaging for any derivative database.
- Real 34-province offline package catalog, on-device/offline route field QA.

Phase 4 remains **IN PROGRESS**, Phase 5 **NOT STARTED**. This audit is an
evidence inventory, not a driver-safe navigation or traffic-law product.
