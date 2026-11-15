#!/usr/bin/env python3
"""Build non-authorizing field/legal REVIEW QUEUES from audited OSM references.

Every source object remains unverified. Survey and legal-evidence columns are
blank by design. No road law, physical sign location, speed_kmh, SQLite
approval, APK asset or driver alert is generated.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

from audit_osm_reference_quality import audit_reference

FORMAT = "navitaxi-road-intelligence-review-queues/v1"
SIGN_FILE = "traffic_sign_field_survey_queue.csv"
SPEED_FILE = "speed_limit_legal_review_queue.csv"
GUIDE_FILE = "REVIEW_INSTRUCTIONS.txt"

# Official legal-text portal is a research link ONLY, never a site-specific
# speed or sign-code approval. No actual legal limits are embedded here.
LEGAL_REFERENCE = (
    "https://congbao.chinhphu.vn/van-ban/"
    "van-ban-hop-nhat-so-74-2026-vbhn-tt-bxd-470578/68818.htm"
)
SIGN_COLUMNS = (
    "review_id", "osm_type", "osm_id", "osm_version", "osm_timestamp",
    "raw_traffic_sign", "raw_osm_tags_json", "osm_latitude_unverified",
    "osm_longitude_unverified", "triage_bucket", "survey_latitude_BLANK",
    "survey_longitude_BLANK", "survey_bearing_degrees_BLANK",
    "survey_accuracy_m_BLANK", "survey_date_BLANK", "photo_sha256_BLANK",
    "sign_code_reviewed_BLANK", "road_direction_reviewed_BLANK",
    "survey_reviewer_BLANK", "independent_evidence_uri_BLANK",
    "review_status", "independently_verified", "driver_alert_approved"
)
SPEED_COLUMNS = (
    "review_id", "osm_way_id", "osm_version", "osm_timestamp",
    "raw_maxspeed", "raw_highway", "raw_name", "raw_osm_tags_json",
    "triage_bucket", "vehicle_class_reviewed_BLANK",
    "direction_reviewed_BLANK", "legal_clause_BLANK",
    "legal_source_uri_BLANK", "effective_date_BLANK",
    "field_sign_evidence_ids_BLANK", "observed_date_BLANK",
    "verified_date_BLANK", "independent_reviewer_BLANK",
    "review_status", "independently_verified", "driver_alert_approved"
)
EMPTY_FIELDS_SIGN = tuple(k for k in SIGN_COLUMNS if k.endswith("_BLANK"))
EMPTY_FIELDS_SPEED = tuple(k for k in SPEED_COLUMNS if k.endswith("_BLANK"))
GUIDE = """NAVITAXI ROAD INTELLIGENCE - UNVERIFIED REVIEW QUEUES
Source: © OpenStreetMap contributors, ODbL-1.0. Preserve original attribution.
CSV values are UTF-8 with protection against spreadsheet formula injection.
DO NOT import these CSV files into road_intelligence.db or APK assets.

OSM node coordinates are UNVERIFIED volunteered map coordinates; these
are NOT surveyed roadside sign positions. An OSM sign on a way/relation
has NO physical point, so its coordinate columns MUST stay blank.
A traffic_sign=yes tag does not identify the sign type.

Speed way IDs and maxspeed tags are UNVERIFIED references only. The review
CSV intentionally does NOT contain legal speed_kmh or road geometry.
Check each segment's law, date, posted signs, vehicle class, direction,
conditional applicability, geometry and original OSM license separately.
Official text for MANUAL legal research (not default speed authorization):
https://congbao.chinhphu.vn/van-ban/van-ban-hop-nhat-so-74-2026-vbhn-tt-bxd-470578/68818.htm

