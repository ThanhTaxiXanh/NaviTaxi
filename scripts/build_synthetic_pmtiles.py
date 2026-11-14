#!/usr/bin/env python3
"""Reproducible PMTiles v3 synthetic MVT test data. NOT real geographic roads/signs."""
import argparse
import gzip
import hashlib
import json
import struct
from pathlib import Path

def varint(n):
    assert n >= 0
    out = bytearray()
    while n > 127:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)

def field(number, kind, value):
    result = varint((number << 3) | kind)
    if kind == 0:
        return result + varint(value)
    assert kind == 2 and isinstance(value, bytes)
    return result + varint(len(value)) + value

def zigzag(n):
    return (n << 1) ^ (n >> 31)

def line(fid, x1, y1, x2, y2):
    cmds = [9, zigzag(x1), zigzag(y1), 10, zigzag(x2 - x1), zigzag(y2 - y1)]
    return (field(1, 0, fid) + field(3, 0, 2) +
            field(4, 2, b"".join(map(varint, cmds))))

def mvt():
    layer = (field(1, 2, b"demo_grid") +
             field(2, 2, line(1, 0, 2048, 4096, 2048)) +
             field(2, 2, line(2, 2048, 0, 2048, 4096)) +
             field(5, 0, 4096) + field(15, 0, 2))
    return field(3, 2, layer)

def stable_gzip(data):
    # Python 3.11 and 3.12 differ in gzip OS header byte with mtime=0.
    result = bytearray(gzip.compress(data, mtime=0))
    result[9] = 255
    return bytes(result)

def build(output, manifest):
    tile = stable_gzip(mvt())
    root = stable_gzip(b"".join(map(varint, [1, 0, 1, len(tile), 1])))
    metadata = {
        "name": "NaviTaxi synthetic grid test",
        "description": "SYNTHETIC ONLY. No real roads, speed limits or traffic signs.",
        "type": "baselayer", "version": "0.0.1",
        "attribution": "NaviTaxi synthetic fixture, not geographic data",
        "vector_layers": [{
            "id": "demo_grid", "description": "Schematic cross lines; not real streets",
            "minzoom": 0, "maxzoom": 0, "fields": {}
        }]
    }
    meta = stable_gzip(json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode())
    root_start = 127
    meta_start = root_start + len(root)
    tile_start = meta_start + len(meta)
    header = bytearray(127)
    header[:8] = b"PMTiles\x03"
    struct.pack_into("<11Q", header, 8, root_start, len(root), meta_start, len(meta),
                     tile_start, 0, tile_start, len(tile), 1, 1, 1)
    header[96:102] = bytes([1, 2, 2, 1, 0, 0])
    struct.pack_into("<4i", header, 102, -1800000000, -850000000,
                     1800000000, 850000000)
    header[118] = 0
    struct.pack_into("<2i", header, 119, 0, 0)
    archive = bytes(header) + root + meta + tile
    assert len(archive) == tile_start + len(tile) < 16384
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(archive)
    details = {
        "format": "navitaxi-offline-package/v1", "id": "synthetic-grid-test",
        "version": "0.0.1", "origin": "created by scripts/build_synthetic_pmtiles.py",
        "license": "NaviTaxi own synthetic test-only content",
        "is_real_map": False, "has_verified_speed_limits": False,
        "has_verified_signs": False, "tile_type": "mvt",
        "layer": "demo_grid", "minzoom": 0, "maxzoom": 0,
        "file": output.name, "size_bytes": len(archive),
        "sha256": hashlib.sha256(archive).hexdigest()
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(details, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    return details

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path,
        default=Path("app/src/main/assets/pmtiles/synthetic_test.pmtiles"))
    ap.add_argument("--manifest", type=Path,
        default=Path("app/src/main/assets/pmtiles/synthetic_manifest.json"))
    args = ap.parse_args()
    print(json.dumps(build(args.output, args.manifest), indent=2))
