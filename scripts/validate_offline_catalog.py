#!/usr/bin/env python3
"""Validate a pinned, license-attributed NaviTaxi offline PMTiles release catalog.

This is a pre-install approval gate, NOT a remote catalog downloader.
The SHA-256 pin must arrive from a separately reviewed/trusted channel.
An unpinned catalog must never be treated as approved; package hashes alone
do not prove road speed limits or roadside sign locations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

FORMAT = "navitaxi-offline-catalog/v1"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
PACKAGE_ID = re.compile(r"[a-z0-9][a-z0-9-]{1,62}\Z")
VERSION = re.compile(r"[0-9A-Za-z][0-9A-Za-z._-]{0,39}\Z")
MAX_CATALOG_BYTES = 1024 * 1024
PUBLIC_TILE_HOSTS = {"tile.openstreetmap.org", "demotiles.maplibre.org"}
TOP_FIELDS = {"format", "published_at", "packages"}
ENTRY_FIELDS = {
    "id", "version", "release_sequence", "url", "size_bytes", "sha256",
    "license", "source_uri", "is_real_map",
    "has_verified_speed_limits", "has_verified_signs",
}


class CatalogError(ValueError):
    """Catalog cannot be approved or is malformed."""


def _reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CatalogError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _exact_fields(record, expected, name):
    if not isinstance(record, dict) or set(record) != expected:
        raise CatalogError(f"{name}: missing or unexpected JSON fields")


def _string(value, name, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise CatalogError(f"{name}: required nonempty text")
    if any(ord(ch) < 32 for ch in value):
        raise CatalogError(f"{name}: control character")
    return value


def _https_url(value, name, pmtiles=False):
    _string(value, name, 2048 if pmtiles else 1024)
    try:
        url = urlsplit(value)
        port = url.port  # Force validation of malformed port declarations.
    except ValueError as exc:
        raise CatalogError(f"{name}: invalid URL") from exc
    if (url.scheme != "https" or not url.hostname or url.username is not None
            or url.password is not None or url.query or url.fragment
            or port is not None or not url.path.startswith("/")):
        raise CatalogError(f"{name}: require plain HTTPS URL without secrets or query")
    host = url.hostname.lower()
    if pmtiles:
        if host in PUBLIC_TILE_HOSTS or not url.path.endswith(".pmtiles"):
            raise CatalogError(f"{name}: not an authorized PMTiles release endpoint")
    return value


def validate_catalog(raw: bytes, trusted_sha256: str) -> dict:
    """Return parsed metadata only if the complete raw bytes match a trusted pin."""
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= MAX_CATALOG_BYTES:
        raise CatalogError("Catalog size outside the accepted range")
    if not isinstance(trusted_sha256, str) or not SHA256.fullmatch(trusted_sha256):
        raise CatalogError("A separately approved lowercase SHA-256 pin is mandatory")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != trusted_sha256:
        raise CatalogError("Catalog fingerprint does not match the approved release")
    try:
        document = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicates,
                              parse_constant=lambda value: (_ for _ in ()).throw(
                                  CatalogError(f"Invalid JSON number: {value}")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CatalogError("Invalid catalog UTF-8/JSON") from exc
    _exact_fields(document, TOP_FIELDS, "Catalog")
    if document["format"] != FORMAT:
        raise CatalogError("Unsupported catalog format")
    published = _string(document["published_at"], "published_at", 32)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", published):
        raise CatalogError("Expected UTC ISO8601 published_at")
    from datetime import datetime
    try:
        datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise CatalogError("Invalid calendar date") from exc
    entries = document["packages"]
    if not isinstance(entries, list) or len(entries) > 500:
        raise CatalogError("Invalid package collection")
    seen = set()
    for entry in entries:
        _exact_fields(entry, ENTRY_FIELDS, "Package")
        identifier = _string(entry["id"], "id", 63)
        if not PACKAGE_ID.fullmatch(identifier) or identifier in seen:
            raise CatalogError("Unsafe or repeated package id")
        seen.add(identifier)
        version = _string(entry["version"], "version", 40)
        if not VERSION.fullmatch(version) or ".." in version:
            raise CatalogError("Invalid version/path")
        sequence = entry["release_sequence"]
        if type(sequence) is not int or not 1 <= sequence <= 9223372036854775807:
            raise CatalogError("Invalid monotonic release_sequence")
        size = entry["size_bytes"]
        if type(size) is not int or not 127 <= size <= 2_000_000_000:
            raise CatalogError("Invalid PMTiles archive size")
        if not isinstance(entry["sha256"], str) or not SHA256.fullmatch(entry["sha256"]):
            raise CatalogError("Invalid package SHA-256")
        _string(entry["license"], "license", 300)
        _https_url(entry["source_uri"], "source_uri")
        _https_url(entry["url"], "url", pmtiles=True)
        for flag in ("is_real_map", "has_verified_speed_limits", "has_verified_signs"):
            if type(entry[flag]) is not bool:
                raise CatalogError(f"{flag}: require a JSON boolean")
        # The catalog contains PMTiles only, never a validated legal speed/sign DB.
        if entry["has_verified_speed_limits"] or entry["has_verified_signs"]:
            raise CatalogError("PMTiles catalog cannot verify legal speed/sign coordinates")
    return {"sha256": digest, "format": FORMAT, "published_at": published,
            "packages": entries}


def classify_release(candidate: dict, installed: dict | None) -> str:
    """Use monotonically increasing sequence, never lexicographic version order."""
    if installed is None:
        return "NOT_INSTALLED"
    if candidate["id"] != installed.get("id"):
        raise CatalogError("Installed record identity mismatch")
    seq = installed.get("release_sequence")
    if type(seq) is not int or seq < 1:
        raise CatalogError("Installed record lacks trustworthy release_sequence")
    if candidate["release_sequence"] < seq:
        return "ROLLBACK_REJECTED"
    if candidate["release_sequence"] > seq:
        return "UPDATE_AVAILABLE"
    if (candidate["version"] == installed.get("version") and
            candidate["sha256"] == installed.get("sha256")):
        return "CURRENT"
    return "SAME_SEQUENCE_CONFLICT"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--approved-sha256", required=True,
                        help="Pin approved independently; NEVER read from catalog itself")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    approved = validate_catalog(args.catalog.read_bytes(), args.approved_sha256)
    report = {"format": approved["format"], "catalog_sha256": approved["sha256"],
              "package_count": len(approved["packages"]), "approved_by_pin": True,
              "download_enabled": False,
              "road_speed_records_verified": 0, "traffic_signs_verified": 0}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