All reviewer/evidence columns were generated BLANK. review_status is
PENDING_INDEPENDENT_REVIEW; independently_verified and driver_alert_approved
are ALWAYS FALSE. Filling these CSV columns does NOT make a DB trusted or
enable any app alerts. Published DB requires independent source/field/legal
review, human approval and an exact code-reviewed release SHA.
"""


class ReviewQueueError(ValueError):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for data in iter(lambda: handle.read(128 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def _safe_csv(value) -> str:
    """Even quoted CSV spreadsheet cells can execute formulas when opened."""
    text = "" if value is None else str(value)
    text = text.replace("\x00", "").replace("\r", " ").replace("\n", " ")
    stripped = text.lstrip(" \t")
    if stripped and stripped[0] in "=+-@":
        return "'" + text
    return text


def _safe_output(path: Path, reference: Path) -> Path:
    path = path.resolve()
    if path == reference or path in reference.parents or reference in path.parents:
        raise ReviewQueueError("Review output cannot overwrite source reference")
    if any(root in str(path) for root in (
            "/app/src/main/assets/", "/app/src/main/res/",
            "/data/road_intelligence/")):
        raise ReviewQueueError("Review output cannot enter app or verified road DB")
    return path


def _sign_bucket(row: dict) -> str:
    if row["osm"]["type"] != "node" or row["osm_node_coordinate"] is None:
        return "NO_VERIFIED_PHYSICAL_POINT"
    raw = row["tags"].get("traffic_sign", "").strip().lower()
    return ("SIGN_TYPE_UNKNOWN" if raw in ("", "yes", "unknown")
            else "SPECIFIC_OSM_TAG_NEEDS_FIELD_SURVEY")


def _speed_bucket(row: dict) -> str:
    tags = row["tags"]
    if "maxspeed" not in tags:
        return "NO_PRIMARY_MAXSPEED_TAG"
    if any(("conditional" in k or "advisory" in k or
            "forward" in k or "backward" in k) for k in tags):
        return "CONTEXTUAL_DIRECTIONAL_OR_ADVISORY"
    if re.fullmatch("[0-9]+", tags["maxspeed"]):
        return "PLAIN_INTEGER_TAG_NOT_LEGAL_VERIFICATION"
    return "NON_NUMERIC_OR_NON_STANDARD_OSM_TAG"


def _rows(reference: Path, filename: str):
    with (reference / filename).open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def _sign_record(row: dict) -> dict:
    obj, tags = row["osm"], row["tags"]
    coordinate = row["osm_node_coordinate"]
    return {
        "review_id": f"osm:{obj['type']}:{obj['id']}@{obj['version']}",
        "osm_type": obj["type"], "osm_id": obj["id"],
        "osm_version": obj["version"], "osm_timestamp": obj["timestamp"],
        "raw_traffic_sign": tags.get("traffic_sign", ""),
        "raw_osm_tags_json": json.dumps(tags, ensure_ascii=False, sort_keys=True),
        "osm_latitude_unverified": coordinate["latitude"] if coordinate else "",
        "osm_longitude_unverified": coordinate["longitude"] if coordinate else "",
        "triage_bucket": _sign_bucket(row),
        "review_status": "PENDING_INDEPENDENT_REVIEW",
        "independently_verified": "FALSE", "driver_alert_approved": "FALSE",
    }


def _speed_record(row: dict) -> dict:
    obj, tags = row["osm"], row["tags"]
    return {
        "review_id": f"osm:way:{obj['id']}@{obj['version']}",
        "osm_way_id": obj["id"], "osm_version": obj["version"],
        "osm_timestamp": obj["timestamp"],
        "raw_maxspeed": tags.get("maxspeed", ""),
        "raw_highway": tags.get("highway", ""), "raw_name": tags.get("name", ""),
        "raw_osm_tags_json": json.dumps(tags, ensure_ascii=False, sort_keys=True),
        "triage_bucket": _speed_bucket(row),
        "review_status": "PENDING_INDEPENDENT_REVIEW",
        "independently_verified": "FALSE", "driver_alert_approved": "FALSE",
    }


def _write_csv(file: Path, columns: tuple, records, buckets: Counter) -> int:
    count = 0
    with file.open("x", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=columns,
                                extrasaction="raise", quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for entry in records:
            row = {key: _safe_csv(entry.get(key, "")) for key in columns}
            if any(row[k] for k in columns if k.endswith("_BLANK")):
                raise ReviewQueueError("Survey/legal review fields may not be prefilled")
            if (row["review_status"] != "PENDING_INDEPENDENT_REVIEW" or
                    row["independently_verified"] != "FALSE" or
                    row["driver_alert_approved"] != "FALSE"):
                raise ReviewQueueError("A candidate cannot authorize driver alerts")
            writer.writerow(row)
            buckets[row["triage_bucket"]] += 1
            count += 1
    return count


def build_review_queues(reference_dir: Path, output_dir: Path,
                        receipt_path: Path | None = None,
                        archive: Path | None = None) -> dict:
    reference_dir = reference_dir.resolve()
    output_dir = _safe_output(output_dir, reference_dir)
    if archive is not None:
        archive = _safe_output(archive, reference_dir)
        if archive.exists() or archive == output_dir or output_dir in archive.parents:
            raise ReviewQueueError("Review archive must be new and outside its output")
    # This SHA/source/row-count/coordinate gate is REQUIRED before writing.
    quality = audit_reference(reference_dir, receipt_path)
    if quality["verified_legal_speed_records"] != 0 or (
            quality["verified_physical_sign_coordinates"] != 0):
        raise ReviewQueueError("Source reference falsely contains approved data")
    source_manifest = reference_dir / "manifest.json"
    output_dir.mkdir(parents=True, exist_ok=False)
    try:
        sign_buckets, speed_buckets = Counter(), Counter()
        sign_count = _write_csv(
            output_dir / SIGN_FILE, SIGN_COLUMNS,
            (_sign_record(r) for r in _rows(reference_dir, "traffic_sign_candidates.jsonl")),
            sign_buckets)
        speed_count = _write_csv(
            output_dir / SPEED_FILE, SPEED_COLUMNS,
            (_speed_record(r) for r in _rows(reference_dir, "speed_way_candidates.jsonl")),
            speed_buckets)
        claimed = quality["counts"]
        if sign_count != sum(claimed[k] for k in
                             ("sign_node_candidates", "sign_way_candidates",
                              "sign_relation_candidates")):
            raise ReviewQueueError("Sign review queue lost source candidates")
        if speed_count != claimed["speed_way_candidates"]:
            raise ReviewQueueError("Speed review queue lost source candidates")
        (output_dir / GUIDE_FILE).write_text(GUIDE, encoding="utf-8")
        files = {
            name: {"size_bytes": (output_dir / name).stat().st_size,
                   "sha256": _sha256(output_dir / name)}
            for name in (SIGN_FILE, SPEED_FILE, GUIDE_FILE)
        }
        result = {
            "format": FORMAT,
            "status": "REVIEW_QUEUES_ONLY_NO_FIELD_OR_LEGAL_APPROVAL",
            "source_snapshot": quality["source_snapshot"],
            "reference_manifest_sha256": _sha256(source_manifest),
            "source_candidate_counts": claimed,
            "review_rows": {"signs": sign_count, "speed_ways": speed_count},
            "sign_triage": dict(sorted(sign_buckets.items())),
            "speed_triage": dict(sorted(speed_buckets.items())),
            "files": files,
            "official_legal_research_url_only": LEGAL_REFERENCE,
            "survey_field_entries_present": 0,
            "independently_approved_speed_records": 0,
            "independently_surveyed_physical_signs": 0,
            "driver_alerts_allowed": False,
            "review_packets_are_not_production_databases": True,
        }
        manifest = output_dir / "manifest.json"
        manifest.write_text(json.dumps(result, ensure_ascii=False,
                                       indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        if archive is not None:
            archive.parent.mkdir(parents=True, exist_ok=True)
            try:
                with zipfile.ZipFile(archive, "x",
                                     compression=zipfile.ZIP_DEFLATED) as z:
                    names = ("manifest.json", SIGN_FILE, SPEED_FILE, GUIDE_FILE)
                    for name in names:
                        z.write(output_dir / name, name)
                    z.writestr("SHA256SUMS", "".join(
                        f"{_sha256(output_dir / name)}  {name}\n" for name in names))
            except BaseException:
                archive.unlink(missing_ok=True)
                raise
        return result
    except BaseException:
        shutil.rmtree(output_dir)
        raise


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reference-dir", type=Path, required=True)
    ap.add_argument("--receipt", type=Path)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--archive", type=Path)
    args = ap.parse_args()
    result = build_review_queues(args.reference_dir, args.output_dir,
                                 args.receipt, args.archive)
    print(json.dumps({
        "status": result["status"],
        "review_rows": result["review_rows"],
        "sign_triage": result["sign_triage"],
        "speed_triage": result["speed_triage"],
        "driver_alerts_allowed": False
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
