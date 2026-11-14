#!/usr/bin/env python3
"""Bounded acquisition of a dated Geofabrik Vietnam PBF for REFERENCE-ONLY audit.

One pinned *filename* and listed byte length, never the moving 'latest' alias.
Records the publisher's MD5 sidecar AND locally computed SHA-256; the sidecar
is not a signature and neither hash proves legal speed or physical signs.
Does not download OSMF tile services, install a map, import SQLite or issue alerts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

SNAPSHOT = "vietnam-261112.osm.pbf"
SOURCE_URI = "https://download.geofabrik.de/asia/" + SNAPSHOT
MD5_URI = SOURCE_URI + ".md5"
EXPECTED_BYTES = 332_558_874  # 2026-11-12 public Geofabrik Vietnam index
MAX_DOWNLOAD_BYTES = 350_000_000
MD5_LINE = re.compile(r"([a-fA-F0-9]{32})[ \t]+\*?vietnam-261112\.osm\.pbf\Z")
USER_AGENT = "NaviTaxi-road-reference-audit/0.1 (+https://github.com/ThanhTaxiXanh/NaviTaxi)"


class AcquisitionError(ValueError):
    pass


def _verified_origin(actual_url: str, expected_path: str) -> None:
    try:
        url = urlsplit(actual_url)
        hostname = url.hostname or ""
        valid_host = (hostname == "download.geofabrik.de" or
                      re.fullmatch(r"download-ext[0-9]+\.geofabrik\.de", hostname))
        if (url.scheme != "https" or not valid_host or url.port is not None
                or url.username or url.password or url.query or url.fragment
                or url.path != expected_path):
            raise AcquisitionError("Download redirected outside the authorized Geofabrik snapshot origin")
    except ValueError as err:
        if isinstance(err, AcquisitionError):
            raise
        raise AcquisitionError("Invalid Geofabrik redirect origin") from err


def acquire_snapshot(directory: Path, opener=urlopen, expected_bytes: int = EXPECTED_BYTES) -> dict:
    """Download once into a NEW staging directory, or discard it entirely."""
    if expected_bytes <= 0 or expected_bytes > MAX_DOWNLOAD_BYTES:
        raise AcquisitionError("Invalid bounded snapshot size")
    directory = directory.resolve()
    parts = directory.parts
    if ("app" in parts and "src" in parts and "main" in parts) or (
            "data" in parts and "road_intelligence" in parts):
        raise AcquisitionError("Snapshot cannot be placed into Android/approved road DB assets")

    directory.mkdir(parents=True, exist_ok=False)
    try:
        request = Request(MD5_URI, headers={"User-Agent": USER_AGENT})
        with opener(request, timeout=60) as response:
            _verified_origin(response.geturl(), "/asia/" + SNAPSHOT + ".md5")
            sidecar = response.read(1024)
        if len(sidecar) >= 1024:
            raise AcquisitionError("Publisher MD5 sidecar is too long")
        match = MD5_LINE.fullmatch(sidecar.decode("ascii").strip())
        if not match:
            raise AcquisitionError("Unexpected Geofabrik filename or digest in MD5 sidecar")
        published_md5 = match.group(1).lower()

        tmp = directory / (SNAPSHOT + ".part")
        digest_md5 = hashlib.md5(usedforsecurity=False)
        digest_sha256 = hashlib.sha256()
        observed_bytes = 0
        request = Request(SOURCE_URI, headers={"User-Agent": USER_AGENT})
        with opener(request, timeout=60) as response:
            _verified_origin(response.geturl(), "/asia/" + SNAPSHOT)
            header = response.headers.get("Content-Length")
            if header is not None:
                try:
                    length = int(header)
                except ValueError as err:
                    raise AcquisitionError("Invalid Content-Length") from err
                if length != expected_bytes:
                    raise AcquisitionError("Unexpected Geofabrik snapshot Content-Length")
            with tmp.open("xb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    observed_bytes += len(chunk)
                    if observed_bytes > MAX_DOWNLOAD_BYTES:
                        raise AcquisitionError("Excessive snapshot byte count")
                    digest_md5.update(chunk)
                    digest_sha256.update(chunk)
                    output.write(chunk)
        if observed_bytes != expected_bytes:
            raise AcquisitionError("Downloaded snapshot size differs from dated source listing")
        if digest_md5.hexdigest() != published_md5:
            raise AcquisitionError("Downloaded data does not match publisher MD5 sidecar")
        final = directory / SNAPSHOT
        os.replace(tmp, final)
        receipt = {
            "format": "navitaxi-geofabrik-pbf-receipt/v1",
            "status": "OSM_SNAPSHOT_INTEGRITY_ONLY_NOT_TRAFFIC_VERIFICATION",
            "source_uri": SOURCE_URI,
            "publisher_md5_uri": MD5_URI,
            "filename": SNAPSHOT,
            "source_index_date": "2026-11-12",
            "size_bytes": observed_bytes,
            "sha256": digest_sha256.hexdigest(),
            "md5": published_md5,
            "publisher_md5_matches": True,
            "sha256_independently_approved": False,
            "legal_speed_limits_verified": False,
            "physical_sign_coordinates_verified": False,
            "driver_alerts_allowed": False,
            "license": "ODbL-1.0",
            "attribution": "© OpenStreetMap contributors",
            "warning": "Geofabrik MD5 and local SHA256 prove snapshot integrity only. Never infer road law/sign survey from OSM tags.",
        }
        (directory / "receipt.json").write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        return receipt
    except BaseException:
        shutil.rmtree(directory)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="A NEW build/ staging directory, never Android assets")
    args = parser.parse_args()
    receipt = acquire_snapshot(args.output_dir)
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
