#!/usr/bin/env python3
"""Find speed-limit, traffic-sign and embedded geo assets in project files or APK.

Report exact relative tree paths and, for APK, exact unambiguous internal entry paths.
Do not make up an asset when no actual data exists.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import zipfile

DATA_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".realm", ".geojson",
                 ".json", ".pbf", ".bin", ".csv", ".pmtiles"}
CODE_SUFFIXES = {".kt", ".java", ".smali"}
CODE_PATTERN = re.compile(
    r"(?i)(maxspeed|traffic_sign|speed.limit|speed_kmh|byteArrayOf|new byte\s*\[\s*\]|\.array-data)"
)
SKIP_DIRS = {".git", ".gradle", ".idea", "__pycache__", "build", ".venv"}

def relevant_asset_path(path: str) -> bool:
    parts = path.replace("\\", "/").strip("/").split("/")
    for index, part in enumerate(parts):
        if part == "assets" or (part == "res" and index + 1 < len(parts)
                                 and parts[index + 1] in {"raw", "assets"}):
            return True
    return False

def db_summary(path: Path):
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            tables = {}
            for (table,) in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
                cols = [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]
                # Avoid arbitrary large scans: COUNT is for local ordinary DB.
                count = connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                tables[table] = {"columns": cols, "row_count": count}
            return tables
        finally:
            connection.close()
    except (sqlite3.Error, OSError) as exc:
        return {"error": str(exc)}

def shape_summary(path: Path):
    if path.suffix.lower() not in {".json", ".geojson"}:
        return None
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(parsed, dict):
            return {"type": parsed.get("type", "object"), "keys": list(parsed)[:25],
                    "feature_count": len(parsed.get("features", [])) if isinstance(parsed.get("features"), list) else None}
        return {"type": type(parsed).__name__, "length": len(parsed)}
    except (ValueError, UnicodeError, OSError) as exc:
        return {"parse_error": str(exc)}

def audit(root: Path, apk: Path | None = None) -> dict:
    results = {"root": str(root.resolve()), "assets": [], "embedded_code_hits": [],
               "apk": str(apk.resolve()) if apk else None, "apk_assets": []}
    for file in root.rglob("*"):
        if not file.is_file():
            continue
        relative = file.relative_to(root)
        if SKIP_DIRS.intersection(relative.parts):
            continue
        rel = relative.as_posix()
        if relevant_asset_path(rel) and file.suffix.lower() in DATA_SUFFIXES:
            entry = {"path": rel, "size_bytes": file.stat().st_size,
                     "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}
            if file.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
                entry["sqlite_tables"] = db_summary(file)
            shape = shape_summary(file)
            if shape is not None:
                entry["json_shape"] = shape
            results["assets"].append(entry)
        if file.suffix.lower() in CODE_SUFFIXES:
            try:
                for number, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
                    if CODE_PATTERN.search(line):
                        results["embedded_code_hits"].append(
                            {"path": rel, "line": number, "snippet": line.strip()[:240]})
            except (OSError, UnicodeError):
                pass
    if apk:
        with zipfile.ZipFile(apk) as archive:
            for info in archive.infolist():
                path = info.filename
                if not info.is_dir() and relevant_asset_path(path) and (
                    Path(path).suffix.lower() in DATA_SUFFIXES
                ):
                    blob = archive.read(info)
                    results["apk_assets"].append({
                        "apk_internal_path": path,
                        "size_bytes": info.file_size,
                        "sha256": hashlib.sha256(blob).hexdigest()
                    })
            for path in archive.namelist():
                if path.endswith(".smali") or path.endswith(".java"):
                    for number, line in enumerate(archive.read(path).decode("utf-8", "replace").splitlines(), 1):
                        if CODE_PATTERN.search(line):
                            results["embedded_code_hits"].append({
                                "path": f"APK!/{path}", "line": number, "snippet": line.strip()[:240]})
    results["assets"].sort(key=lambda e: e["path"])
    results["apk_assets"].sort(key=lambda e: e["apk_internal_path"])
    return results

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--apk", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    data = audit(args.root.resolve(), args.apk)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Source assets: {len(data['assets'])}; APK assets: {len(data['apk_assets'])}; code hits: {len(data['embedded_code_hits'])}")
    print(f"Report: {args.out}")
