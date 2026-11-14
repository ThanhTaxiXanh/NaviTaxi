# Real Vietnam OSM reference snapshot audit (Phase 4)

## Fixed source and scope

- Upstream listing: https://download.geofabrik.de/asia/vietnam.html
- Fixed historical snapshot: https://download.geofabrik.de/asia/vietnam-261112.osm.pbf
- Sidecar: https://download.geofabrik.de/asia/vietnam-261112.osm.pbf.md5
- Published size: **332,558,874 bytes**, dated 2026-11-12.
- License: **ODbL-1.0**, © OpenStreetMap contributors.
- Reader: Python-only pyosmium 4.3.2, BSD-2-Clause.
- No download from the OSMF public tile services, paid APIs or map servers.

An immutable-date filename prevents silent use of the moving `latest` alias.
The publisher sidecar MD5 checks transfer consistency, but **is not a
digital signature** or independent data approval. The workflow also computes
full-file SHA-256 and records it in `receipt.json` and the reference manifest.
Hashes/bytes alone do NOT prove posted speed limits or physical sign locations.

## One-time acquisition and exact output

Workflow: `.github/workflows/vietnam-real-road-reference.yml`. Runs only when
the acquisition script, its tests, or the workflow itself changes in a PR to
`main`, or when explicitly dispatched. Routine CI does **not** repeat a 333 MB
download. Its single audit is bounded to 350 million bytes and exact expected
size 332,558,874 bytes; rejects unexpected redirects away from Geofabrik
HTTPS. Any short read, bad MD5/size, invalid source, or exception removes the
entire partial download directory.

- `build/geofabrik-vietnam-source/vietnam-261112.osm.pbf`:
  temporary complete download on the GitHub runner; **never uploaded**.
- `build/geofabrik-vietnam-source/receipt.json`:
  filename, source and MD5 URI, measured size, original publisher MD5,
  newly measured SHA-256 and explicit nonapproval flags.
- `build/vietnam-osm-reference-only/speed_way_candidates.jsonl`:
  original OSM `maxspeed*` tag strings, way type/id/version/timestamp,
  no inferred legal `speed_kmh`.
- `build/vietnam-osm-reference-only/traffic_sign_candidates.jsonl`:
  tagged OSM nodes, ways and relations. Node original coordinates are
  **unverified reference points**; way/relation physical point is always null.
- `build/vietnam-osm-reference-only/manifest.json`:
  per-file byte size/SHA-256, source SHA and true candidate counts.
- `build/vietnam-osm-reference-only.zip`: manifest, JSONL and `SHA256SUMS`.
- `build/vietnam-osm-reference-summary.json`: candidate counts and
  explicit zero independently verified legal speeds and physical signs.

CI uploads receipts and small derivative audit artifacts, NOT the original
large PBF. Artifacts retain 14 days. ODbL attribution must be retained and
derivative database licensing assessed before any downstream distribution.

## Exact command line reproduction

```bash
python -m pip install --disable-pip-version-check osmium==4.3.2
python scripts/acquire_geofabrik_vietnam.py \
  --output-dir build/geofabrik-vietnam-source
PIN=$(python -c "import json;print(json.load(open('build/geofabrik-vietnam-source/receipt.json'))['sha256'])")
python scripts/extract_osm_road_reference.py \
  --input build/geofabrik-vietnam-source/vietnam-261112.osm.pbf \
  --expected-sha256 "$PIN" \
  --source-uri https://download.geofabrik.de/asia/vietnam-261112.osm.pbf \
  --output-dir build/vietnam-osm-reference-only \
  --archive build/vietnam-osm-reference-only.zip
```

The reference archive MUST NOT be installed in `road_intelligence.db`,
`app/src/main/assets`, `res` or a verified speed-limit/sign map layer.
No `RoadDatabaseApprovalGate` pin is created.

## Acceptance conditions and blocked domains

Only call the real-source audit complete if GitHub Actions actually downloads
the full date-pinned PBF, verifies its byte length/MD5, computes SHA-256,
streams pyosmium successfully and publishes source-backed counts and hashes.
If network or input fails, state the blocker; do not invent any counts or
substitute the synthetic test fixtures.

Even a successful source audit is just **unverified OSM reference data**.
Independent law, vehicle-class and direction verification; physical survey
of signs with WGS84 position/bearing; legal licenses; and on-device road
testing are mandatory before driver warnings. Phase 4 overall remains
IN PROGRESS and Phase 5 has not begun.


## Real-world source execution result — verified
- PR #19 merged 8e9ad423100234b022506667b269f25d0a3df556 after Python/SQLite 43624034554, actual source workflow 43624034669 and Android 43624034656 all SUCCESS.
- The dated source file *was actually downloaded and parsed*: 332558874 bytes, SHA256 ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed, publisher MD5 1f7716ad049551852fc281e969a000aa.
- Source-tag object counts: 44,472 speed-tagged ways, 810 sign-tagged OSM nodes, 1 sign-tagged way, 0 relations. All OSM sign-node coordinates remain UNVERIFIED reference positions, not surveyed roadside sign points.
- Reproducibility evidence (14-day GitHub artifact): ID 14124844201, digest sha256:42352c12807767bfbe7ae4af26a060ad156443e2b05411496f7b0c63d47a5370, nested ZIP SHA256 23bfbef5e6fdc63a2a5e268a04fafeaee837f6c83c1fa5a3b21894bf47094380. Nested SHA256SUMS + JSONL line counts were checked.
- Detailed findings: `docs/VIETNAM_OSM_SPEED_SIGN_AUDIT_2026_11_12.md`. Real-data upload to APK and speed/sign alert flags remain DISABLED.
