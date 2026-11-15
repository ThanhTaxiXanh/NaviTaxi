# Phase 11 — PR #34 original-photo EXIF/WGS84 verification record

Recorded 2026-11-15. **This report verifies code, synthetic tests, and APK
assets only. It does not independently approve a legal speed or physical sign.**

## Directly checked GitHub lineage / workflows

- Starting main commit `cfae62309f645904151c6d9a23aa00962b7ad559`, with
  zero open PRs at the start and Android push CI #43680051200 SUCCESS.
- [PR #34](https://github.com/ThanhTaxiXanh/NaviTaxi/pull/34) merged into
  main as commit `d7032bb2f774499c1c95376b1cb63a6785231d61`.
- [Python/SQLite PR CI](https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43685525932)
  SUCCESS on final PR head `29ead2f7402996cc92ba6ea7dad3a46a2880e610`;
  **135 of 135 tests passed** (up from 130).
- [Android PR-head CI](https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43685525912)
  SUCCESS for assembleDebug, testDebugUnitTest, lintDebug, and APK asset
  audit/package.
- [Post-merge main Android push CI](https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43685630989)
  SUCCESS on the exact merge SHA above. The APK and asset inventory were
  downloaded from **this post-merge run**, not reused from the PR build.

## Source-code changes and testing boundary

- `scripts/road_photo_exif.py`: bounded pure-Python JPEG APP1 Exif/TIFF
  extraction with IFD endian/length/duplicate checks. Reads the original
  JPEG's optional `DateTimeOriginal` (0x9003), `OffsetTimeOriginal`
  (0x9011), GPSInfo 0x8825 and signed WGS84 GPS rational fields.
- `scripts/review_road_field_evidence.py:251-288`: `survey_photo()`
  verifies actual private bytes, license, SHA-256 and image type. If the
  JPEG contains a **timezone-qualified** camera capture timestamp,
  rejects more than 15 minutes discrepancy with the claimed observation.
  If camera GPS tags are present, rejects coordinates more than
  max(15 metres, claimed GPS accuracy +10 metres) from the independently
  supplied WGS84 sign claim. Rejected sign paperwork also causes linked
  observed-sign legal-speed review paperwork to fail.
- `tests/test_road_field_evidence.py`: 5 synthetic regression methods,
  including matching EXIF, contradicted photo time, contradicted photo GPS
  while GPX matches the claimed point, missing timezone, and duplicate/
  damaged EXIF. These are invented photos/locations, not field evidence.
- EXIF metadata can be edited. Successful byte/hash consistency is
  **not** a camera authenticity proof, GPS receiver calibration, accurate
  field fix, sign orientation, source license sign-off, or legal speed
  verification. Missing JPEG EXIF, missing timezone offset and PNG EXIF
  remain **UNKNOWN**, not automatically valid observations.

## Downloaded main APK and audit ZIP — exact checksum evidence

GitHub Actions artifacts from the post-merge run:

1. `phase4-apk-road-asset-audit`, artifact ID **14149758685**
   - Outer ZIP: **7,894 bytes**; SHA-256
     `5de197cc6741eb02c83354b75091896706b3e3c715ed3eab607a830bf97e1c59`.
   - Nested `apk-road-assets.zip`: **8,952 bytes**; SHA-256
     `5da47f49f3bb3cb12712eec7a5c3996c1a976c748744082cf36d1aa4b94cac4d`.
   - Outer/nested ZIP CRC PASS; internal SHA256SUMS **13/13 PASS**,
     including source/AUDIT/MANIFEST entries.
2. `NaviTaxi-debug-apk`, artifact ID **14150485688**
   - Outer ZIP: **33,473,017 bytes**; SHA-256
     `f3a7e80262a3fd22c75103f7ed0c70c2bc4db73b96f7df21d532f074410e5e4c`.
   - `app-debug.apk` inside: **60,301,524 bytes**; SHA-256
     `5091257a3b20b0aca1bb11a60132172486bfcde7aa6a6578ebefc66073cc68f4`.
   - Outer ZIP/APK CRC PASS; **196 APK entries**, including **5 DEX**.
     This is a CI debug APK, **not** a signed field-tested driving release.

Exactly **five geographic/map assets** exist inside the checked APK.
Their true APK-internal paths, byte counts and independent SHA-256 of extracted
APK member bytes are:

| APK internal path | Bytes | SHA-256 |
| --- | ---: | --- |
| `assets/map_styles/offline_empty.json` | 238 | `6d8da2793feb72236894ba2a3cc5b090e12e0b5be02cff26d131260dd7fe61a9` |
| `assets/map_styles/osm_streets_experimental.json` | 416 | `6f9cff41ffe4fddc03eb359db60f5bc786e80f4c64042a99fbc917a693779c27` |
| `assets/map_styles/pmtiles_synthetic.json` | 698 | `88a8fa9eb1116daf89f8c55fbdb225c4d83d3be13ede436352ea2e3494eefe4b` |
| `assets/pmtiles/synthetic_manifest.json` | 525 | `580cb9bf6c139ab33b8f94dca288edb5a8256b5f0cce27a0e7a1f9eac9e67c81` |
| `assets/pmtiles/synthetic_test.pmtiles` | 462 | `d9a53b380463498cc31fd59a30d00e07a2f3f32f9f894eefa7b796d20470de9c` |

- Three styles are JSON objects with `version/name/sources/layers`.
- Synthetic manifest JSON keys include `format`, `origin`, `license`,
  `has_verified_speed_limits` and `has_verified_signs`; **both flags
  are false**. This is not an authoritative traffic sign manifest.
- PMTiles is a **synthetic binary PMTiles v3** with 127-byte header,
  root directory at byte 127 (25 bytes), compressed metadata at byte
  152 (245 bytes), and one tile at byte 397 (65 bytes); zoom 0 only,
  one synthetic vector tile, **no legal road speed or field sign point**.
- There are no `res/raw/` or `res/assets/` entries and no APK
  `*.db`, `*.sqlite`, `*.sqlite3`, `*.realm`, `*.pbf`,
  `*.geojson` or `*.csv`. The reviewed APK contains no physical
  sign survey coordinates or legal-speed database.
- The repository has `data/road_intelligence/schema.sql` (4,124 bytes;
  SHA-256 `6618cef715f3f0512f03291e19017a2d1a13607f1006d8277ada900bcb01c5d3`)
  but this *schema source file* is not an APK road DB.
- `scripts/audit_road_assets.py` recorded **18 source code search
  hits**. Examples: `app/src/main/java/vn/navitaxi/RoadIntelligenceRepository.kt:26,50,69`
  SQLite query/rendering logic; synthetic Android instrumented test
  `RoadIntelligenceApprovalSmokeTest.kt:27-31`. These are **not real
  GPS coordinates or approved speed records**. Source-code scanning
  and checking APK DEX names are not equivalent to full Smali disassembly;
  a claim of exhaustive binary bytecode absence is not made.
- `app/src/main/java/vn/navitaxi/RoadDatabaseApproval.kt:30-31` retains
  **`RoadIntelligenceApprovedPins.entries = emptyList()`**.

## Reproducible private/offline asset and ZIP inspection

Use a lawfully acquired APK downloaded from the indicated GitHub Actions run.
From repository root:

```bash
python3 scripts/audit_road_assets.py --root . \
  --apk /absolute/path/to/app-debug.apk \
  --out build/road-assets-pr34.json
python3 scripts/package_road_data.py --root . \
  --apk /absolute/path/to/app-debug.apk \
  --output build/road-assets-pr34.zip
sha256sum build/road-assets-pr34.zip
unzip -t build/road-assets-pr34.zip
unzip -p build/road-assets-pr34.zip SHA256SUMS
```

The archive includes exact relative file tree paths plus `AUDIT.json`,
`MANIFEST.json`, `SHA256SUMS`. Original private photos and GPX traces
must be held separately with `scripts/package_field_evidence.py` and
never committed to GitHub or included in this APK/road-asset archive.

## Fixed safety status / remaining work

Reference-only Geofabrik Vietnam 2026-11-12 data (external, ODbL-1.0):
**44,472** OSM ways tagged speed, **811** OSM sign-tag objects,
ALL **UNVERIFIED**.

- Approved applicable Vietnamese legal speed records: **0**.
- Independently surveyed and approved physical WGS84 sign coordinates: **0**.
- Publisher-approved Android road database SHA-256 pins: **0**.
- Driver speed/traffic-sign warnings: **BLOCKED**.
- Phase 4 **IN PROGRESS**; Phase 5 **NOT STARTED**.

Next: independently obtain original sign photos, GNSS device logs/GPX,
field latitude/longitude accuracy, camera time/EXIF, physical sign bearing,
source rights, road geometry, and date/vehicle/direction-specific governing
legal clauses; have separate reviewers adjudicate before releasing any
SQLite SHA or enabling driver alerts.
