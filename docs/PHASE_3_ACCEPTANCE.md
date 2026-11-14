# Phase 3 – PMTiles v3 offline acceptance

## Scope
- Use native MapLibre 13.7.1 PMTiles protocol (no new paid SDK or unnecessary loopback server).
- Format: PMTiles v3 / one compressed MVT z0 tile / vector layer demo_grid / 2 artificial cross lines.
- Source: scripts/build_synthetic_pmtiles.py; output is small, deterministic and fully synthetic.
- Exact APK internal files:
  * assets/pmtiles/synthetic_test.pmtiles — 462 bytes.
  * assets/pmtiles/synthetic_manifest.json — SHA-256, version, source license, clearly false real-road/sign/speed flags.
  * assets/map_styles/pmtiles_synthetic.json — vector source style template.
- SHA-256 archive: d9a53b380463498cc31fd59a30d00e07a2f3f32f9f894eefa7b796d20470de9c.
- Header v3: 127 bytes, little-endian section offsets, gzip metadata/directory and MVT tile. Prevent stale/mutated bytes or unsupported tile type being used.
- MapLibre Native cannot read PMTiles directly from Android assets; verify and copy to <app-private-files>/offline_packages/synthetic_test.pmtiles before loading with pmtiles://file://.
- Native remote PMTiles supports HTTP Range with pmtiles://https:// but no live endpoint is configured. Loopback probe checks 206, Content-Range and expected 127-byte header.

## Test gates
- Python reproduce-byte-for-byte, checksum mismatch, malformed header, local HTTP Range.
- Kotlin JUnit PMTiles v3 header sanity tests.
- Android assembleDebug + testDebugUnitTest + lintDebug.
- Android API 35 emulator: launch native MapLibre screen, select synthetic PMTiles, verify style opens in renderer, assert unknown speed/sign overlays, return without crash.
- All current-head workflows must be green before merging to main.

## Explicit limitations
- The synthetic geometry is not a Vietnam map, not an OSM extract and contains NO road names, POIs, driving routes, legal maxspeed observations or traffic sign locations.
- No 34-province dataset, download/pause/resume manager or routing is claimed.
- No offline driving suitability or production performance guarantee; Phase 4/5/11 handle real data and Phase 15/17 handle device driving tests.

## Final verified evidence
- SQLite/Python PMTiles byte-for-byte, corruption and local Range tests: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43603204053 (success).
- Kotlin Android compile, debug APK, unit test and Lint: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43603204092 (success).
- MapLibre Android Emulator API 35 2/2 native offline style and lifecycle tests: https://github.com/ThanhTaxiXanh/NaviTaxi/actions/runs/43603204072 (success).
- Phase 3 code PR #5 merged: https://github.com/ThanhTaxiXanh/NaviTaxi/pull/5, commit f401f03.
- Tested: integrity and native style load, NOT real tile coverage, navigation, province coverage or actual traffic sign data.
