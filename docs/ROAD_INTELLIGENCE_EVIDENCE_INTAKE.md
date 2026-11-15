# Road Intelligence — Independent field & legal evidence intake (Phase 11)

Status: **mechanical audit only**. This pipeline cannot approve a legal speed
or physical traffic-sign location, create an Android database or enable alerts.
The sign and speed allowlists in RoadDatabaseApprovalGate remain EMPTY.

## Source boundary

Original Geofabrik Vietnam OSM PBF, 2026-11-12:
- Filename: vietnam-261112.osm.pbf
- Size: 332,558,874 bytes
- SHA-256: ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed
- License: ODbL-1.0, © OpenStreetMap contributors.
- Original review queue ZIP (previous session; NOT checked into Git):
  NaviTaxi_Vietnam_2026-11-12_Field_Sign_Speed_Review_UNVERIFIED.zip
- Original queue ZIP SHA-256:
  26891bd61d10cb6228f30db5201af275254832b0705a5c553731df7f24c7df7c

This archive contains 811 **OSM sign-tag candidates** and 44,472 **OSM
speed-tag way candidates**. Their source coordinates/tags remain UNVERIFIED.
The original ZIP must be available locally to run a full real-source
evidence audit; these scripts do NOT reconstruct any real surveys.

## Input v1

Use a separate UTF-8 JSON evidence packet with:

- "format": "navitaxi-independent-road-evidence/v1"
- "source_review_manifest_sha256": the SHA-256 of manifest.json within
  the separately SHA256-pinned review ZIP.
- "sign_evidence": an array of survey observations.
- "speed_evidence": an array of legal-speed assessments.

Each sign entry must have review_id, evidence_uri, surveyor, reviewer (a
different identity), observed_at, reviewed_at (timezone-aware), measured
WGS84 latitude/longitude, GPS accuracy <=25m, measured bearing [0,360),
specific Vietnamese sign code (e.g., "P.127"), explicit forward/backward
application, related_osm_way_id, road_geometry (GeoJSON LineString),
road_geometry_sha256, independent road_geometry_evidence_uri,
road_direction_evidence_note, and photo:
path, sha256, mime_type image/jpeg or image/png, and license.

The photo must be physically present under --photo-root: hash claims alone
are insufficient. Photos are never uploaded to Git or copied into the APK.
Road proximity <=100m is ONLY a gross geometry consistency check, not a
determination of legal effect, which side of the carriageway faces the
driver, or the truthfulness of a measured coordinate. An OSM way never
supplies a physical sign point.

Each speed entry must have review_id, source osm_way_id, explicit speed_kmh
(not derived from maxspeed), vehicle_class, forward/backward direction,
observed_at, reviewed_at, inspector and independent reviewer, evidence_uri,
road_geometry plus hash and independent evidence URI, road_context
(inside_built_up_area boolean, divided/undivided/oneway carriageway_type,
observed/none_confirmed posted_sign_status), sign_evidence_ids array and
sign_applicability_note. Its legal section requires document_id, clause,
official_uri (.gov.vn or vbpl.vn), effective_from, checked_at and a
substantive applicability_note. Law effective date must be no later than
the actual observation. An official link is ONLY a citation; it does NOT
automatically prove law applicability at the road position/date/direction.


If posted_sign_status is observed, sign_evidence_ids MUST point to complete
sign entries in the same evidence packet for the same OSM way and travel
direction. References to rejected, absent or contradictory signs fail the speed
packet. A none_confirmed status must NOT simultaneously provide sign IDs.
Even a syntactically consistent match still requires field/independent review.

Hashes for LineString JSON are SHA-256 over UTF-8 of
json.dumps(geometry, ensure_ascii=False, sort_keys=True,
separators=(",", ":"), allow_nan=False). Time fields use full ISO-8601 with
timezone offset, including +07:00 or Z.

The current official legal research sources include:
- https://congbao.chinhphu.vn/van-ban/van-ban-hop-nhat-so-74-2026-vbhn-tt-bxd-470578.htm
  (74/2026/VBHN-TT-BXD, 2026-09-15).
