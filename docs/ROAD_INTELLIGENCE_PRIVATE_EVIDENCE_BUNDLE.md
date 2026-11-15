# Road Intelligence — PRIVATE field-evidence archive (Phase 11)

**Status: mechanical review only.** The portable ZIP does not establish Vietnamese legal speed limits, physical roadside sign positions or permission to alert drivers.

## Exact ZIP layout

The tool archives a separately supplied, SHA-256-pinned, UNVERIFIED OpenStreetMap review queue plus independently collected evidence packet and photograph bytes.

    MANIFEST.json
    SHA256SUMS
    source/unverified_osm_review_queue.zip
    evidence/independent_packet.json
    audit/mechanical_review_report.json
    photos/<safe-relative-input-photo-path>

MANIFEST.json uses format navitaxi-private-field-evidence-bundle/v1; its entries array contains each ZIP-internal path, size in bytes and SHA-256. SHA256SUMS includes all members except itself. A deterministic sort order, fixed ZIP member timestamps and modes, and DEFLATE compression guarantee byte-for-byte repeatability for the same input bytes.

The source review ZIP is archived **unaltered** and its expected SHA-256 is checked before packaging. Every included photo is copied unchanged after the existing independent survey-audit checks. Symlinks, path traversal, absolute paths, control characters, name collisions, duplicate members, corrupt checksums and unsafe sizes are rejected. Only nonempty packets with ZERO mechanically rejected entries may be packaged.

The archive holds private investigation information and potentially sensitive photos. Do not commit, upload, or distribute actual evidence without express permissions and a legitimate retention/access policy. The Python tool makes no network requests and does not add any photograph or real road data to Git, CI, Android assets or production road databases.

## Create a private evidence ZIP

The original Vietnam reference review ZIP from the 2026-11-12 Geofabrik source must be supplied separately. Its exact expected checksum is:

    26891bd61d10cb6228f30db5201af275254832b0705a5c553731df7f24c7df7c

This 1,170,686-byte UNVERIFIED review queue is NOT stored in the repository or shipped in the APK.

    python3 scripts/package_field_evidence.py \
      --review-zip /safe/review/NaviTaxi_Vietnam_2026-11-12_Field_Sign_Speed_Review_UNVERIFIED.zip \
      --expected-review-zip-sha256 26891bd61d10cb6228f30db5201af275254832b0705a5c553731df7f24c7df7c \
      --evidence /safe/private/field-evidence.json \
      --photo-root /safe/private/photos \
      --out /safe/private/NaviTaxi_FIELD_EVIDENCE_UNAPPROVED.zip

The output contains the exact archive path, total bytes, SHA-256, photo count, mechanical review status and ZERO approvals or driver warnings. **Store the printed outer ZIP SHA-256 independently before transfer to a human reviewer.** Output files cannot overwrite existing paths or enter Android asset/resource, production DB or photo-source folders.

## Independently verify a transferred archive

    python3 scripts/package_field_evidence.py \
      --verify /safe/incoming/NaviTaxi_FIELD_EVIDENCE_UNAPPROVED.zip \
      --expected-archive-sha256 <64-lowercase-hex-from-independent-channel>

The verifier checks the externally supplied SHA-256 of the **whole ZIP**, exact member list and types, ZIP size limits, all member digests and SHA256SUMS. It then extracts into a private temporary directory using checked relative paths and re-runs the genuine field-evidence auditor against the archived source ZIP, evidence packet, and photos. A forged mechanical report fails even if the attacker recalculates internal member hashes.

An attacker who controls both the external expected hash and ZIP can falsify the whole package. SHA-256 cannot authenticate a human, legal opinion, surveyed roadside sign, actual position/bearing, legal applicability, photographer copyright ownership or real-world event time.

## Legal and production boundaries

- The dated Vietnam OSM PBF reference source is 332,558,874 bytes, SHA256 ddb9155f112af521d0674e4f40b87173f92954e5b8a3f71445d3008b506ef9ed, ODbL-1.0 © OpenStreetMap contributors. The original PBF is not archived here.
- OSM reference candidates are 811 sign-tag objects and 44,472 speed-tagged ways; ZERO are accepted as independently surveyed physical sign points or enforceable site-specific legal speed records.
- Actual GPS instrument accuracy, original photo provenance, travel direction, road shape and governing legal texts/effective dates need independent human examination. No maxspeed tag or sign node may be promoted automatically.
- Manifest, audit report and CLI output always set approved_legal_speeds=0, approved_physical_sign_coordinates=0 and driver_alerts_allowed=false; production_database_authorized=false. Android RoadIntelligenceApprovedPins.entries remains EMPTY.
- The additional ZIP is not a code-reviewed production SQLite candidate, not a trust pin and not a licence to distribute photos. ODbL derivative-database and independent photo permissions still require review.
- Rejected evidence remains available for diagnosis via scripts/review_road_field_evidence.py, but cannot be packaged as mechanically review-ready without correcting inconsistencies.

## Synthetic-only acceptance

    python3 -m unittest discover -s tests -v

Automated tests create synthetic XML/OSM references, fake legal identities and a synthetic JPEG signature only. They cover deterministic ZIP checksums, required source pins, missing images, path traversal, photo-symlink refusal, nonempty review, tampered image bytes, external digest mismatch, and a forged report with recomputed SHA256SUMS. They never create real legal speeds or surveyed sign coordinates.


## PR #27 — mandatory private-photo minimization and real survey timestamps
- The source tree is an absolute privacy exclusion: NEVER set `--out` anywhere
  under the repository (including `build/`, `docs/`, `tests/`, untracked
  directories or Android resources); also NEVER within `--photo-root`.
  A private archive should live outside Git in an access-controlled directory.
- In `--verify`, the photo member set MUST equal the set of original
  `sign_evidence[*].photo.path` names inside the archived JSON. A surplus
  photo is rejected even when the attacker has recomputed `MANIFEST.json`,
  `SHA256SUMS` and the outer ZIP SHA-256. This prevents a ZIP with unrelated
  private photographs from being falsely passed as a complete sign survey.
- Exact manifest and file-entry key sets are required; unexpected fields
  claiming authority cannot be hidden in those records. The evidence JSON
  is limited to 80 MB and each photograph to 30 MB before ZIP extraction.
- Field survey and legal observation/review timestamps cannot be more than
  five minutes ahead of the auditor's UTC clock (minimal device clock-skew
  allowance, **not** evidence of real observation). This tolerance does
  not authenticate GPS, EXIF, photo subject, sign placement, legal clause
  or human independence.
- All checks remain a HUMAN-REVIEW-ONLY screen, with zero legally approved
  speed records, zero verified roadside sign coordinates and zero alerts.
