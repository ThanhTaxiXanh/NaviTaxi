# Road Intelligence: field sign surveys and legal speed review worklists

## Scope and evidence

This phase converts the already independently checksum-audited **2026-11-12
Geofabrik Vietnam OSM reference snapshot** into **unapproved review queues**.
It does not convert an OSM tag or tagged node into an enforceable speed limit
or a field-surveyed physical roadside sign.

- Exact upstream snapshot: https://download.geofabrik.de/asia/vietnam-261112.osm.pbf
- Snapshot SHA-256: ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed
- Original reference source: 44,472 way speed-tag candidates; 810 sign
  nodes, one sign-tagged way, zero sign relations (source count, not approvals).
- Source: © OpenStreetMap contributors, ODbL 1.0, with attribution and
  derivative database distribution requirements.
- Real-source JSONL/manifest checksums were verified separately; the
  reference-only archives are NOT installed as APK assets.
- Official speed-law research starting point, NOT approval of OSM values:
  [74/2026/VBHN-TT-BXD, published 15/09/2026](https://congbao.chinhphu.vn/van-ban/van-ban-hop-nhat-so-74-2026-vbhn-tt-bxd-470578/68818.htm).
  It consolidates the traffic speed/distance circular; original
  [38/2024/TT-BGTVT](https://congbao.chinhphu.vn/van-ban/thong-tu-so-38-2024-tt-bgtvt-43378/53130.htm)
  took effect 01/01/2025. Reviewers must verify current amendments,
  effective dates, vehicle class, direction, posted signs and local road
  conditions. These links do not independently establish the speed of
  any particular OSM way.

## Exact output paths and types

Script: scripts/build_road_review_queues.py

- traffic_sign_field_survey_queue.csv: original OSM node/way/relation ID,
  version, timestamp, raw sign tags, only original OSM node coordinates when
  present, and classification for follow-up. Survey latitude/longitude,
  accuracy, orientation/bearing, actual sign code, photo SHA-256, survey date,
  reviewer and independent evidence URL are BLANK.
- speed_limit_legal_review_queue.csv: original OSM way ID, version,
  timestamp, unmodified raw maxspeed string and other tags, class/context
  flags. Reviewed vehicle class, travel direction, applicable legal
  clause and URL, effective date, sign evidence IDs and reviewer are BLANK.
  There is deliberately NO auto-produced legal speed_kmh.
- REVIEW_INSTRUCTIONS.txt: field work and provenance safeguards.
- manifest.json: upstream PBF SHA, original reference-manifest SHA,
  reviewed counts/buckets, file sizes and SHA-256, 0 independently verified
  legal speeds and physical roadside signs, 0 surveys completed.
- Optional ZIP with SHA256SUMS: complete review worklist archive.

Source objects can be used to assemble a survey schedule without asserting
these represent confirmed physical objects. OSM traffic_sign=yes is an
unknown code: never interpret it as a speed sign. The single sign-tagged way
has NO physical point and cannot be surveyed at a fabricated centroid.

Spreadsheet exports quote every field and neutralize formulas/CRLF in raw OSM
tags. Review files cannot be written to app/src/main/assets, app resources or
data/road_intelligence. Existing review outputs are never overwritten.

## Reproduce with the exact inspected reference archive (no PBF re-download)

Extract the reviewed reference-only ZIP that contains manifest.json,
speed_way_candidates.jsonl, traffic_sign_candidates.jsonl and SHA256SUMS:

    mkdir -p build/vietnam-osm-reference-for-review
    unzip /path/to/vietnam-osm-reference-only.zip \
      -d build/vietnam-osm-reference-for-review

    python scripts/build_road_review_queues.py \
      --reference-dir build/vietnam-osm-reference-for-review \
      --output-dir build/road-legal-field-review-2026-11-12 \
      --archive build/road-legal-field-review-2026-11-12.zip

Audit validates exact JSONL byte sizes, SHA-256, OSM identity and WGS84
coordinates before writing any output. Source publication receipts may be
passed with --receipt /path/to/receipt.json for independent cross-check.

## Independent approval remains separate and unimplemented

Completing or modifying these CSVs has NO authority to approve an OSM tag.
A legal speed-limit record requires a current relevant legal rule and/or
posted signage, actual road geometry and direction, vehicle applicability,
date and a verifiable independent reviewer. A physical sign requires an
actual survey with measured WGS84 position, bearing, sign code, accuracy,
timestamp, photographic evidence hash, road/direction and reviewer.

When independent evidence exists, a **separate reviewed release process**
must validate the scope and geometry, license, update staleness and approved
DB SHA via RoadDatabaseApprovalGate. No route matching or driver alert is
enabled by these CSVs or this PR. No field survey was actually performed.

Phase 4 remains IN PROGRESS (licensed real offline packages/field/OEM proof
not accepted); Phase 5 NOT STARTED. Phase 11 Road Intelligence alert
functionality remains BLOCKED until legal and physical sign verification.