- https://congbao.chinhphu.vn/van-ban/thong-tu-so-38-2024-tt-bgtvt-43378/53130.htm
  (38/2024/TT-BGTVT; original effective 2025-01-01).

Human reviewers must check the actual enacted rules, later amendments,
road category, vehicle, populated-area applicability, posted signs,
exceptions and each effective date. No general maximum speed is embedded
in the validator.

## Run (on a real independently collected packet)

    python3 scripts/review_road_field_evidence.py \
      --review-zip /safe/path/NaviTaxi_Vietnam_2026-11-12_Field_Sign_Speed_Review_UNVERIFIED.zip \
      --expected-review-zip-sha256 26891bd61d10cb6228f30db5201af275254832b0705a5c553731df7f24c7df7c \
      --evidence /safe/private/field-evidence.json \
      --photo-root /safe/private/photos \
      --out build/field-evidence-mechanical-audit.json

Inputs with a changed ZIP hash, original CSV approvals, missing photo bytes,
unbound review IDs, unverified legal context, invalid GPS or conflicts are
rejected. Each entry receives READY_FOR_HUMAN_REVIEW or REJECTED with reasons.
The overall report remains HUMAN_REVIEW_REQUIRED or REJECTED.
Every report fixes:
approved_legal_speeds = 0,
approved_physical_sign_coordinates = 0,
driver_alerts_allowed = false,
production_database_authorized = false.

These statuses refer only to **packet completeness** and cannot substitute
for independent human verification. A reviewer self-identification string
cannot prove review independence or authenticity. GPS/EXIF, photo provenance,
sign placement and direction, current legislation, source permissions, line
geometry authority, conflicts and case-specific decisions still require
human/field adjudication.

## Tested scope and open blockers

All test inputs are explicitly synthetic XML/GPS/photos and invented legal
identifiers; test numbers must NEVER be shipped as real speed limits.
Regression coverage includes evidence binding, ZIP SHA-256, WGS84, direction,
GPS accuracy, photos and checksum, field sign code, legal source/effective
date, road context, duplicate records and no automatic approval.

No new Android dependencies, speed database, field-survey photographs or
untrusted authority pins are committed. The next safe steps are real field
surveys under a lawful license, independent human legal review,
source/geometry reconciliation, SQLite schema/RTree and checksum audit,
a separately approved release pin and on-device driving tests.


## Conflict quarantine hardening (2026-11-15; PR pending)

The mechanical auditor now fail-closes on **all affected records** when
multiple sign observations share the same OSM review ID, reuse the exact
photo SHA-256, or claim the same sign code within three metres. Previously
the first candidate could still appear ready after a later conflict.
When a trusted-by-structure speed paper cites any quarantined sign, its
mechanical status is also rejected. Duplicated speed scope
(OSM way, direction, vehicle class) is quarantined, not resolved by
file order. The output never asserts the truth of a GPS reading, photo,
legal rule or reviewer identity.

An observed speed-sign reference must use the same independently supplied
road geometry digest as the sign evidence, the same OSM way/direction,
and a sign survey observed **no later than** the speed observation.
A sign first seen after a speed inspection cannot establish the earlier
speed limit. The geometry digest is self-reported and remains subject
to independent source verification.

The legal checked_at timestamp must fall between observed_at and reviewed_at;
an optional legal.effective_to ISO date, when supplied, must not predate
the road observation. A legal URL and its timestamp alone do not
authenticate the source's actual contents, repeal history, sign
applicability or legal limit.

Any input key that attempts to declare a driver/database approval
(e.g. driver_alerts_allowed, independently_verified or
production_database_authorized) is rejected even when nested.
Empty packets yield NO_EVIDENCE_TO_REVIEW, not HUMAN_REVIEW_REQUIRED.

The review ZIP, independent photos and current-law evidence are still
external sources. CI uses synthetic data only; no real legal speed or
sign coordinates are approved, and Android allowlist remains empty.
