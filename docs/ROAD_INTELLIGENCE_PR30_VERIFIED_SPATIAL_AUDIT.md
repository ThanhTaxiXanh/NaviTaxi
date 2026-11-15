# Phase 11 — PR #30 accepted spatial candidate-audit evidence

Date: 2026-11-15. This is a **mechanical code and artifact audit**, not
independent proof of enforceable speed limits or surveyed physical signs.

## Verified GitHub lineage

- Base main (PR #29 squash): `525d3a5a1d58a68005a5e6b7a1d13ec75187a889`.
- [PR #30](https://github.com/ThanhTaxiXanh/NaviTaxi/pull/30) merged into
  main as `b9dcd82d4ce20ab684c1946e6a3c10e13c74eb22`.
- [Python/SQLite CI](https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43678384469):
  SUCCESS, 125/125 unittest cases PASS (previous handoff 121).
- [Android PR-head CI](https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43678384457):
  SUCCESS: `:app:assembleDebug :app:testDebugUnitTest :app:lintDebug` plus
  `scripts/audit_road_assets.py` and `scripts/package_road_data.py`.
- [Post-merge main Android CI](https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43678522872):
  SUCCESS on the merge SHA above. No release APK/on-road validation claimed.

### Scope of change

- `scripts/review_road_candidate.py`:
  candidate road bounding box must match the actual GeoJSON LineString
  extrema (1e-8-degree tolerance for stored double-precision metadata).
  Road and physical sign spatial index values must agree with canonical
  SQLite coordinates subject only to conservative two-ULP float32 rounding
  for SQLite RTree. A 0.001-degree tolerance previously permitted roughly
  111 m latitude displacement.
- `tests/test_road_candidate.py`: 4 new synthetic-only regression cases,
  including shifted sign RTree (~55 m), shifted road RTree, inflated road
  bounding box and valid native SQLite RTree float32 outward rounding.
- No new road observations, law, sign GPS evidence, production SQLite,
  APK road resources or external dependency added.

## Direct post-merge APK and archive inspection

The artifact `phase4-apk-road-asset-audit` (GitHub Actions artifact ID
`14146828917`) was downloaded and both ZIP layers were checked:

- Outer artifact ZIP: 7,894 bytes, SHA-256
  `0cff03145a5912d6e3033b961874713a2bae6730912fa0fcb190a1195ce2a736`;
  ZIP CRC PASS.
- Nested `apk-road-assets.zip`: 8,952 bytes, SHA-256
  `56c8fc6afbff79ceb3271a52bea378879875a464b6cc6e3b96cb6a761b3ae2f3`;
  ZIP CRC PASS; `SHA256SUMS` verified 13/13.
- Post-merge `NaviTaxi-debug-apk` artifact ID `14146973349`;
  outer ZIP 33,473,020 bytes SHA-256
  `93374ddf6827ad9530be8f3fb1d9175589cfe7764f72f30d96a246470102e296`.
  Inside: `app-debug.apk`, 60,301,524 bytes SHA-256
  `a8e9941348040292ee12ebe5a97e19f6f164a892009f0b78d38b3e61446bc4e4`;
  both ZIP CRC checks PASS.

Exact paths **inside the post-merge APK** (the only five reviewed
geographic/map assets):

| Exact APK internal path | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| `assets/map_styles/offline_empty.json` | 238 | `6d8da2793feb72236894ba2a3cc5b090e12e0b5be02cff26d131260dd7fe61a9` |
| `assets/map_styles/osm_streets_experimental.json` | 416 | `6f9cff41ffe4fddc03eb359db60f5bc786e80f4c64042a99fbc917a693779c27` |
| `assets/map_styles/pmtiles_synthetic.json` | 698 | `88a8fa9eb1116daf89f8c55fbdb225c4d83d3be13ede436352ea2e3494eefe4b` |
| `assets/pmtiles/synthetic_manifest.json` | 525 | `580cb9bf6c139ab33b8f94dca288edb5a8256b5f0cce27a0e7a1f9eac9e67c81` |
| `assets/pmtiles/synthetic_test.pmtiles` | 462 | `d9a53b380463498cc31fd59a30d00e07a2f3f32f9f894eefa7b796d20470de9c` |

The three style JSON objects contain `version/name/sources/layers`.
`synthetic_manifest.json` records synthetic origin, license, tile identity,
SHA, `has_verified_speed_limits` and `has_verified_signs` (both false).
`synthetic_test.pmtiles` is PMTiles v3 with a 127-byte header, 25-byte root
directory, 245-byte compressed metadata and 65-byte tile data, zoom 0 only,
one synthetic tile. No real road-speed or physical-sign records are in these
assets. The reviewed APK has no `res/raw/` or `res/assets/` files, and no
embedded `.db`, `.sqlite`, `.sqlite3`, `.realm`, `.pbf`, `.geojson` or
`.csv` road dataset. One non-asset `DebugProbesKt.bin` is not a Road
Intelligence source file; compiled DEX is not a replacement for source review.

Relevant **source class and line**:
`app/src/main/java/vn/navitaxi/RoadDatabaseApproval.kt:30-31`,
`RoadIntelligenceApprovedPins.entries = emptyList()`. The source-code
scanner found Road Intelligence query terms in
`app/src/main/java/vn/navitaxi/RoadIntelligenceRepository.kt:26,50,69`;
these are query/rendering code, not embedded real measurements. The APK DEX
string scan is limited and was not a full Smali decompilation; the audit does
not claim binary-proof absence of every conceivable obfuscated constant.

## Reproduce the path/hash inventory and archive

Use a lawfully obtained APK (the provided post-merge GitHub Actions artifact),
outside private survey folders. Run from the repository root:

```bash
python3 scripts/audit_road_assets.py --root . \
  --apk /absolute/path/to/app-debug.apk \
  --out build/road-assets-postmerge.json
python3 scripts/package_road_data.py --root . \
  --apk /absolute/path/to/app-debug.apk \
  --output build/road-sign-speed-postmerge.zip
sha256sum build/road-sign-speed-postmerge.zip
unzip -t build/road-sign-speed-postmerge.zip
```

The packaging script preserves internal APK-relative paths and includes
an `AUDIT.json`, `MANIFEST.json` and `SHA256SUMS`. Never package private
field GPS/GPX/photos into Git or an APK. Use the separately controlled private
evidence ZIP workflow for originals.

## Remaining blockers

- Geofabrik Vietnam 2026-11-12 raw reference: 44,472 OSM speed-tag ways
  and 811 OSM sign-tag candidates — all **UNVERIFIED**.
- Independently approved applicable legal speed values: **0**.
- Independently surveyed and approved physical GPS sign locations: **0**.
- Independently approved Android SQLite SHA pins: **0**.
- Driver speed/sign alerts: **BLOCKED**. Phase 4 IN PROGRESS,
  Phase 5 NOT STARTED.
- Next actual-source work: obtain original sign photos/GPX with WGS84 accuracy,
  bearings, observation time and source rights; independently validate road
  geometry, travel direction, taxi vehicle classification, legal source clauses,
  effective times and separate reviewer decisions before any production pin.
