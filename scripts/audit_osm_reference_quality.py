#!/usr/bin/env python3
"""Strict quality inventory of UNVERIFIED OSM speed/sign candidate JSONL.

Checks exact source and archive provenance, SHA256, JSONL rows, field scopes,
duplicate identities and WGS84 nodes. Summaries are raw tag statistics only:
not an official legal speed limit or physical traffic-sign survey.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

EXPECTED_FILES = ("speed_way_candidates.jsonl", "traffic_sign_candidates.jsonl")
COUNT_KEYS = ("speed_way_candidates", "sign_node_candidates",
              "sign_way_candidates", "sign_relation_candidates",
              "sign_nodes_without_usable_point")
HASH = re.compile(r"[0-9a-f]{64}\Z")
MAX_ROWS = 2_000_000
MAX_FILE_BYTES = 1_000_000_000


class AuditError(ValueError):
    pass


def _read_json(path: Path):
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise AuditError("Duplicated JSON property: " + key)
            result[key] = value
        return result
    try:
        return json.loads(path.read_text(encoding="utf-8"),
                          object_pairs_hook=no_duplicates,
                          parse_constant=lambda v: (_ for _ in ()).throw(AuditError(
                              "NaN/Infinity is not valid JSON")))
    except (OSError, UnicodeError, json.JSONDecodeError) as e:
        raise AuditError("Cannot read JSON " + path.name) from e


def _read_row(line: str):
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise AuditError("Duplicated candidate JSON property")
            result[key] = value
        return result
    try:
        return json.loads(line, object_pairs_hook=no_duplicates,
                          parse_constant=lambda v: (_ for _ in ()).throw(AuditError(
                              "Non-finite candidate JSON number")))
    except json.JSONDecodeError as e:
        raise AuditError("Invalid JSONL row") from e


def _hash(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(128 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_reference(directory: Path, receipt_path: Path | None = None) -> dict:
    directory = directory.resolve()
    manifest = _read_json(directory / "manifest.json")
    if manifest.get("format") != "navitaxi-osm-road-reference/v1" or (
            manifest.get("status") != "UNVERIFIED_OSM_REFERENCE_ONLY"):
        raise AuditError("Input is not a reference-only OSM manifest")
    if manifest.get("prohibitions") != {
        "approved_speed_limits": False,
        "approved_sign_coordinates": False,
        "driver_speed_alerts": False,
        "traffic_sign_alerts": False,
        "production_offline_map_package": False,
    }:
        raise AuditError("Untrusted data incorrectly authorizes an application")
    source = manifest.get("source_snapshot")
    if not isinstance(source, dict) or not HASH.fullmatch(str(source.get("sha256"))) or (
            type(source.get("size_bytes")) is not int or
            source["size_bytes"] <= 0 or source.get("license") != "ODbL-1.0"):
        raise AuditError("Original OSM source provenance is missing")
    if receipt_path is not None:
        receipt = _read_json(receipt_path)
        for attr, theirs in (
            ("sha256", "sha256"), ("size_bytes", "size_bytes"),
            ("source_uri", "source_uri"), ("filename", "filename")):
            if source.get(theirs) != receipt.get(attr):
                raise AuditError("Independent acquisition receipt does not match source " + attr)
        if (receipt.get("driver_alerts_allowed") is not False or
                receipt.get("legal_speed_limits_verified") is not False or
                receipt.get("physical_sign_coordinates_verified") is not False):
            raise AuditError("Acquisition receipt asserts unapproved safety data")

    entries = manifest.get("files")
    if not isinstance(entries, dict) or set(entries) != set(EXPECTED_FILES):
        raise AuditError("Unexpected or missing reference payload")
    for name in EXPECTED_FILES:
        entry = entries[name]
        file = directory / name
        if (not isinstance(entry, dict) or
                type(entry.get("size_bytes")) is not int or
                not 0 <= entry["size_bytes"] <= MAX_FILE_BYTES or
                not HASH.fullmatch(str(entry.get("sha256"))) or
                not file.is_file() or file.stat().st_size != entry["size_bytes"] or
                _hash(file) != entry["sha256"]):
            raise AuditError("Mismatched reference file size/SHA256: " + name)

    counts = {k: 0 for k in COUNT_KEYS}
    seen_speed = set()
    seen_sign = set()
    raw_speed = Counter()
    raw_signs = Counter()
    semantics = Counter()
    def records(name):
        with (directory / name).open("r", encoding="utf-8") as file:
            for line in file:
                if len(line) > 65536:
                    raise AuditError("Excessively long reference record")
                if not line.strip():
                    raise AuditError("Empty reference JSONL row")
                yield _read_row(line)

    for row in records(EXPECTED_FILES[0]):
        counts["speed_way_candidates"] += 1
        if counts["speed_way_candidates"] > MAX_ROWS:
            raise AuditError("Too many source candidates")
        if row.get("kind") != "way_speed_tag":
            raise AuditError("Unexpected speed record kind")
        obj = row.get("osm")
        if not isinstance(obj, dict) or obj.get("type") != "way" or (
                type(obj.get("id")) is not int or obj["id"] <= 0):
            raise AuditError("Source speed OSM way identity invalid")
        if obj["id"] in seen_speed:
            raise AuditError("Duplicate speed source way ID")
        seen_speed.add(obj["id"])
        if row.get("osm_node_coordinate") is not None:
            raise AuditError("Speed way invents a point coordinate")
        _assert_unverified(row)
        tags = row.get("tags")
        if not isinstance(tags, dict) or not tags.get("highway") or (
                not any(k.startswith("maxspeed") or k == "source:maxspeed"
                        for k in tags)):
            raise AuditError("Speed way is missing source raw OSM speed tags")
        if not all(isinstance(k, str) and isinstance(v, str) for k,v in tags.items()):
            raise AuditError("Invalid raw source tags")
        raw_speed[tags.get("maxspeed", "<no-maxspeed-main-tag>")] += 1
        if any(k.startswith("maxspeed:conditional") for k in tags):
            semantics["conditional"] += 1
        if any("advisory" in k for k in tags):
            semantics["advisory"] += 1
        if any(k.startswith("maxspeed:forward") or k.startswith("maxspeed:backward")
               for k in tags):
            semantics["directional"] += 1
        if any("mph" in v.lower() for k,v in tags.items() if k.startswith("maxspeed")):
            semantics["mph"] += 1
        if not re.fullmatch(r"[0-9]+", tags.get("maxspeed", "")):
            semantics["non_plain_integer_maxspeed"] += 1

    for row in records(EXPECTED_FILES[1]):
        obj = row.get("osm")
        if not isinstance(obj, dict) or obj.get("type") not in ("node", "way", "relation") or (
                type(obj.get("id")) is not int or obj["id"] <= 0):
            raise AuditError("Invalid sign OSM identity")
        kind = obj["type"]
        key = (kind, obj["id"])
        if key in seen_sign:
            raise AuditError("Duplicate sign OSM object identity")
        seen_sign.add(key)
        metric = {"node": "sign_node_candidates", "way": "sign_way_candidates",
                  "relation": "sign_relation_candidates"}[kind]
        counts[metric] += 1
        if len(seen_sign) > MAX_ROWS:
            raise AuditError("Too many sign source candidates")
        _assert_unverified(row)
        tags = row.get("tags")
        if not isinstance(tags, dict) or not any(
                k == "traffic_sign" or k.startswith("traffic_sign:") for k in tags):
            raise AuditError("Sign record has no original traffic_sign tag")
        if not all(isinstance(k, str) and isinstance(v, str) for k,v in tags.items()):
            raise AuditError("Invalid sign source tags")
        raw_signs[tags.get("traffic_sign", "<variant-only>")] += 1
        position = row.get("osm_node_coordinate")
        if kind != "node" and position is not None:
            raise AuditError("Way or relation fabricates a physical sign coordinate")
        if kind == "node" and position is None:
            counts["sign_nodes_without_usable_point"] += 1
        if position is not None:
            if not isinstance(position, dict):
                raise AuditError("Sign coordinate must be a WGS84 point object")
            lat = position.get("latitude")
            lon = position.get("longitude")
            if (type(lat) not in (int, float) or
                    type(lon) not in (int, float) or
                    not math.isfinite(lat) or not math.isfinite(lon) or
                    not -90 <= lat <= 90 or not -180 <= lon <= 180):
                raise AuditError("Invalid OSM node WGS84 point")

    if counts != manifest.get("counts"):
        raise AuditError("Reference manifest count mismatch")
    return {
        "format": "navitaxi-osm-reference-quality/v1",
        "status": "REFERENCE_ONLY_NO_LEGAL_OR_PHYSICAL_SIGN_APPROVAL",
        "source_snapshot": source,
        "counts": counts,
        "top_raw_maxspeed_values": raw_speed.most_common(15),
        "top_raw_traffic_sign_values": raw_signs.most_common(15),
        "raw_speed_semantics": dict(sorted(semantics.items())),
        "unverified_osm_sign_node_coordinate_count": (
            counts["sign_node_candidates"] - counts["sign_nodes_without_usable_point"]),
        "verified_legal_speed_records": 0,
        "verified_physical_sign_coordinates": 0,
        "driver_speed_alerts_enabled": False,
        "physical_sign_alerts_enabled": False,
        "warning": "OSM tags and node coordinates are references, not verified traffic laws or physical sign surveys.",
    }


def _assert_unverified(row):
    for name in ("independently_verified_legal_speed",
                 "independently_verified_physical_sign",
                 "approved_for_driver_alert"):
        if row.get(name) is not False:
            raise AuditError("A raw OSM candidate falsely claims independent verification")
    expected_position = ("osm_node_point_unverified"
                         if row.get("osm_node_coordinate") is not None
                         else "no_physical_sign_coordinate")
    if row.get("position_type") != expected_position:
        raise AuditError("Unverified physical point semantics are inconsistent")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reference-dir", required=True, type=Path)
    ap.add_argument("--receipt", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    report = audit_reference(args.reference_dir, args.receipt)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps({"status": report["status"], "counts": report["counts"],
                      "raw_speed_semantics": report["raw_speed_semantics"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
