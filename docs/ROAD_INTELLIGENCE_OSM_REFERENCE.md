# Phase 4 — OSM Road Intelligence reference-only staging

**Status: implementation under CI review. NOT a legal speed-limit / traffic-sign source approval.**

## Source and license

The Vietnam extract is described at https://download.geofabrik.de/asia/vietnam.html
with an OSM PBF at https://download.geofabrik.de/asia/vietnam-latest.osm.pbf .
This *latest* file can change; record the exact local SHA-256 for repeatable
processing. **No full Vietnam PBF is downloaded, checked, or embedded in this PR.**

OpenStreetMap data is under ODbL 1.0 with attribution and derivative database
obligations. The PBF reader uses Python-only pyosmium **4.3.2** (BSD-2-Clause);
no Android dependency, paid API or server is added.

OSM traffic-sign mapping: https://wiki.openstreetmap.org/wiki/Key:traffic_sign .
A way/relation sign tag describes an affected section, **not a physical sign
position**. A node is an OSM point, not necessarily a surveyed roadside sign.
OSM maxspeed can be mph, conditional, lane-specific, advisory or inaccurate;
no unverified tag becomes a legal km/h limit.

## Pipeline and safeguards

- Local input: `.osm` or `.osm.pbf` only, not tile services.
- Required pin: 64-character SHA-256, checked before and after parsing.
- Provenance: HTTPS source URI, exact filename/byte size/hash, ODbL license,
  original OSM object type/id/version/timestamp.
- Files: `speed_way_candidates.jsonl`, `traffic_sign_candidates.jsonl`,
  `manifest.json`, and optional ZIP with `SHA256SUMS`.
- Raw `maxspeed*`, `traffic_sign*`, `direction` and context tags are preserved.
  mph, conditional and advisory values are never converted to `speed_kmh`.
- Way and relation sign candidates always have `osm_node_coordinate=null`.
  Only OSM nodes can have an original coordinate, still **not independently
  verified**. No way centroids or invented points.
- Output to `app/src/main/assets`, `app/src/main/res` and
  `data/road_intelligence` is rejected; no SQLite import, Android assets,
  PMTiles, approvals, overlay or driver alerts.
- Manifest and every record explicitly mark approval and driver alerts FALSE.
  Errors reject the entire output and discard incomplete staging files.
  Existing completed output cannot be silently overwritten.

## Command when a lawful local snapshot actually exists

```bash
python -m pip install osmium==4.3.2
sha256sum /path/to/vietnam-snapshot.osm.pbf

python scripts/extract_osm_road_reference.py \
  --input /path/to/vietnam-snapshot.osm.pbf \
  --expected-sha256 <recorded-lowercase-SHA256> \
  --source-uri https://download.geofabrik.de/asia/vietnam-latest.osm.pbf \
  --output-dir build/osm-reference-vietnam-SNAPSHOT \
  --archive build/osm-reference-vietnam-SNAPSHOT.zip
```

The command makes NO network request. The source link is a candidate only,
not proof this project downloaded it. Do not invent real counts, coordinates,
hashes or extract timestamps.

## Synthetic CI verification

Python/SQLite CI installs pinned pyosmium, tests XML and *actual binary PBF*
parsing with a generated **test-only** fixture, then uploads JSONL, manifest
and ZIP. It tests raw mph/conditional values, sign node vs way/relation point,
wrong SHA, dangerous URLs, archive integrity, output non-overwrite and abort
on candidate limit. No real-world signed legal speeds or sign positions exist
in these fixtures. Synthetic coordinates and numbers MUST never be bundled as
legal driving data.

## Still blocked

Acquire a lawful versioned Vietnam PBF with actual URI, license, timestamp,
size and independently retained SHA-256. Only after staging real reference
tags should independent law/field review establish vehicle-class and
direction-specific speeds and surveyed sign coordinates. Release to SQLite
requires `review_road_candidate.py`, source/license approval and code-reviewed
`RoadDatabaseApprovalGate` pin for each domain. Phase 4 remains unfinished
for real maps and device/OEM field validation; Phase 5 NOT STARTED.
