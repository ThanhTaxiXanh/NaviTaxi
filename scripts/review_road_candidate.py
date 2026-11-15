#!/usr/bin/env python3
"""Offline candidate audit for Road Intelligence SQLite; NEVER authorizes driving alerts.

Unlike a source_id or a user-supplied license string, the final publication pin
must be approved separately after legal, coordinate and field-evidence review.
This script does not fetch maps, infer maxspeed or generate physical sign points.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit

REQUIRED = {
    "data_sources": {"source_id", "provider", "source_uri", "license",
                     "acquired_at", "checksum_sha256"},
    "road_segments": {"segment_id", "direction", "speed_kmh", "geometry_geojson",
                      "min_lon", "max_lon", "min_lat", "max_lat",
                      "source_id", "observed_at", "verified_at"},
    "traffic_signs": {"sign_id", "sign_code", "latitude", "longitude",
                      "direction", "source_id", "observed_at", "verified_at"},
    "road_segments_rtree": {"segment_pk", "min_lon", "max_lon", "min_lat", "max_lat"},
    "traffic_signs_rtree": {"sign_pk", "min_lon", "max_lon", "min_lat", "max_lat"},
}
MAX_BYTES = 2_000_000_000
MAX_ROWS = 1_000_000
MAX_ISSUES = 100


def _date_present(value):
    if not isinstance(value, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})?)?", value):
        return False
    try:
        if len(value) == 10:
            date.fromisoformat(value)
        else:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _https_evidence(value):
    if not isinstance(value, str) or len(value) > 2048:
        return False
    try:
        url = urlsplit(value)
        return (url.scheme == "https" and url.hostname is not None and
                url.username is None and url.password is None and
                url.fragment == "" and url.path.startswith("/"))
    except ValueError:
        return False


def _valid_geometry(value, bbox):
    try:
        geometry = json.loads(value, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if not isinstance(geometry, dict) or geometry.get("type") != "LineString":
            return False
        coordinates = geometry.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            return False
        lons, lats = [], []
        for point in coordinates:
            if not isinstance(point, list) or len(point) < 2:
                return False
            lon, lat = point[:2]
            if (type(lon) not in (int, float) or type(lat) not in (int, float)
                    or not math.isfinite(lon) or not math.isfinite(lat)
                    or not -180 <= lon <= 180 or not -90 <= lat <= 90):
                return False
            lons.append(lon)
            lats.append(lat)
        # A padded or shifted box can make a road appear applicable far away.
        # The source bounds must describe the supplied LineString, not merely
        # contain it. The separate RTree is checked against these source bounds.
        exact_bounds = (min(lons), max(lons), min(lats), max(lats))
        return all(abs(float(actual) - float(claimed)) <= 1e-8
                   for actual, claimed in zip(exact_bounds, bbox))
    except (TypeError, ValueError):
        return False


def _rtree_box_matches(source_bounds, indexed_bounds):
    """Check RTree's outward-rounded float32 coordinates, not a ~111m window.

    SQLite RTree stores 32-bit floats and rounds min/max outward. Two float32
    ULPs are a conservative tolerance for this conversion, whereas 0.001
    degrees previously hid tens of metres of sign-index corruption.
    """
    for original, indexed in zip(source_bounds, indexed_bounds):
        if (type(original) not in (int, float) or
                type(indexed) not in (int, float) or
                not math.isfinite(original) or not math.isfinite(indexed)):
            return False
        tolerance = (2.0 ** -148 if original == 0 else
                     2.0 ** (max(-126, math.floor(math.log2(abs(original)))) - 22))
        if abs(original - indexed) > tolerance:
            return False
    return True


def audit_candidate(path: Path) -> dict:
    path = path.resolve()
    report = {
        "format": "navitaxi-road-candidate-audit/v1",
        "filename": path.name,
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "sha256": None,
        "status": "REJECTED",
        "driver_speed_alerts_allowed": False,
        "physical_sign_alerts_allowed": False,
        "approval_pin_created": False,
        "counts": {"data_sources": 0, "road_segments": 0, "traffic_signs": 0},
        "issues": [],
        "warning": "A valid SQLite audit is NOT independent verification of road law or physical sign coordinates.",
    }

    def issue(message):
        if len(report["issues"]) < MAX_ISSUES:
            report["issues"].append(message)

    if not path.is_file() or not 100 <= report["size_bytes"] <= MAX_BYTES:
        issue("Missing or oversized/corrupt candidate file")
        return report
    if any(Path(str(path) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
        issue("Unhashed SQLite WAL/SHM/journal sidecar is present")
        return report
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(64 * 1024), b""):
            digest.update(chunk)
    report["sha256"] = digest.hexdigest()
    try:
        # Immutable read avoids modifying the candidate or following unreviewed WAL.
        connection = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
        try:
            connection.execute("PRAGMA query_only = ON")
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                issue("SQLite integrity_check failed")
            if connection.execute("PRAGMA user_version").fetchone()[0] != 1:
                issue("Unexpected canonical schema version")
            present = {name for (name,) in connection.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
            for table, needed in REQUIRED.items():
                if table not in present:
                    issue(f"Missing table: {table}")
                    continue
                columns = {row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')}
                if not needed.issubset(columns):
                    issue(f"Missing columns in {table}: {sorted(needed-columns)}")
            if report["issues"]:
                return report
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                issue("Broken source/segment foreign key")
            for table in ("data_sources", "road_segments", "traffic_signs"):
                report["counts"][table] = connection.execute(
                    f"SELECT count(*) FROM {table}").fetchone()[0]
                if report["counts"][table] > MAX_ROWS:
                    issue(f"{table}: unsupported row count for this audit")
            if report["issues"]:
                return report
            source_ids = set()
            for source_id, provider, uri, license_text, acquired, checksum in connection.execute(
                "SELECT source_id,provider,source_uri,license,acquired_at,checksum_sha256 "
                "FROM data_sources"):
                source_ids.add(source_id)
                if (not provider or not license_text or not _https_evidence(uri)
                        or not _date_present(acquired)
                        or not isinstance(checksum, str)
                        or not re.fullmatch(r"[0-9a-f]{64}", checksum)):
                    issue(f"Source {source_id!r}: legal/license/source metadata requires review")
            road_rows = connection.execute(
                "SELECT r.segment_id,r.direction,r.speed_kmh,r.geometry_geojson,"
                "r.min_lon,r.max_lon,r.min_lat,r.max_lat,r.source_id,"
                "r.observed_at,r.verified_at,"
                "t.segment_pk,t.min_lon,t.max_lon,t.min_lat,t.max_lat "
                "FROM road_segments r LEFT JOIN road_segments_rtree t "
                "ON r.segment_pk=t.segment_pk"
            )
            for row in road_rows:
                segment_id, direction, speed, geo, minlon, maxlon, minlat, maxlat, source_id, observed, verified, pk, *box = row
                if (not isinstance(speed, int) or not 1 <= speed <= 250
                        or direction not in ("forward", "backward", "both")
                        or source_id not in source_ids or not _date_present(observed)
                        or not _date_present(verified)
                        or not _valid_geometry(geo, (minlon, maxlon, minlat, maxlat))):
                    issue(f"Road {segment_id!r}: geometry, source, speed or field evidence invalid")
                if pk is None or not _rtree_box_matches(
                        (minlon, maxlon, minlat, maxlat), box):
                    issue(f"Road {segment_id!r}: RTree entry mismatched")
            sign_rows = connection.execute(
                "SELECT s.sign_id,s.sign_code,s.latitude,s.longitude,s.direction,"
                "s.source_id,s.observed_at,s.verified_at,"
                "t.sign_pk,t.min_lon,t.max_lon,t.min_lat,t.max_lat "
                "FROM traffic_signs s LEFT JOIN traffic_signs_rtree t "
                "ON s.sign_pk=t.sign_pk"
            )
            for row in sign_rows:
                sign_id, code, lat, lon, direction, source_id, observed, verified, pk, *box = row
                if (not code or not isinstance(lat, (int, float))
                        or not isinstance(lon, (int, float))
                        or not math.isfinite(lat) or not math.isfinite(lon)
                        or not -90 <= lat <= 90 or not -180 <= lon <= 180
                        or direction not in ("forward", "backward", "both", "unknown")
                        or source_id not in source_ids or not _date_present(observed)
                        or not _date_present(verified)):
                    issue(f"Sign {sign_id!r}: coordinate, code, source or field evidence invalid")
                if pk is None or not _rtree_box_matches((lon, lon, lat, lat), box):
                    issue(f"Sign {sign_id!r}: RTree entry mismatched")
            for main_table, index_table in (
                    ("road_segments", "road_segments_rtree"),
                    ("traffic_signs", "traffic_signs_rtree")):
                original = connection.execute(f"SELECT count(*) FROM {main_table}").fetchone()[0]
                spatial = connection.execute(f"SELECT count(*) FROM {index_table}").fetchone()[0]
                if original != spatial:
                    issue(f"{index_table}: orphan or missing spatial entries")
            if not report["issues"]:
                report["status"] = ("EMPTY_DATABASE" if not
                    (report["counts"]["road_segments"] or report["counts"]["traffic_signs"])
                    else "CANDIDATE_REQUIRES_INDEPENDENT_FIELD_REVIEW")
        finally:
            connection.close()
    except (sqlite3.Error, ValueError, TypeError, KeyError, OSError) as exc:
        issue(f"SQLite inspection failed: {type(exc).__name__}: {exc}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = audit_candidate(args.db)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "sha256", "counts", "issues")},
                     ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] != "REJECTED" else 2)


if __name__ == "__main__":
    main()
