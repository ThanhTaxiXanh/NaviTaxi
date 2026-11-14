#!/usr/bin/env python3
"""Archive every discovered geospatial asset and a machine-verifiable inventory."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

from audit_road_assets import audit

SCHEMA_REL = "data/road_intelligence/schema.sql"

def package(root: Path, output: Path, apk: Path | None = None) -> dict:
    root = root.resolve()
    data = audit(root, apk)
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    entries = {}
    for a in data["assets"]:
        path = root / a["path"]
        if path.resolve() == output:
            continue
        entries["project/" + a["path"]] = path.read_bytes()
    schema = root / SCHEMA_REL
    if schema.is_file():
        entries["project/" + SCHEMA_REL] = schema.read_bytes()
    if apk:
        with zipfile.ZipFile(apk) as source:
            for a in data["apk_assets"]:
                entries["apk/" + a["apk_internal_path"]] = source.read(a["apk_internal_path"])
    inventory = [
        {"path": path, "size_bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}
        for path, blob in sorted(entries.items())
    ]
    manifest = {"format": "navitaxi-road-archive/v1",
                "real_geospatial_asset_count": len(data["assets"]) + len(data["apk_assets"]),
                "entries": inventory,
                "warning": "Empty or provenance-less assets do not demonstrate valid legal speed limits."}
    entries["MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    entries["AUDIT.json"] = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    sha_lines = []
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as dst:
        for name, blob in sorted(entries.items()):
            dst.writestr(name, blob)
            sha_lines.append(hashlib.sha256(blob).hexdigest() + "  " + name)
        dst.writestr("SHA256SUMS", "\n".join(sha_lines) + "\n")
    return {"archive": str(output), "bytes": output.stat().st_size, **manifest}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--apk", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = package(args.root, args.output, args.apk)
    print(json.dumps(result, indent=2, ensure_ascii=False))
