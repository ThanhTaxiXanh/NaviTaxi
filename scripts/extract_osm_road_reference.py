#!/usr/bin/env python3
"""Extract *reference-only* OSM speed/sign tags from a pinned LOCAL snapshot.

No download, inferred road speed, sign centroid, SQLite import, Android asset,
map overlay or driver alert is performed. PBF needs the BSD-2-Clause pyosmium
package; small .osm XML snapshots use the standard library.

The --expected-sha256 is a reproducible source snapshot pin, NOT independent
approval of legal speed limits or surveyed physical sign coordinates.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit
import zipfile

FORMAT = "navitaxi-osm-road-reference/v1"
MAX_CANDIDATES = 2_000_000
SHA = re.compile(r"[0-9a-f]{64}\Z")
SIGN_KEYS = {"traffic_sign", "traffic_sign:forward", "traffic_sign:backward",
             "traffic_sign:direction"}
SPEED_CONTEXT = {"highway", "oneway", "name", "ref", "source",
                 "source:maxspeed", "maxspeed:type", "maxspeed:source"}


class ReferenceError(ValueError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_uri(uri: str) -> str:
    if not isinstance(uri, str) or len(uri) > 2048:
        raise ReferenceError("Source URI is required")
    try:
        parts = urlsplit(uri)
        port = parts.port
    except ValueError as error:
        raise ReferenceError("Invalid source URI") from error
    if (parts.scheme != "https" or not parts.hostname or port is not None or
            parts.username is not None or parts.password is not None or
            parts.query or parts.fragment or not parts.path.startswith("/")):
        raise ReferenceError("Source must be a plain HTTPS provenance URI")
    if parts.hostname.lower() in {"tile.openstreetmap.org", "demotiles.maplibre.org"}:
        raise ReferenceError("Public tile services are not offline PBF sources")
    return uri


def _speed_tags(tags: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in sorted(tags.items())
            if k.startswith("maxspeed") or k == "source:maxspeed"}


def _sign_tags(tags: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in sorted(tags.items())
            if k == "traffic_sign" or k.startswith("traffic_sign:")}


def _whitelist(tags: dict[str, str], domain: str) -> dict[str, str]:
    picked = (_speed_tags(tags) if domain == "speed" else {**_sign_tags(tags), **_speed_tags(tags)})
    for key in SPEED_CONTEXT | {"direction"}:
        if key in tags:
            picked[key] = tags[key]
    # Keep original OSM strings: mph, conditional, advisory, variable,
    # national defaults, lane-dependent values are NEVER converted here.
    return dict(sorted(picked.items()))


def _point(lat, lon):
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(lat) and math.isfinite(lon) and
            -90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return {"latitude": lat, "longitude": lon}


def _identity(kind: str, osm_id: int, version, timestamp) -> dict:
    if int(osm_id) <= 0:
        raise ReferenceError("Invalid OSM identity")
    return {"type": kind, "id": int(osm_id),
            "version": int(version) if version is not None else None,
            "timestamp": str(timestamp) if timestamp else None}


def _record(kind: str, osm_id: int, version, timestamp, tags: dict,
            domain: str, location=None) -> dict:
    return {
        "kind": "way_speed_tag" if domain == "speed" else "traffic_sign_tag",
        "osm": _identity(kind, osm_id, version, timestamp),
        "tags": _whitelist(tags, domain),
        "osm_node_coordinate": location if kind == "node" else None,
        "position_type": ("osm_node_point_unverified" if location is not None
                          else "no_physical_sign_coordinate"),
        "independently_verified_legal_speed": False,
        "independently_verified_physical_sign": False,
        "approved_for_driver_alert": False,
    }


class _Sink:
    def __init__(self, speeds, signs, max_candidates: int):
        self.speeds = speeds
        self.signs = signs
        self.counts = {"speed_way_candidates": 0, "sign_node_candidates": 0,
                       "sign_way_candidates": 0, "sign_relation_candidates": 0,
                       "sign_nodes_without_usable_point": 0}
        self.max_candidates = max_candidates

    def _write(self, file, record):
        if (self.counts["speed_way_candidates"] +
                self.counts["sign_node_candidates"] +
                self.counts["sign_way_candidates"] +
                self.counts["sign_relation_candidates"]) >= self.max_candidates:
            raise ReferenceError("Candidate limit exceeded; no partial release is kept")
        file.write(json.dumps(record, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":"), allow_nan=False) + "\n")

    def object(self, kind, osm_id, version, timestamp, tags, location=None):
        if kind == "way" and tags.get("highway") and _speed_tags(tags):
            self._write(self.speeds, _record(
                kind, osm_id, version, timestamp, tags, "speed"))
            self.counts["speed_way_candidates"] += 1
        # Only an actual OSM NODE can contribute an OSM coordinate.
        # Even that node's coordinate is NOT field-verified sign placement.
        if _sign_tags(tags):
            self._write(self.signs, _record(
                kind, osm_id, version, timestamp, tags, "sign", location))
            name = {"node": "sign_node_candidates", "way": "sign_way_candidates",
                    "relation": "sign_relation_candidates"}[kind]
            self.counts[name] += 1
            if kind == "node" and location is None:
                self.counts["sign_nodes_without_usable_point"] += 1


def _parse_xml(path: Path, sink: _Sink):
    iterator = ET.iterparse(path, events=("start", "end"))
    root = None
    for event, elem in iterator:
        if root is None and event == "start":
            root = elem
            if root.tag != "osm":
                raise ReferenceError("Not an OSM XML snapshot")
        if event != "end" or elem.tag not in {"node", "way", "relation"}:
            continue
        tags = {tag.get("k"): tag.get("v", "") for tag in elem.findall("tag")
                if tag.get("k")}
        kind = elem.tag
        coord = (_point(elem.get("lat"), elem.get("lon"))
                 if kind == "node" else None)
        sink.object(kind, int(elem.attrib["id"]),
                    int(elem.attrib["version"]) if "version" in elem.attrib else None,
                    elem.get("timestamp"), tags, coord)
        # OSM's large top-level node/way sequence must not build an XML tree.
        if root is not None:
            root.clear()


def _parse_pbf(path: Path, sink: _Sink):
    try:
        import osmium
    except ImportError as error:
        raise ReferenceError(
            "PBF extraction requires the BSD-2-Clause dependency: pip install osmium==4.3.2"
        ) from error

    class Handler(osmium.SimpleHandler):
        def node(self, obj):
            tags = dict(obj.tags)
            if not _sign_tags(tags):
                return
            location = None
            if obj.location.valid():
                location = _point(obj.location.lat, obj.location.lon)
            sink.object("node", obj.id, obj.version, obj.timestamp, tags, location)

        def way(self, obj):
            tags = dict(obj.tags)
            if (tags.get("highway") and _speed_tags(tags)) or _sign_tags(tags):
                sink.object("way", obj.id, obj.version, obj.timestamp, tags)

        def relation(self, obj):
            tags = dict(obj.tags)
            if _sign_tags(tags):
                sink.object("relation", obj.id, obj.version, obj.timestamp, tags)

    Handler().apply_file(str(path), locations=False)


def extract_reference(snapshot: Path, expected_sha256: str, source_uri: str,
                      output_dir: Path, max_candidates: int = MAX_CANDIDATES,
                      archive: Path | None = None) -> dict:
    snapshot, output_dir = snapshot.resolve(), output_dir.resolve()
    source_uri = _source_uri(source_uri)
    if not SHA.fullmatch(expected_sha256):
        raise ReferenceError("An explicit lowercase 64-character snapshot SHA is required")
    if not snapshot.is_file() or snapshot.stat().st_size <= 0:
        raise ReferenceError("Source snapshot does not exist or is empty")
    if snapshot.name.endswith(".osm.pbf"):
        parser = _parse_pbf
    elif snapshot.name.endswith(".osm"):
        parser = _parse_xml
    else:
        raise ReferenceError("Only local .osm or .osm.pbf snapshots are accepted")
    if not 1 <= max_candidates <= MAX_CANDIDATES:
        raise ReferenceError("Invalid maximum candidate count")
    path_text = "/" + output_dir.as_posix().strip("/") + "/"
    if any(segment in path_text for segment in (
            "/app/src/main/assets/", "/app/src/main/res/",
            "/data/road_intelligence/")):
        raise ReferenceError("Reference output cannot enter Android or verified road data assets")
    if snapshot == output_dir or output_dir in snapshot.parents:
        raise ReferenceError("Output directory must not contain the source snapshot")
    if archive is not None:
        archive = archive.resolve()
        if archive.exists():
            raise ReferenceError("Refusing to overwrite a previous reference archive")
        if archive.parent == output_dir or output_dir in archive.parents:
            raise ReferenceError("Archive must be outside the output directory")
    initial_sha = _sha256(snapshot)
    if initial_sha != expected_sha256:
        raise ReferenceError("Local snapshot does not match the independently supplied pin")

    # Exclusive destination + cleanup: a failed parser can never look like a
    # complete reference catalog. Nothing becomes an Android asset.
    output_dir.mkdir(parents=True, exist_ok=False)
    try:
        with ExitStack() as stack:
            speeds = stack.enter_context(
                (output_dir / "speed_way_candidates.jsonl").open("w", encoding="utf-8"))
            signs = stack.enter_context(
                (output_dir / "traffic_sign_candidates.jsonl").open("w", encoding="utf-8"))
            sink = _Sink(speeds, signs, max_candidates)
            parser(snapshot, sink)
        if _sha256(snapshot) != initial_sha:
            raise ReferenceError("Source changed while parsing; reference output discarded")
        inventory = {}
        for name in ("speed_way_candidates.jsonl", "traffic_sign_candidates.jsonl"):
            file = output_dir / name
            inventory[name] = {"size_bytes": file.stat().st_size,
                               "sha256": _sha256(file)}
        manifest = {
            "format": FORMAT,
            "status": "UNVERIFIED_OSM_REFERENCE_ONLY",
            "source_snapshot": {
                "filename": snapshot.name, "source_uri": source_uri,
                "sha256": initial_sha, "size_bytes": snapshot.stat().st_size,
                "license": "ODbL-1.0",
                "attribution": "© OpenStreetMap contributors",
            },
            "counts": sink.counts,
            "files": inventory,
            "prohibitions": {
                "approved_speed_limits": False,
                "approved_sign_coordinates": False,
                "driver_speed_alerts": False,
                "traffic_sign_alerts": False,
                "production_offline_map_package": False,
            },
            "warning": "OSM way tags are not legal limits; OSM sign nodes are not verified physical surveys. Ways/relations have NO physical sign coordinates.",
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8")
        if archive is not None:
            archive.parent.mkdir(parents=True, exist_ok=True)
            try:
                with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as zipf:
                    for name in ("manifest.json", "speed_way_candidates.jsonl",
                                 "traffic_sign_candidates.jsonl"):
                        zipf.write(output_dir / name, arcname=name)
                    sha_lines = [
                        f"{_sha256(output_dir / name)}  {name}"
                        for name in ("manifest.json", "speed_way_candidates.jsonl",
                                     "traffic_sign_candidates.jsonl")
                    ]
                    zipf.writestr("SHA256SUMS", "\n".join(sha_lines) + "\n")
            except Exception:
                archive.unlink(missing_ok=True)
                raise
        return manifest
    except Exception:
        shutil.rmtree(output_dir)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--source-uri", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--max-candidates", type=int, default=MAX_CANDIDATES)
    args = parser.parse_args()
    report = extract_reference(args.input, args.expected_sha256, args.source_uri,
                               args.output_dir, args.max_candidates, args.archive)
    print(json.dumps({"status": report["status"], "counts": report["counts"],
                      "sha256": report["source_snapshot"]["sha256"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
