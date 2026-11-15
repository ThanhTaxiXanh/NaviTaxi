#!/usr/bin/env python3
"""Create/verify a PRIVATE, SHA256-pinned, non-authorizing road evidence ZIP.

The archive is for independent human review only. It can NEVER populate the
Android road database, issue approval pins or enable driver speed/sign alerts.
No real field observations, legal limits or photos are bundled in the source.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
import tempfile
import zipfile

from review_road_field_evidence import (
    EvidenceError, MAX_FILE, SHA, audit_evidence, digest, read_json, read_queue,
)

FORMAT = "navitaxi-private-field-evidence-bundle/v1"
STATUS = "MECHANICAL_EVIDENCE_ONLY_HUMAN_REVIEW_REQUIRED"
MAX_TOTAL = 300_000_000
MAX_ARCHIVE = 350_000_000
MAX_PHOTOS = 1000
MAX_MANIFEST = 2_000_000
CHUNK = 128 * 1024
SOURCE_NAME = "source/unverified_osm_review_queue.zip"
EVIDENCE_NAME = "evidence/independent_packet.json"
REPORT_NAME = "audit/mechanical_review_report.json"
META_NAME = "MANIFEST.json"
SUMS_NAME = "SHA256SUMS"


def require(condition, reason):
    if not condition:
        raise EvidenceError(reason)


def canonical_json(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def safe_relative(name):
    require(isinstance(name, str) and name and len(name) <= 250
            and "\x00" not in name and "\\" not in name
            and not name.startswith("/") and ":" not in name
            and "//" not in name and not name.endswith("/"),
            "UNSAFE_EVIDENCE_PHOTO_PATH")
    parts = name.split("/")
    require(all(p not in ("", ".", "..") for p in parts)
            and PurePosixPath(name).as_posix() == name,
            "UNSAFE_EVIDENCE_PHOTO_PATH")
    return name


def file_hash(path):
    h = hashlib.sha256()
    count = 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            count += len(chunk)
            require(count <= MAX_TOTAL, "OVERSIZED_EVIDENCE_FILE")
            h.update(chunk)
    return count, h.hexdigest()


def photo_source(root, name):
    safe_relative(name)
    current = root
    for part in name.split("/"):
        current = current / part
        require(not current.is_symlink(), "SYMLINK_IN_PHOTO_PATH")
    require(current.is_file() and current.resolve().is_relative_to(root.resolve()),
            "MISSING_OR_UNSAFE_PHOTO")
    return current


def output_path(out, queue, packet, photo_root):
    root = Path(__file__).resolve().parents[1]
    out = out.absolute()
    resolved = out.resolve()
    for forbidden in (root / "app/src/main/assets",
                      root / "app/src/main/res",
                      root / "data/road_intelligence",
                      photo_root):
        require(not resolved.is_relative_to(forbidden.resolve()),
                "BUNDLE_MUST_NOT_ENTER_APP_OR_PHOTO_ROOT")
    require(resolved not in (queue.resolve(), packet.resolve()),
            "BUNDLE_CANNOT_REPLACE_INPUT")
    require(not out.exists() and not out.is_symlink(), "BUNDLE_OUTPUT_ALREADY_EXISTS")
    return out


def zip_entry(name):
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100600 << 16
    info.flag_bits = 0
    return info


def _file_spec(path):
    require(path.is_file() and not path.is_symlink(), "MISSING_OR_UNSAFE_BUNDLE_SOURCE")
    size, checksum = file_hash(path)
    return {"kind": "file", "value": path, "size_bytes": size, "sha256": checksum}


def _bytes_spec(raw):
    return {"kind": "bytes", "value": raw, "size_bytes": len(raw),
            "sha256": digest(raw)}


def _write_member(z, name, spec):
    h = hashlib.sha256()
    count = 0
    with z.open(zip_entry(name), "w", force_zip64=True) as dst:
        source = (spec["value"].open("rb") if spec["kind"] == "file"
                  else io.BytesIO(spec["value"]))
        with source as src:
            for chunk in iter(lambda: src.read(CHUNK), b""):
                count += len(chunk)
                require(count <= MAX_TOTAL, "OVERSIZED_ARCHIVED_MEMBER")
                h.update(chunk)
                dst.write(chunk)
    require(count == spec["size_bytes"] and h.hexdigest() == spec["sha256"],
            "EVIDENCE_CHANGED_DURING_ARCHIVE")


def package(review_zip, expected_queue_sha, evidence, photo_root, output):
    require(SHA.fullmatch(expected_queue_sha) is not None,
            "INVALID_EXPECTED_QUEUE_SHA256")
    output = output_path(output, review_zip, evidence, photo_root)
    _, manifest_sha, _ = read_queue(review_zip, expected_queue_sha)
    report = audit_evidence(review_zip, expected_queue_sha, evidence, photo_root)
    require(report["status"] == "HUMAN_REVIEW_REQUIRED"
            and report["ready_for_independent_human_review"] > 0
            and report["rejected_records"] == 0,
            "BUNDLE_REQUIRES_NONEMPTY_MECHANICALLY_READY_EVIDENCE")
    packet = read_json(evidence.read_bytes())
    require(isinstance(packet, dict) and isinstance(packet.get("sign_evidence"), list),
            "INVALID_EVIDENCE_PACKET")

    specs = {
        SOURCE_NAME: _file_spec(review_zip),
        EVIDENCE_NAME: _file_spec(evidence),
        REPORT_NAME: _bytes_spec(canonical_json(report)),
    }
    photo_entries = set()
    for sign in packet["sign_evidence"]:
        photo = sign["photo"]
        name = safe_relative(photo["path"])
        photo_entries.add(name)
    require(len(photo_entries) <= MAX_PHOTOS, "TOO_MANY_EVIDENCE_PHOTOS")
    for name in sorted(photo_entries):
        specs["photos/" + name] = _file_spec(photo_source(photo_root, name))

    entries = [
        {"path": name, "size_bytes": spec["size_bytes"], "sha256": spec["sha256"]}
        for name, spec in sorted(specs.items())
    ]
    require(sum(e["size_bytes"] for e in entries) <= MAX_TOTAL,
            "EVIDENCE_BUNDLE_TOTAL_TOO_LARGE")
    manifest = {
        "format": FORMAT,
        "status": STATUS,
        "source_queue_sha256": expected_queue_sha,
        "source_queue_manifest_sha256": manifest_sha,
        "evidence_sha256": specs[EVIDENCE_NAME]["sha256"],
        "audit_report_sha256": specs[REPORT_NAME]["sha256"],
        "entries": entries,
        "photo_file_count": len(photo_entries),
        "approved_legal_speeds": 0,
        "approved_physical_sign_coordinates": 0,
        "driver_alerts_allowed": False,
        "production_database_authorized": False,
        "warning": ("PRIVATE observational materials, NOT validated road law, "
                    "field truth, release approval, or permission to drive by."),
    }
    specs[META_NAME] = _bytes_spec(canonical_json(manifest))
    require(specs[META_NAME]["size_bytes"] <= MAX_MANIFEST,
            "BUNDLE_MANIFEST_TOO_LARGE")
    sums = "".join(spec["sha256"] + "  " + name + "\n"
                   for name, spec in sorted(specs.items()))
    specs[SUMS_NAME] = _bytes_spec(sums.encode("utf-8"))
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("xb") as f:
            with zipfile.ZipFile(f, "w", allowZip64=True) as z:
                for name, spec in sorted(specs.items()):
                    _write_member(z, name, spec)
    except Exception:
        output.unlink(missing_ok=True)
        raise
    size, checksum = file_hash(output)
    return {"archive": str(output), "size_bytes": size, "sha256": checksum,
            "source_queue_sha256": expected_queue_sha,
            "photo_file_count": len(photo_entries),
            "status": STATUS, "approved_legal_speeds": 0,
            "approved_physical_sign_coordinates": 0,
            "driver_alerts_allowed": False}


def verify(archive, expected_archive_sha):
    require(SHA.fullmatch(expected_archive_sha) is not None,
            "EXTERNAL_ARCHIVE_SHA256_REQUIRED")
    require(archive.is_file() and not archive.is_symlink()
            and archive.stat().st_size <= MAX_ARCHIVE,
            "MISSING_OR_OVERSIZED_EVIDENCE_ARCHIVE")
    require(file_hash(archive)[1] == expected_archive_sha,
            "ARCHIVE_SHA256_MISMATCH")
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        require(len(infos) <= MAX_PHOTOS + 5 and len(set(names)) == len(names),
                "DUPLICATE_OR_TOO_MANY_ARCHIVE_MEMBERS")
        require(META_NAME in names and SUMS_NAME in names
                and SOURCE_NAME in names and EVIDENCE_NAME in names
                and REPORT_NAME in names,
                "MISSING_REQUIRED_ARCHIVE_MEMBERS")
        total = 0
        for info in infos:
            safe_relative(info.filename)
            require(info.compress_type == zipfile.ZIP_DEFLATED
                    and info.file_size <= MAX_TOTAL and
                    not (info.flag_bits & 0x1) and
                    (info.external_attr >> 16 & 0o170000) == 0o100000,
                    "UNSAFE_ARCHIVE_MEMBER")
            total += info.file_size
        require(total <= MAX_TOTAL and z.getinfo(META_NAME).file_size <= MAX_MANIFEST,
                "ARCHIVE_UNCOMPRESSED_SIZE_LIMIT")
        manifest = read_json(z.read(META_NAME))
        require(isinstance(manifest, dict) and manifest.get("format") == FORMAT
                and manifest.get("status") == STATUS
                and manifest.get("approved_legal_speeds") == 0
                and manifest.get("approved_physical_sign_coordinates") == 0
                and manifest.get("driver_alerts_allowed") is False
                and manifest.get("production_database_authorized") is False,
                "BUNDLE_CANNOT_CLAIM_PRODUCTION_APPROVAL")
        entries = manifest.get("entries")
        require(isinstance(entries, list) and len(entries) == len(infos) - 2,
                "INVALID_BUNDLE_FILE_MANIFEST")
        expected = {}
        for row in entries:
            require(isinstance(row, dict) and isinstance(row.get("path"), str)
                    and isinstance(row.get("size_bytes"), int)
                    and SHA.fullmatch(str(row.get("sha256"))) is not None
                    and row["path"] not in expected,
                    "INVALID_BUNDLE_FILE_ENTRY")
            expected[row["path"]] = row
        require(set(expected) == set(names) - {META_NAME, SUMS_NAME}
                and all(n in (SOURCE_NAME, EVIDENCE_NAME, REPORT_NAME)
                        or n.startswith("photos/") for n in expected),
                "UNEXPECTED_EVIDENCE_ARCHIVE_FILES")
        expected[META_NAME] = {"path": META_NAME,
                               "size_bytes": z.getinfo(META_NAME).file_size,
                               "sha256": digest(z.read(META_NAME))}
        expected_sums = "".join(row["sha256"] + "  " + name + "\n"
                                for name, row in sorted(expected.items()))
        require(z.read(SUMS_NAME) == expected_sums.encode("utf-8"),
                "ARCHIVE_SHA256SUMS_MISMATCH")

        with tempfile.TemporaryDirectory(prefix="navitaxi-private-evidence-") as temp:
            root = Path(temp)
            for name, row in expected.items():
                dest = root.joinpath(*name.split("/"))
                dest.parent.mkdir(parents=True, exist_ok=True)
                sha = hashlib.sha256()
                count = 0
                with z.open(name) as src, dest.open("xb") as dst:
                    for chunk in iter(lambda: src.read(CHUNK), b""):
                        count += len(chunk)
                        require(count <= MAX_TOTAL, "OVERSIZED_ARCHIVE_STREAM")
                        sha.update(chunk)
                        dst.write(chunk)
                require(count == row["size_bytes"] and sha.hexdigest() == row["sha256"],
                        "ARCHIVE_MEMBER_HASH_MISMATCH")
            require(manifest.get("source_queue_sha256") ==
                    expected[SOURCE_NAME]["sha256"],
                    "ARCHIVE_QUEUE_PROVENANCE_MISMATCH")
            require(manifest.get("evidence_sha256") ==
                    expected[EVIDENCE_NAME]["sha256"]
                    and manifest.get("audit_report_sha256") ==
                    expected[REPORT_NAME]["sha256"],
                    "ARCHIVE_EVIDENCE_PROVENANCE_MISMATCH")
            require(manifest.get("photo_file_count") ==
                    sum(n.startswith("photos/") for n in expected),
                    "BUNDLE_PHOTO_COUNT_MISMATCH")
            raw_report = (root / REPORT_NAME).read_bytes()
            repeat = audit_evidence(root / SOURCE_NAME,
                                    manifest["source_queue_sha256"],
                                    root / EVIDENCE_NAME, root / "photos")
            require(repeat["status"] == "HUMAN_REVIEW_REQUIRED"
                    and repeat["rejected_records"] == 0
                    and repeat["ready_for_independent_human_review"] > 0
                    and repeat["queue_manifest_sha256"] ==
                    manifest.get("source_queue_manifest_sha256")
                    and raw_report == canonical_json(repeat),
                    "ARCHIVE_REAUDIT_MISMATCH")
            return {"archive": str(archive), "sha256": expected_archive_sha,
                    "status": STATUS,
                    "verified_archived_files": len(expected),
                    "photo_file_count": manifest["photo_file_count"],
                    "approved_legal_speeds": 0,
                    "approved_physical_sign_coordinates": 0,
                    "driver_alerts_allowed": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--review-zip", type=Path)
    p.add_argument("--expected-review-zip-sha256")
    p.add_argument("--evidence", type=Path)
    p.add_argument("--photo-root", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--verify", type=Path, help="Re-audit an existing archive offline")
    p.add_argument("--expected-archive-sha256",
                   help="Independent checksum printed by the packaging command")
    args = p.parse_args()
    try:
        if args.verify is not None:
            require(args.expected_archive_sha256 is not None,
                    "EXTERNAL_ARCHIVE_SHA256_REQUIRED")
            result = verify(args.verify, args.expected_archive_sha256)
        else:
            require(args.review_zip is not None and args.evidence is not None
                    and args.photo_root is not None and args.out is not None
                    and args.expected_review_zip_sha256 is not None,
                    "MISSING_PACKAGE_INPUT")
            result = package(args.review_zip, args.expected_review_zip_sha256,
                             args.evidence, args.photo_root, args.out)
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    except (EvidenceError, KeyError, TypeError, OSError, zipfile.BadZipFile) as exc:
        print("REJECTED: " + str(exc), file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
