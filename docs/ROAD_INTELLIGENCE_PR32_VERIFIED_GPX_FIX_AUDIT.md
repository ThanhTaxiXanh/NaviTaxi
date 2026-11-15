# Phase 11 — verified GPX sign-fix evidence guard (PR #32)

Evidence recorded 2026-11-15. **Mechanical consistency, not legal-speed or physical sign approval.**

## GitHub provenance and CI

- Starting main SHA: `663468b61eea989c2ea506045cbc2698261416fa`.
- [PR #32](https://github.com/ThanhTaxiXanh/NaviTaxi/pull/32) **MERGED**; final main
  SHA `4f009ac16735acae35c4f8d0bd1aa8c958a8ff2a`.
- [Final PR-head Python/SQLite tests](https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43679448917):
  130/130 PASS (previous 125), `road-data-tests` completed SUCCESS.
- [Final PR-head Android CI](https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43679448978):
  SUCCESS for `:app:assembleDebug :app:testDebugUnitTest :app:lintDebug`,
  and full APK asset audit/archive.
- [Post-merge main Android CI](https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43679593826):
  `build` job SUCCESS on exact main SHA above.
- All five new test methods and subcases are **synthetic only**; neither
  confidence in an original device source nor real sign existence follows
  from a green CI job.

## Reviewed implementation and limitations

- `scripts/review_road_field_evidence.py:264-350`:
  optional GPX 1.1 evidence now requires mandatory root `version="1.1"` and
  nonblank `creator`; a producer name is not authenticated identity.
  Per-point optional `fix`, `sat` and `hdop` values must be syntactically
  valid and non-duplicated. An explicitly failed fix (`none`), too few
  satellites or poor horizontal dilution cannot establish a position/time
  match, even if its coordinates appear identical to a sign claim.
  Missing quality fields remain UNKNOWN and require original device review.
- Original SHA-256 byte matching and original GPX/photo privacy controls
  are unchanged. The quality heuristics are not calibrated positional error
  limits; GPX `hdop` does not equal WGS84 accuracy in metres.
- `tests/test_road_field_evidence.py` adds five synthetic regression
  methods: invalid root metadata, unusable fix/satellite/HDOP, invalid
  reported quality or duplicates, valid 3D test-only fix, mixed
  failed+usable source points.
- Official GPX 1.1 schema: https://www.topografix.com/gpx/1/1/
- Android approval allowlist in
  `app/src/main/java/vn/navitaxi/RoadDatabaseApproval.kt:30-31` remains
  `RoadIntelligenceApprovedPins.entries = emptyList()`.

## Direct APK and road asset inventory after merge

Downloaded GitHub Actions artifact `phase4-apk-road-asset-audit`
ID **14148011282**, from the post-merge main run above:

- Outer audit ZIP: **7,897 bytes**, SHA-256
  `f3bd457d7c19f371a29a40adaf698286c60eb4f5dfe719d803df5334df5ff3d9`,
  ZIP CRC PASS.
- Nested `apk-road-assets.zip`: **8,953 bytes**, SHA-256
  `a2d76fee329512c7ee71cde096436e96de01ddbc28bc12f33a9ec3f746beb8b3`,
  ZIP CRC PASS and internal SHA256SUMS **13/13 PASS**.
- APK debug artifact ID **14147454260**: outer archive 33,473,019
  bytes SHA-256
  `ca21cbfb114bf268dce9b53bd755b7972e4a4c8322e9e630ffcde75c4b25d55b`,
  ZIP CRC PASS; inner `app-debug.apk` **60,301,524 bytes** SHA-256
  `7e2d24316f90a92e8d23a9228a639b333b473a8929ab59f715a84234ee3ab487`,
  APK ZIP CRC PASS. This is a CI debug build, **not a device-tested release**.

Five real APK **entry paths**, all synthetic/experimental map resources:

| Exact path inside APK | Size bytes | SHA-256 |
| --- | ---: | --- |
| `assets/map_styles/offline_empty.json` | 238 | `6d8da2793feb72236894ba2a3cc5b090e12e0b5be02cff26d131260dd7fe61a9` |
| `assets/map_styles/osm_streets_experimental.json` | 416 | `6f9cff41ffe4fddc03eb359db60f5bc786e80f4c64042a99fbc917a693779c27` |
| `assets/map_styles/pmtiles_synthetic.json` | 698 | `88a8fa9eb1116daf89f8c55fbdb225c4d83d3be13ede436352ea2e3494eefe4b` |
| `assets/pmtiles/synthetic_manifest.json` | 525 | `580cb9bf6c139ab33b8f94dca288edb5a8256b5f0cce27a0e7a1f9eac9e67c81` |
| `assets/pmtiles/synthetic_test.pmtiles` | 462 | `d9a53b380463498cc31fd59a30d00e07a2f3f32f9f894eefa7b796d20470de9c` |

APK scan: no `res/raw/` or `res/assets/` entries; no
`*.db`, `*.sqlite`, `*.sqlite3`, `*.realm`, `*.geojson`,
`*.pbf`, or `*.csv` entries. The four map-style/manifest JSON files
remain descriptive, not legal evidence; the tiny PMTiles v3 file
contains only synthetic vector features. The APK has five DEX files and
one unrelated `DebugProbesKt.bin`; DEX string inspection is not full
Smali reverse engineering and does not prove the absence of every
possible obfuscated constant. Source review found only untrusted-data
handling, not approved hardcoded speed/sign records.

The reference `data/road_intelligence/schema.sql` exists in the
**repository**, but no physical sign/road-speed SQLite database from it
was included in the audited APK.

## Reproduce audit and evidence ZIP packaging

From repository root, with a legally acquired `app-debug.apk` obtained
from the post-merge GitHub Actions artifact:

```bash
python3 scripts/audit_road_assets.py --root . \
    --apk /absolute/path/to/app-debug.apk \
    --out build/road-asset-inventory.json
python3 scripts/package_road_data.py --root . \
    --apk /absolute/path/to/app-debug.apk \
    --output build/road-sign-speed-archive.zip
sha256sum build/road-sign-speed-archive.zip
unzip -t build/road-sign-speed-archive.zip
```

The archive retains exact APK-relative paths, report, `MANIFEST.json`,
and `SHA256SUMS`. Do not add private GPX, photo, location data or
unreviewed legal speed assertions to GitHub/APK or the audit archive.
Private evidence has a separate controlled bundle process documented in
`docs/ROAD_INTELLIGENCE_PRIVATE_EVIDENCE_BUNDLE.md`.

## Unchanged safety gates and next research

Original Geofabrik Vietnam 2026-11-12 source/reference:
**44,472** OSM speed-tag ways; **811** OSM sign-tag objects;
**all UNVERIFIED**. Original PBF and unverified review ZIP stay outside
Git/APK with their independent source digests unchanged.

- Independently approved applicable legal speeds: **0**.
- Independently field-surveyed and approved physical WGS84 sign points: **0**.
- Approved Android SQLite SHA pins: **0**.
- Driver speed/sign alerts: **BLOCKED**.
- Phase 4: **IN PROGRESS**; Phase 5: **NOT STARTED**.

Next: authenticate *original* source photographs/GPX, receiver accuracy and
clock, sign bearing and travel direction, independent road geometry, and
dated legal clause applicability by vehicle category before preparing any
publisher-approved SQLite release.
