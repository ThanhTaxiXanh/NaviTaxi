#!/usr/bin/env python3
"""PMTiles v3 fixture header/directory/metadata/checksum validator, no extra packages."""
import argparse
import gzip
import hashlib
import json
import struct
from pathlib import Path

def read_varint(data, pos):
    out = 0
    for index in range(10):
        if pos >= len(data):
            raise ValueError("truncated directory varint")
        value = data[pos]
        pos += 1
        out |= (value & 127) << (7 * index)
        if not value & 128:
            return out, pos
    raise ValueError("varint overrun")

def read_pmtiles(data):
    if len(data) < 127 or data[:8] != b"PMTiles\x03":
        raise ValueError("not a PMTiles v3 archive")
    root_start, root_len, meta_start, meta_len, leaf_start, leaf_len, tile_start, tile_len, n_addr, n_entries, n_contents = struct.unpack_from("<11Q", data, 8)
    for start, count in [(root_start, root_len), (meta_start, meta_len),
                         (tile_start, tile_len)]:
        if count == 0 or start < 127 or start + count > len(data):
            raise ValueError("invalid PMTiles section bounds")
    if root_start + root_len > 16384:
        raise ValueError("root not in first 16KB")
    if data[96:102] != bytes([1, 2, 2, 1, 0, 0]):
        raise ValueError("unexpected compression, tile type or zoom")
    if (n_addr, n_entries, n_contents, leaf_len) != (1, 1, 1, 0):
        raise ValueError("synthetic fixture must have exactly one tile")
    directory = gzip.decompress(data[root_start:root_start + root_len])
    pos, items = 0, []
    for _ in range(5):
        value, pos = read_varint(directory, pos)
        items.append(value)
    if items != [1, 0, 1, tile_len, 1]:
        raise ValueError("invalid directory")
    metadata = json.loads(gzip.decompress(data[meta_start:meta_start + meta_len]))
    if len(metadata["vector_layers"]) != 1 or metadata["vector_layers"][0]["id"] != "demo_grid":
        raise ValueError("invalid MVT metadata")
    payload = gzip.decompress(data[tile_start:tile_start + tile_len])
    if b"demo_grid" not in payload:
        raise ValueError("MVT layer missing")
    return {"tile_count": 1, "layer": "demo_grid",
            "tile_payload_bytes": len(payload), "metadata": metadata}

def validate(package, manifest):
    content = package.read_bytes()
    meta = json.loads(manifest.read_text("utf-8"))
    if meta["file"] != package.name or meta["size_bytes"] != len(content):
        raise ValueError("manifest size/path mismatch")
    if meta["sha256"] != hashlib.sha256(content).hexdigest():
        raise ValueError("SHA-256 mismatch")
    if meta["is_real_map"] is not False or meta["has_verified_signs"] is not False \
            or meta["has_verified_speed_limits"] is not False:
        raise ValueError("synthetic fixture must not claim real road/sign data")
    return {"size_bytes": len(content), "sha256": meta["sha256"], **read_pmtiles(content)}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", type=Path,
        default=Path("app/src/main/assets/pmtiles/synthetic_test.pmtiles"))
    ap.add_argument("--manifest", type=Path,
        default=Path("app/src/main/assets/pmtiles/synthetic_manifest.json"))
    args = ap.parse_args()
    result = validate(args.package, args.manifest)
    print(json.dumps({k: v for k, v in result.items() if k != "metadata"}, indent=2))
