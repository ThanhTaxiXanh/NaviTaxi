#!/usr/bin/env python3
"""Audit independent field/legal EVIDENCE PACKETS; NEVER approve driver alerts.

Inputs are a SHA256-pinned, unverified OSM review ZIP and separately collected
observations. Passing means only mechanically complete for HUMAN review.
Neither source tags nor this script can approve a production SQLite database.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit
import zipfile
from xml.etree import ElementTree as ET

from build_road_review_queues import SIGN_COLUMNS, SPEED_COLUMNS, SIGN_FILE, SPEED_FILE

FORMAT = "navitaxi-independent-road-evidence/v1"
QUEUE_FORMAT = "navitaxi-road-intelligence-review-queues/v1"
SHA = re.compile(r"[0-9a-f]{64}\Z")
SIGN_CODE = re.compile(r"(?:[A-Z]{1,3})\.[0-9]{2,3}[a-z]?\Z")
# A source OSM way may legitimately require separate human speed reviews for
# forward/backward travel and each of the six supported vehicle classes.
SPEED_CASE_ID = re.compile(r"[A-Za-z0-9._:@-]{1,128}\Z")
MAX_FILE = 80_000_000
MAX_ROWS = 100_000
MAX_SPEED_SCOPES_PER_WAY = 12  # 2 travel directions x 6 vehicle classes
MAX_GPX_BYTES = 2_000_000
MAX_GPX_POINTS = 10_000
GPS_TIME_WINDOW_SECONDS = 15 * 60
GPX_NS = "{http://www.topografix.com/GPX/1/1}"
EXPECTED_ZIP = {
    "manifest.json", SIGN_FILE, SPEED_FILE, "REVIEW_INSTRUCTIONS.txt", "SHA256SUMS"
}

# Incoming survey paperwork cannot carry a user-supplied approval decision.
# Production authorization is confined to the independently reviewed Kotlin
# source-code SHA pins; even FALSE approval claims in input are out of scope.
UNTRUSTED_AUTHORIZATION_KEYS = frozenset({
    "driver_alert_approved", "driver_alerts_allowed", "traffic_sign_alerts_allowed",
    "approved_legal_speeds", "approved_physical_sign_coordinates",
    "production_database_authorized", "approval_pin_created",
    "independently_verified", "legally_or_physically_verified",
    "approved_speeds", "approved_signs", "approval_status", "trust_pin",
})


class EvidenceError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, reason: str):
    if not condition:
        raise EvidenceError(reason)


def read_json(data: bytes):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=unique,
                          parse_constant=lambda _: require(False, "NONFINITE_JSON"))
    except (UnicodeError, ValueError, TypeError) as exc:
        raise EvidenceError("INVALID_JSON: " + str(exc)) from exc


def https(url, official=False):
    if not isinstance(url, str):
        return False
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    if p.scheme != "https" or not host or p.username or p.password or p.fragment:
        return False
    if host in ("openstreetmap.org", "www.openstreetmap.org") or host.endswith(".openstreetmap.org"):
        return False  # OSM reference is not independent field/legal evidence
    return (not official or host.endswith(".gov.vn") or host == "vbpl.vn"
            or host == "chinhphu.vn" or host.endswith(".chinhphu.vn"))


def reject_authorization_claims(value):
    """Reject attempted promotion of a source/evidence document into approval."""
    if isinstance(value, dict):
        for key, child in value.items():
            require(key not in UNTRUSTED_AUTHORIZATION_KEYS,
                    "INPUT_ATTEMPTS_TO_AUTHORIZE_DRIVER_DATA")
            reject_authorization_claims(child)
    elif isinstance(value, list):
        for child in value:
            reject_authorization_claims(child)


def date_at(value):
    require(isinstance(value, str), "MISSING_DATE")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError("INVALID_TIMESTAMP") from exc
    require(result.tzinfo is not None and result.utcoffset() is not None,
            "TIMESTAMP_REQUIRES_TIMEZONE")
    require(datetime(2020, 1, 1, tzinfo=timezone.utc) <= result.astimezone(timezone.utc)
            <= datetime.now(timezone.utc) + timedelta(minutes=5), "TIMESTAMP_OUT_OF_RANGE")
    return result


def number(value, low, high):
    require(type(value) in (int, float) and math.isfinite(value)
            and low <= value <= high, "INVALID_NUMERIC_RANGE")
    return float(value)


def point(lat, lon):
    number(lat, -90, 90)
    number(lon, -180, 180)


def line_geometry(raw):
    require(isinstance(raw, dict) and raw.get("type") == "LineString",
            "MISSING_INDEPENDENT_LINESTRING")
    coords = raw.get("coordinates")
    require(isinstance(coords, list) and 2 <= len(coords) <= 20000,
            "INVALID_ROAD_GEOMETRY")
    for p in coords:
        require(isinstance(p, list) and len(p) == 2, "INVALID_ROAD_VERTEX")
        point(p[1], p[0])
    require(any(p != coords[0] for p in coords[1:]), "DEGENERATE_ROAD_GEOMETRY")
    return coords


def geometry_digest(raw):
    return digest(json.dumps(raw, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8"))


def nearest_road_m(lat, lon, coords):
    # Geometric plausibility only; does NOT validate the sign's legal direction.
    cos_lat = max(0.01, math.cos(math.radians(lat)))
    xy = [((p[0] - lon) * 111320 * cos_lat, (p[1] - lat) * 110540)
          for p in coords]
    smallest = float("inf")
    for (ax, ay), (bx, by) in zip(xy, xy[1:]):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, -(ax * dx + ay * dy) / (dx * dx + dy * dy))) if (dx or dy) else 0
        smallest = min(smallest, math.hypot(ax + t * dx, ay + t * dy))
    return smallest


def read_queue(archive_path: Path, expected_sha: str):
    require(SHA.fullmatch(expected_sha) is not None, "INVALID_EXPECTED_ZIP_SHA256")
    require(archive_path.is_file() and archive_path.stat().st_size <= MAX_FILE,
            "MISSING_OR_OVERSIZED_REVIEW_ZIP")
    require(digest(archive_path.read_bytes()) == expected_sha, "REVIEW_ZIP_SHA256_MISMATCH")
    with zipfile.ZipFile(archive_path) as z:
        require(set(z.namelist()) == EXPECTED_ZIP
                and len(z.infolist()) == len(EXPECTED_ZIP), "UNEXPECTED_REVIEW_ZIP_MEMBERS")
        for info in z.infolist():
            require(info.file_size <= MAX_FILE and info.compress_type == zipfile.ZIP_DEFLATED,
                    "UNSAFE_REVIEW_ZIP_MEMBER")
        data = {name: z.read(name) for name in EXPECTED_ZIP}
    manifest = read_json(data["manifest.json"])
    require(isinstance(manifest, dict) and manifest.get("format") == QUEUE_FORMAT
            and manifest.get("status") == "REVIEW_QUEUES_ONLY_NO_FIELD_OR_LEGAL_APPROVAL",
            "NOT_AN_UNVERIFIED_REVIEW_QUEUE")
    for key in ("independently_approved_speed_records",
                "independently_surveyed_physical_signs", "survey_field_entries_present"):
        require(manifest.get(key) == 0, "QUEUE_CLAIMS_APPROVAL")
    require(manifest.get("driver_alerts_allowed") is False
            and manifest.get("review_packets_are_not_production_databases") is True,
            "QUEUE_CLAIMS_DRIVER_ALERTS")
    checks = {}
    for entry in data["SHA256SUMS"].decode("utf-8").splitlines():
        parts = entry.split("  ", 1)
        require(len(parts) == 2 and parts[1] in EXPECTED_ZIP - {"SHA256SUMS"}
                and parts[1] not in checks, "INVALID_SHA256SUMS")
        checks[parts[1]] = parts[0]
    require(set(checks) == EXPECTED_ZIP - {"SHA256SUMS"}, "MISSING_SHA256SUMS")
    for name, checksum in checks.items():
        require(SHA.fullmatch(checksum) is not None and digest(data[name]) == checksum,
                "REVIEW_MEMBER_CHECKSUM_MISMATCH")
        if name in (SIGN_FILE, SPEED_FILE, "REVIEW_INSTRUCTIONS.txt"):
            entry = manifest.get("files", {}).get(name, {})
            require(entry.get("sha256") == checksum and
                    entry.get("size_bytes") == len(data[name]),
                    "REVIEW_MANIFEST_MISMATCH")

    def rows(name, columns, count_key):
        require(len(data[name]) <= MAX_FILE, "OVERSIZED_CSV")
        stream = io.StringIO(data[name].decode("utf-8"), newline="")
        reader = csv.DictReader(stream, strict=True)
        require(tuple(reader.fieldnames or ()) == columns, "REVIEW_CSV_SCHEMA_MISMATCH")
        result = {}
        for row in reader:
            require(len(result) < MAX_ROWS and None not in row, "INVALID_REVIEW_CSV_ROW")
            review_id = row["review_id"]
            require(review_id not in result, "DUPLICATE_REVIEW_ID")
            require(row["review_status"] == "PENDING_INDEPENDENT_REVIEW"
                    and row["independently_verified"] == "FALSE"
                    and row["driver_alert_approved"] == "FALSE",
                    "QUEUE_HAS_UNTRUSTED_APPROVAL_FLAGS")
            require(all(not row[k] for k in columns if k.endswith("_BLANK")),
                    "QUEUE_PREPOPULATED_SURVEY_FIELDS")
            result[review_id] = row
        require(len(result) == manifest.get("review_rows", {}).get(count_key),
                "QUEUE_CSV_COUNT_MISMATCH")
        return result

    return manifest, digest(data["manifest.json"]), (
        rows(SIGN_FILE, SIGN_COLUMNS, "signs"),
        rows(SPEED_FILE, SPEED_COLUMNS, "speed_ways"),
    )


def private_evidence_bytes(root: Path, rel: str, max_bytes: int, category: str):
    """Fail closed on linked paths, including symlinked ancestor components."""
    require(isinstance(rel, str) and rel and len(rel) <= 250
            and "\\" not in rel and ":" not in rel and
            not any(ord(c) < 32 or ord(c) == 127 for c in rel),
            "UNSAFE_" + category + "_PATH")
    candidate = Path(rel)
    require(not candidate.is_absolute() and
            all(part not in ("", ".", "..") for part in rel.split("/")),
            "UNSAFE_" + category + "_PATH")
    current = root
    require(root.is_dir() and not root.is_symlink(), "UNSAFE_PRIVATE_EVIDENCE_ROOT")
    for part in rel.split("/"):
        current = current / part
        require(not current.is_symlink(), "SYMLINKED_PRIVATE_EVIDENCE_PATH")
    require(current.resolve().is_relative_to(root.resolve())
            and current.is_file() and 0 < current.stat().st_size <= max_bytes,
            "MISSING_OR_OVERSIZED_" + category)
    with current.open("rb") as fh:
        raw = fh.read(max_bytes + 1)
    require(0 < len(raw) <= max_bytes, "MISSING_OR_OVERSIZED_" + category)
    return raw


def survey_photo(photo: dict, root: Path):
    require(isinstance(photo, dict), "PHOTO_REQUIRED")
    raw = private_evidence_bytes(root, photo.get("path"), 30_000_000, "PHOTO")
    mime = photo.get("mime_type")
    require((mime == "image/jpeg" and raw.startswith(b"\xff\xd8")
             or mime == "image/png" and raw.startswith(b"\x89PNG\r\n\x1a\n")),
            "PHOTO_FORMAT_MISMATCH")
    require(isinstance(photo.get("license"), str) and photo["license"].strip()
            and photo["license"].lower() != "unknown", "MISSING_PHOTO_LICENSE")
    require(SHA.fullmatch(str(photo.get("sha256"))) is not None
            and digest(raw) == photo["sha256"], "PHOTO_SHA256_MISMATCH")


def gps_track_alignment(track: dict, root: Path, lat: float, lon: float,
                        observed: datetime, accuracy_m: float):
    """Correlate supplied GPX points/time with claimed sign GPS. NOT proof of truth.

    Optional legacy-v1 supplement. Requires original GPX bytes, rather than
    accepting an unbacked GPS claim or an external URL as coordinates.
    """
    require(isinstance(track, dict) and track.get("mime_type") == "application/gpx+xml"
            and https(track.get("source_uri"))
            and isinstance(track.get("license"), str) and track["license"].strip()
            and track["license"].strip().lower() != "unknown",
            "INCOMPLETE_GNSS_TRACE_PROVENANCE")
    raw = private_evidence_bytes(root, track.get("path"), MAX_GPX_BYTES, "GPS_TRACK")
    require(SHA.fullmatch(str(track.get("sha256"))) is not None
            and digest(raw) == track["sha256"], "GPS_TRACK_SHA256_MISMATCH")
    require(b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(),
            "GPS_TRACK_XML_DTD_NOT_ALLOWED")
    try:
        document = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise EvidenceError("INVALID_GPS_TRACK_XML") from exc
    require(document.tag == GPX_NS + "gpx", "GPS_TRACK_REQUIRES_GPX_1_1")
    # Both attributes are mandatory in the official GPX 1.1 schema. A
    # namespace alone does not make a fragment an original GPX 1.1 export.
    require(document.attrib.get("version") == "1.1"
            and isinstance(document.attrib.get("creator"), str)
            and bool(document.attrib["creator"].strip()),
            "GPS_TRACK_MISSING_GPX_1_1_CREATOR_OR_VERSION")
    points = document.iter()
    count = 0
    aligned = False
    for node in points:
        if node.tag not in (GPX_NS + "trkpt", GPX_NS + "wpt", GPX_NS + "rtept"):
            continue
        count += 1
        require(count <= MAX_GPX_POINTS, "TOO_MANY_GPS_TRACK_POINTS")
        try:
            sample_lat = float(node.attrib["lat"])
            sample_lon = float(node.attrib["lon"])
        except (KeyError, TypeError, ValueError) as exc:
            raise EvidenceError("GPS_TRACK_INVALID_WGS84_POINT") from exc
        number(sample_lat, -90, 90)
        number(sample_lon, -180, 180)
        times = node.findall(GPX_NS + "time")
        require(len(times) == 1 and times[0].text, "GPS_TRACK_POINT_TIME_REQUIRED")
        sample_at = date_at(times[0].text.strip())
        # GPX 1.1 quality fields are optional. Absence is UNKNOWN, not proof
        # of a good fix. Explicitly failed/invalid fixes must NEVER be used to
        # corroborate a claimed physical sign position, even if coordinates
        # and timestamps appear to match.
        quality = {}
        for field in ("fix", "sat", "hdop"):
            values = node.findall(GPX_NS + field)
            require(len(values) <= 1, "GPS_TRACK_DUPLICATE_QUALITY_FIELD")
            quality[field] = values[0].text.strip() if values and values[0].text else None
            require(not values or quality[field], "GPS_TRACK_INVALID_QUALITY_FIELD")
        fix = quality["fix"]
        require(fix is None or fix in ("none", "2d", "3d", "dgps", "pps"),
                "GPS_TRACK_INVALID_FIX")
        satellites = None
        if quality["sat"] is not None:
            raw_sat = quality["sat"]
            require(raw_sat.isascii() and raw_sat.isdecimal() and len(raw_sat) <= 4,
                    "GPS_TRACK_INVALID_SATELLITE_COUNT")
            satellites = int(raw_sat)
        hdop = None
        if quality["hdop"] is not None:
            try:
                hdop = float(quality["hdop"])
            except ValueError as exc:
                raise EvidenceError("GPS_TRACK_INVALID_HDOP") from exc
            require(math.isfinite(hdop) and hdop >= 0, "GPS_TRACK_INVALID_HDOP")
        # 2D requires at least three satellites; 3D/DGPS/PPS require four.
        # Missing sat/HDOP fields do not prove fix quality: separate human
        # checking of the original receiver log remains mandatory.
        min_sat = 4 if fix in ("3d", "dgps", "pps") else 3
        usable_fix = (fix != "none"
                      and (satellites is None or satellites >= min_sat)
                      and (hdop is None or 0 < hdop <= 10))
        distance = math.hypot(
            (sample_lat - lat) * 110540,
            (sample_lon - lon) * 111320 * max(
                0.01, math.cos(math.radians((sample_lat + lat) / 2))))
        if (usable_fix and distance <= max(15.0, accuracy_m + 10.0) and
                abs((sample_at - observed).total_seconds()) <= GPS_TIME_WINDOW_SECONDS):
            aligned = True
    require(count > 0 and aligned, "GPS_TRACK_HAS_NO_USABLE_SIGN_FIX_TIME_POSITION_MATCH")




def independent_record(item, source, kind, photo_root):
    require(isinstance(item, dict), "INVALID_EVIDENCE_RECORD")
    require(item.get("review_id") in source, "UNKNOWN_SOURCE_REVIEW_ID")
    require(https(item.get("evidence_uri")), "INDEPENDENT_EVIDENCE_URI_REQUIRED")
    collector = item.get("surveyor" if kind == "sign" else "inspector")
    reviewer = item.get("reviewer")
    require(isinstance(collector, str) and collector.strip()
            and isinstance(reviewer, str) and reviewer.strip()
            and collector.strip().casefold() != reviewer.strip().casefold(),
            "REQUIRES_DIFFERENT_HUMAN_REVIEWER")
    observed = date_at(item.get("observed_at"))
    checked = date_at(item.get("reviewed_at"))
    require(checked >= observed, "REVIEW_PREDATES_OBSERVATION")
    geom = item.get("road_geometry")
    coords = line_geometry(geom)
    require(https(item.get("road_geometry_evidence_uri")),
            "INDEPENDENT_GEOMETRY_SOURCE_REQUIRED")
    require(item.get("road_geometry_sha256") == geometry_digest(geom),
            "ROAD_GEOMETRY_HASH_MISMATCH")
    require(item.get("direction") in ("forward", "backward"),
            "EXPLICIT_TRAVEL_DIRECTION_REQUIRED")
    if kind == "sign":
        require(SIGN_CODE.fullmatch(str(item.get("sign_code"))) is not None,
                "SPECIFIC_VIETNAM_SIGN_CODE_REQUIRED")
        require(type(item.get("related_osm_way_id")) is int
                and item["related_osm_way_id"] > 0, "RELATED_WAY_REQUIRED")
        lat = number(item.get("latitude"), -90, 90)
        lon = number(item.get("longitude"), -180, 180)
        accuracy_m = number(item.get("gps_accuracy_m"), 0.01, 25)
        number(item.get("bearing_degrees"), 0, 359.999999)
        if "gps_track" in item:
            gps_track_alignment(item["gps_track"], photo_root, lat, lon,
                                observed, accuracy_m)
        require(nearest_road_m(lat, lon, coords) <= 100,
                "SURVEY_POINT_NOT_NEAR_RELATED_ROAD")
        survey_photo(item.get("photo"), photo_root)
        require(item.get("road_direction_evidence_note")
                and len(str(item["road_direction_evidence_note"]).strip()) >= 12,
                "NO_DIRECTION_APPLICABILITY_EVIDENCE")
    else:
        require(type(item.get("speed_kmh")) is int
                and 1 <= item["speed_kmh"] <= 250, "EXPLICIT_SPEED_KMH_REQUIRED")
        require(type(item.get("osm_way_id")) is int and
                str(item["osm_way_id"]) == source[item["review_id"]]["osm_way_id"],
                "WAY_ID_MISMATCH")
        require(isinstance(item.get("vehicle_class"), str)
                and item["vehicle_class"] in ("motorcar", "bus", "hgv", "motorcycle",
                                             "taxi", "special_vehicle"),
                "VEHICLE_CLASS_REQUIRED")
        context = item.get("road_context")
        require(isinstance(context, dict) and
                type(context.get("inside_built_up_area")) is bool and
                context.get("posted_sign_status") in ("observed", "none_confirmed") and
                context.get("carriageway_type") in ("divided", "undivided", "oneway"),
                "ROAD_CONTEXT_NOT_INDEPENDENTLY_DETERMINED")
        legal = item.get("legal")
        require(isinstance(legal, dict) and https(legal.get("official_uri"), official=True)
                and isinstance(legal.get("document_id"), str)
                and legal["document_id"].strip()
                and isinstance(legal.get("clause"), str) and legal["clause"].strip()
                and isinstance(legal.get("applicability_note"), str)
                and len(legal["applicability_note"].strip()) >= 20,
                "INCOMPLETE_LEGAL_PROVENANCE")
        try:
            effective = date.fromisoformat(legal["effective_from"])
        except (ValueError, TypeError, KeyError) as exc:
            raise EvidenceError("LEGAL_EFFECTIVE_DATE_REQUIRED") from exc
        require(effective <= observed.date(), "LAW_NOT_EFFECTIVE_AT_OBSERVATION")
        if legal.get("effective_to") is not None:
            try:
                expires = date.fromisoformat(legal["effective_to"])
            except (ValueError, TypeError) as exc:
                raise EvidenceError("INVALID_LEGAL_EXPIRY_DATE") from exc
            require(expires >= observed.date(), "LAW_EXPIRED_AT_OBSERVATION")
        verified_law_at = date_at(legal.get("checked_at"))
        require(observed <= verified_law_at <= checked,
                "LEGAL_CHECK_MUST_FOLLOW_OBSERVATION_AND_PRECEDE_REVIEW")
        require(isinstance(item.get("sign_evidence_ids"), list)
                and all(isinstance(s, str) and s for s in item["sign_evidence_ids"]),
                "SIGN_RELEVANCE_LIST_REQUIRED")
        require(item.get("sign_applicability_note")
                and len(str(item["sign_applicability_note"]).strip()) >= 12,
                "SIGN_APPLICABILITY_EXPLANATION_REQUIRED")


def audit_evidence(queue_zip: Path, expected_queue_sha: str, evidence: Path,
                   photo_root: Path) -> dict:
    manifest, manifest_sha, (sign_rows, speed_rows) = read_queue(
        queue_zip, expected_queue_sha)
    require(evidence.is_file() and evidence.stat().st_size <= MAX_FILE,
            "INVALID_EVIDENCE_INPUT")
    evidence_raw = evidence.read_bytes()
    packet = read_json(evidence_raw)
    require(isinstance(packet, dict) and packet.get("format") == FORMAT
            and packet.get("source_review_manifest_sha256") == manifest_sha,
            "UNBOUND_EVIDENCE_PACKET")
    reject_authorization_claims(packet)
    report = {
        "format": "navitaxi-evidence-mechanical-audit/v1",
        "queue_zip_sha256": expected_queue_sha,
        "queue_manifest_sha256": manifest_sha,
        "evidence_sha256": digest(evidence_raw),
        "queue_records": manifest["review_rows"],
        "results": [],
        "ready_for_independent_human_review": 0,
        "rejected_records": 0,
        "approved_legal_speeds": 0,
        "approved_physical_sign_coordinates": 0,
        "driver_alerts_allowed": False,
        "production_database_authorized": False,
        "warning": "Complete paperwork is not proof of legal applicability or a surveyed sign.",
    }
    seen_signs = set()
    signs_seen = []
    speeds_seen = set()
    for kind, rows, key in (("sign", sign_rows, "sign_evidence"),
                             ("speed", speed_rows, "speed_evidence")):
        entries = packet.get(key)
        # Speed entries are a reviewed (way, direction, vehicle) scope, not
        # one packet per raw OSM way. Do not multiply the sign-photo queue.
        limit = len(rows) * (MAX_SPEED_SCOPES_PER_WAY if kind == "speed" else 1)
        require(isinstance(entries, list) and
                len(entries) <= min(MAX_ROWS, limit),
                "EVIDENCE_ARRAY_EXCEEDS_SOURCE_QUEUE")
        for item in entries:
            review_id = item.get("review_id") if isinstance(item, dict) else None
            case_id = (item.get("case_id", review_id) if
                       kind == "speed" and isinstance(item, dict) else None)
            reasons = []
            try:
                require(isinstance(review_id, str) and review_id,
                        "DUPLICATE_OR_MISSING_EVIDENCE_ID")
                if kind == "sign":
                    require(review_id not in seen_signs,
                            "DUPLICATE_OR_MISSING_EVIDENCE_ID")
                    seen_signs.add(review_id)
                else:
                    require(isinstance(case_id, str) and
                            SPEED_CASE_ID.fullmatch(case_id) is not None,
                            "INVALID_SPEED_CASE_ID")
                independent_record(item, rows, kind, photo_root)
                if kind == "sign":
                    coord = (item["latitude"], item["longitude"], item["sign_code"])
                    # Reject a repeated physical position/code, even if OSM IDs differ.
                    require(not any(code == coord[2] and math.hypot(
                        (lat - coord[0]) * 110540,
                        (lon - coord[1]) * 111320 * math.cos(math.radians(lat))) < 3
                        for lat, lon, code in signs_seen),
                        "POSSIBLE_DUPLICATE_PHYSICAL_SIGN")
                    signs_seen.append(coord)
                else:
                    k = (item["osm_way_id"], item["direction"], item["vehicle_class"])
                    require(k not in speeds_seen, "CONFLICTING_SPEED_SCOPE")
                    speeds_seen.add(k)
            except (EvidenceError, KeyError, TypeError) as exc:
                reasons.append(str(exc) or "INVALID_PACKET")
            accepted = not reasons
            finding = {
                "kind": kind, "review_id": review_id,
                "status": "READY_FOR_HUMAN_REVIEW" if accepted else "REJECTED",
                "reasons": reasons,
                "legally_or_physically_verified": False,
            }
            if kind == "speed":
                # A unique review case is NOT a unique OSM reference row.
                # The audit is still non-authorizing and needs human review.
                finding["case_id"] = case_id
            report["results"].append(finding)
            report["ready_for_independent_human_review" if accepted
                   else "rejected_records"] += 1
    # A later contradictory or duplicate record invalidates ALL potentially
    # matching candidates, never merely the second row in input order.
    # Use only provenance/identity for grouping: this does not establish field truth.
    def quarantine(result, reason):
        if reason not in result["reasons"]:
            result["reasons"].append(reason)
        if result["status"] != "REJECTED":
            result["status"] = "REJECTED"
            report["ready_for_independent_human_review"] -= 1
            report["rejected_records"] += 1

    by_id, by_photo = {}, {}
    sign_pairs = []
    speed_scope = {}
    speed_cases = {}
    speed_sources = {}
    sign_results = [x for x in report["results"] if x["kind"] == "sign"]
    speed_results = [x for x in report["results"] if x["kind"] == "speed"]
    for item, result in zip(packet["sign_evidence"], sign_results):
        if not isinstance(item, dict):
            continue
        sid = item.get("review_id")
        if isinstance(sid, str):
            by_id.setdefault(sid, []).append(result)
        photo = item.get("photo")
        if isinstance(photo, dict) and SHA.fullmatch(str(photo.get("sha256"))):
            by_photo.setdefault(photo["sha256"], []).append(result)
        lat, lon, code = item.get("latitude"), item.get("longitude"), item.get("sign_code")
        if (type(lat) in (float, int) and type(lon) in (float, int) and
                math.isfinite(lat) and math.isfinite(lon) and
                -90 <= lat <= 90 and -180 <= lon <= 180 and
                isinstance(code, str)):
            sign_pairs.append((float(lat), float(lon), code, result))
    for group in by_id.values():
        if len(group) > 1:
            for result in group:
                quarantine(result, "DUPLICATE_SIGN_SOURCE_ID")
    for group in by_photo.values():
        if len(group) > 1:
            for result in group:
                quarantine(result, "REUSED_SIGN_PHOTO_SHA256")
    # Actual source queue contains 811 sign candidates; small bounded
    # all-pairs scan avoids missed 3m overlaps at grid-cell boundaries.
    for i, (lat, lon, code, left) in enumerate(sign_pairs):
        for other_lat, other_lon, other_code, right in sign_pairs[i + 1:]:
            if code == other_code and math.hypot(
                    (lat - other_lat) * 110540,
                    (lon - other_lon) * 111320 *
                    max(0.01, math.cos(math.radians((lat + other_lat) / 2)))) < 3:
                quarantine(left, "POSSIBLE_DUPLICATE_PHYSICAL_SIGN")
                quarantine(right, "POSSIBLE_DUPLICATE_PHYSICAL_SIGN")
    for item, result in zip(packet["speed_evidence"], speed_results):
        if not isinstance(item, dict):
            continue
        source_id = item.get("review_id")
        if isinstance(source_id, str):
            speed_sources.setdefault(source_id, []).append((item, result))
        case_id = result.get("case_id")
        if isinstance(case_id, str):
            speed_cases.setdefault(case_id, []).append(result)
        scope = (item.get("osm_way_id"), item.get("direction"),
                 item.get("vehicle_class"))
        if type(scope[0]) is int and all(isinstance(v, str) for v in scope[1:]):
            speed_scope.setdefault(scope, []).append(result)
    for group in speed_cases.values():
        if len(group) > 1:
            for result in group:
                quarantine(result, "DUPLICATE_SPEED_CASE_ID")
    for source_id, group in speed_sources.items():
        if len(group) > MAX_SPEED_SCOPES_PER_WAY:
            for _, result in group:
                quarantine(result, "TOO_MANY_SPEED_SCOPES_PER_SOURCE_WAY")
        if len(group) > 1 and any(
                not isinstance(item.get("case_id"), str) for item, _ in group):
            # Do not allow implicit legacy case IDs when a source OSM way
            # is split into multiple independently reviewed legal scopes.
            for _, result in group:
                quarantine(result, "REPEATED_SPEED_SOURCE_REQUIRES_CASE_ID")
    for group in speed_scope.values():
        if len(group) > 1:
            for result in group:
                quarantine(result, "CONFLICTING_SPEED_SCOPE")

    # Speed paperwork must never cite an unreviewed, unrelated or differently
    # directed sign merely by writing its ID into a text array.
    sign_packets = {
        item.get("review_id"): item for item in packet["sign_evidence"]
        if isinstance(item, dict) and isinstance(item.get("review_id"), str)
    }
    sign_ready = {
        result["review_id"] for result in report["results"]
        if result["kind"] == "sign" and result["status"] == "READY_FOR_HUMAN_REVIEW"
    }
    speed_results = [result for result in report["results"]
                     if result["kind"] == "speed"]
    for result, item in zip(speed_results, packet["speed_evidence"]):
        if result["status"] != "READY_FOR_HUMAN_REVIEW":
            continue
        ids = item["sign_evidence_ids"]
        posted = item["road_context"]["posted_sign_status"]
        problem = None
        if posted == "none_confirmed" and ids:
            problem = "NO_POSTED_SIGN_BUT_SIGN_IDS_PRESENT"
        elif posted == "observed":
            if not ids or len(set(ids)) != len(ids):
                problem = "OBSERVED_SIGN_IDS_REQUIRED_UNIQUE"
            elif any(s not in sign_ready or s not in sign_packets
                     or sign_packets[s].get("related_osm_way_id") != item["osm_way_id"]
                     or sign_packets[s].get("direction") != item["direction"]
                     for s in ids):
                problem = "SIGN_EVIDENCE_MISSING_REJECTED_OR_WRONG_ROAD_DIRECTION"
            elif any(sign_packets[s].get("road_geometry_sha256") !=
                     item["road_geometry_sha256"] for s in ids):
                problem = "SIGN_AND_SPEED_ROAD_GEOMETRY_DISAGREE"
            elif any(date_at(sign_packets[s].get("observed_at")) >
                     date_at(item["observed_at"]) for s in ids):
                problem = "SIGN_SURVEY_POSTDATES_SPEED_OBSERVATION"
        if problem:
            quarantine(result, problem)
    report["status"] = ("REJECTED" if report["rejected_records"]
                        else ("HUMAN_REVIEW_REQUIRED" if
                              report["ready_for_independent_human_review"] > 0
                              else "NO_EVIDENCE_TO_REVIEW"))
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--review-zip", type=Path, required=True)
    ap.add_argument("--expected-review-zip-sha256", required=True)
    ap.add_argument("--evidence", type=Path, required=True)
    ap.add_argument("--photo-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out.resolve()
    require(not any(x in str(out) for x in (
        "/app/src/main/assets/", "/app/src/main/res/",
        "/data/road_intelligence/")), "AUDIT_REPORT_CANNOT_BECOME_APP_DATA")
    report = audit_evidence(args.review_zip, args.expected_review_zip_sha256,
                            args.evidence, args.photo_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print(json.dumps({k: report[k] for k in (
        "status", "ready_for_independent_human_review", "rejected_records",
        "approved_legal_speeds", "approved_physical_sign_coordinates",
        "driver_alerts_allowed")}, indent=2))
    raise SystemExit(2 if report["rejected_records"] else 0)


if __name__ == "__main__":
    main()
