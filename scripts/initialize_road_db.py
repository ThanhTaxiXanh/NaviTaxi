#!/usr/bin/env python3
"""Create an EMPTY road-intelligence SQLite DB. No synthetic road records shipped."""
import argparse
from pathlib import Path
import sqlite3

SCHEMA = Path(__file__).resolve().parents[1] / "data/road_intelligence/schema.sql"

def initialize(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    # Avoid overwriting a possibly important existing user/database file.
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing DB: {output}")
    try:
        with sqlite3.connect(output) as connection:
            connection.executescript(SCHEMA.read_text(encoding="utf-8"))
            connection.execute("PRAGMA foreign_keys=ON")
            check = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if check != "ok":
                raise RuntimeError("SQLite integrity_check failed: " + check)
            for table in ("road_segments", "traffic_signs", "data_sources"):
                count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                if count != 0:
                    raise RuntimeError("New DB contains unexpected records")
    except Exception:
        output.unlink(missing_ok=True)
        raise

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    initialize(args.output)
    print(f"Created empty road-intelligence DB: {args.output} ({args.output.stat().st_size} bytes)")
