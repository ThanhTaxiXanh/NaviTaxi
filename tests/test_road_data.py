import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from initialize_road_db import initialize
from audit_road_assets import audit
from package_road_data import package

class RoadDataTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.db = Path(self.work.name) / "road.db"
        initialize(self.db)
        self.conn = sqlite3.connect(self.db)
        self.addCleanup(self.conn.close)
        self.conn.execute("PRAGMA foreign_keys=ON")

    def source(self):
        self.conn.execute(
            "INSERT INTO data_sources(source_id,provider,source_uri,license,acquired_at,checksum_sha256) VALUES(?,?,?,?,?,?)",
            ("synthetic-fixture","unittest only","test://invalid-not-for-distribution",
             "TEST_ONLY","2000-01-01","0"*64))

    def test_database_starts_empty_and_integrity_ok(self):
        self.assertEqual(self.conn.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        for table in ("data_sources", "road_segments", "traffic_signs"):
            self.assertEqual(self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("PRAGMA user_version").fetchone()[0], 1)

    def test_unknown_source_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO traffic_signs(sign_id,sign_code,latitude,longitude,source_id) VALUES(?,?,?,?,?)",
                ("synthetic","test-sign",0,0,"missing-source"))

    def test_sign_bounds_and_rtree_updates(self):
        self.source()
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO traffic_signs(sign_id,sign_code,latitude,longitude,source_id) VALUES(?,?,?,?,?)",
                ("bad","test",91,0,"synthetic-fixture"))
        self.conn.execute(
            "INSERT INTO traffic_signs(sign_id,sign_code,latitude,longitude,source_id) VALUES(?,?,?,?,?)",
            ("synthetic-sign","test-sign",0,0,"synthetic-fixture"))
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM traffic_signs_rtree").fetchone()[0], 1)
        self.conn.execute("UPDATE traffic_signs SET longitude=12 WHERE sign_id='synthetic-sign'")
        self.assertEqual(self.conn.execute("SELECT min_lon FROM traffic_signs_rtree").fetchone()[0], 12)
        self.conn.execute("DELETE FROM traffic_signs WHERE sign_id='synthetic-sign'")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM traffic_signs_rtree").fetchone()[0], 0)

    def test_road_speed_and_rtree(self):
        self.source()
        statement = """INSERT INTO road_segments(
            segment_id,direction,speed_kmh,geometry_geojson,min_lon,max_lon,min_lat,max_lat,source_id)
            VALUES(?,?,?,?,?,?,?,?,?)"""
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(statement, ("testbad","both",0,'{"type":"LineString","coordinates":[[0,0],[1,1]]}',0,1,0,1,"synthetic-fixture"))
        self.conn.execute(statement, ("testok","forward",50,'{"type":"LineString","coordinates":[[0,0],[1,1]]}',0,1,0,1,"synthetic-fixture"))
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM road_segments_rtree").fetchone()[0], 1)
        self.conn.execute("DELETE FROM road_segments WHERE segment_id='testok'")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM road_segments_rtree").fetchone()[0], 0)

    def test_archive_and_deep_asset_scan(self):
        root = Path(self.work.name) / "project"
        asset = root / "app/src/main/assets/road_intelligence/map.sqlite"
        asset.parent.mkdir(parents=True)
        asset.write_bytes(self.db.read_bytes())
        geojson = root / "res/raw/signs.geojson"
        geojson.parent.mkdir(parents=True)
        geojson.write_text('{"type":"FeatureCollection","features":[]}')
        schema = root / "data/road_intelligence/schema.sql"
        schema.parent.mkdir(parents=True)
        schema.write_bytes((ROOT / "data/road_intelligence/schema.sql").read_bytes())
        discovered = audit(root)
        self.assertEqual(len(discovered["assets"]), 2)
        self.assertIn("sqlite_tables", discovered["assets"][0])
        output = root / "build/road-archive.zip"
        record = package(root, output)
        self.assertEqual(record["real_geospatial_asset_count"], 2)
        with zipfile.ZipFile(output) as z:
            self.assertIn("project/app/src/main/assets/road_intelligence/map.sqlite", z.namelist())
            self.assertIn("project/res/raw/signs.geojson", z.namelist())
            self.assertIn("project/data/road_intelligence/schema.sql", z.namelist())
            self.assertIn("SHA256SUMS", z.namelist())
            manifest = json.loads(z.read("MANIFEST.json"))
            for entry in manifest["entries"]:
                self.assertEqual(hashlib.sha256(z.read(entry["path"])).hexdigest(),
                                 entry["sha256"])

    def test_apk_internal_paths_are_exact(self):
        apk = Path(self.work.name) / "test.apk"
        with zipfile.ZipFile(apk, "w") as z:
            z.writestr("assets/nested/limits.csv", "id,maxspeed\n")
            z.writestr("res/raw/signs.json", "{}")
        result = audit(Path(self.work.name), apk)
        paths = [row["apk_internal_path"] for row in result["apk_assets"]]
        self.assertEqual(paths, ["assets/nested/limits.csv", "res/raw/signs.json"])

if __name__ == "__main__":
    unittest.main()
