"""Road candidate review must never approve invented source speed or sign data."""
import sqlite3
import sys
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from initialize_road_db import initialize
from review_road_candidate import audit_candidate


class RoadCandidateAuditTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "candidate.db"
        initialize(self.db)

    def insert_test_only_records(self):
        """Artificial test records only; NEVER approved physical road observations."""
        con = sqlite3.connect(self.db)
        con.execute("PRAGMA foreign_keys=ON")
        con.execute(
            "INSERT INTO data_sources(source_id,provider,source_uri,license,acquired_at,checksum_sha256) "
            "VALUES(?,?,?,?,?,?)",
            ("unittest-only", "synthetic", "https://example.org/test-source", "TEST_ONLY",
             "2026-11-14", "0" * 64),
        )
        con.execute(
            "INSERT INTO road_segments(segment_id,direction,speed_kmh,geometry_geojson,"
            "min_lon,max_lon,min_lat,max_lat,source_id,observed_at,verified_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            ("test-way", "forward", 50,
             '{"type":"LineString","coordinates":[[0,0],[1,1]]}',
             0, 1, 0, 1, "unittest-only", "2026-11-14", "2026-11-14"),
        )
        con.execute(
            "INSERT INTO traffic_signs(sign_id,sign_code,latitude,longitude,direction,"
            "source_id,observed_at,verified_at) VALUES(?,?,?,?,?,?,?,?)",
            ("test-sign", "TEST_ONLY", 0, 0, "unknown",
             "unittest-only", "2026-11-14", "2026-11-14"),
        )
        con.commit()
        con.close()

    def test_empty_schema_has_no_approvable_geodata(self):
        report = audit_candidate(self.db)
        self.assertEqual(report["status"], "EMPTY_DATABASE")
        self.assertEqual(report["counts"]["road_segments"], 0)
        self.assertEqual(report["counts"]["traffic_signs"], 0)
        self.assertEqual(report["issues"], [])
        self.assertFalse(report["driver_speed_alerts_allowed"])
        self.assertFalse(report["physical_sign_alerts_allowed"])
        self.assertFalse(report["approval_pin_created"])

    def test_synthetics_are_candidate_only_even_with_license_strings(self):
        self.insert_test_only_records()
        report = audit_candidate(self.db)
        self.assertEqual(report["status"], "CANDIDATE_REQUIRES_INDEPENDENT_FIELD_REVIEW")
        self.assertEqual(report["counts"]["road_segments"], 1)
        self.assertEqual(report["counts"]["traffic_signs"], 1)
        self.assertFalse(report["driver_speed_alerts_allowed"])
        self.assertFalse(report["physical_sign_alerts_allowed"])
        self.assertEqual(len(report["sha256"]), 64)

    def test_missing_field_verification_or_bad_evidence_uri_is_rejected(self):
        self.insert_test_only_records()
        con = sqlite3.connect(self.db)
        con.execute("UPDATE road_segments SET verified_at=NULL")
        con.execute("UPDATE data_sources SET source_uri='file:///untrusted'")
        con.commit()
        con.close()
        report = audit_candidate(self.db)
        self.assertEqual(report["status"], "REJECTED")
        self.assertTrue(any("Source" in issue for issue in report["issues"]))
        self.assertTrue(any("Road" in issue for issue in report["issues"]))

    def test_impossible_calendar_dates_are_rejected(self):
        self.insert_test_only_records()
        con = sqlite3.connect(self.db)
        con.execute("UPDATE road_segments SET verified_at='2026-02-31'")
        con.commit()
        con.close()
        report = audit_candidate(self.db)
        self.assertEqual(report["status"], "REJECTED")
        self.assertTrue(any("Road" in issue for issue in report["issues"]))

    def test_mismatched_spatial_index_is_rejected(self):
        self.insert_test_only_records()
        con = sqlite3.connect(self.db)
        con.execute("DELETE FROM traffic_signs_rtree")
        con.commit()
        con.close()
        report = audit_candidate(self.db)
        self.assertEqual(report["status"], "REJECTED")
        self.assertTrue(any("RTree" in issue or "spatial" in issue for issue in report["issues"]))

    def test_sign_spatial_index_shifted_by_fifty_metres_is_rejected(self):
        self.insert_test_only_records()
        con = sqlite3.connect(self.db)
        # The survey record is at (0, 0), but the index falsely plots it
        # around 55m east. The previous 0.001-degree tolerance accepted this.
        con.execute("UPDATE traffic_signs_rtree SET min_lon=?,max_lon=?",
                    (0.0005, 0.0005))
        con.commit()
        con.close()
        report = audit_candidate(self.db)
        self.assertEqual(report["status"], "REJECTED")
        self.assertTrue(any("Sign" in issue and "RTree" in issue
                            for issue in report["issues"]))

    def test_road_spatial_index_shifted_by_fifty_metres_is_rejected(self):
        self.insert_test_only_records()
        con = sqlite3.connect(self.db)
        con.execute("UPDATE road_segments_rtree SET min_lon=0.0005")
        con.commit()
        con.close()
        report = audit_candidate(self.db)
        self.assertEqual(report["status"], "REJECTED")
        self.assertTrue(any("Road" in issue and "RTree" in issue
                            for issue in report["issues"]))

    def test_padded_road_bbox_with_matching_rtree_is_rejected(self):
        self.insert_test_only_records()
        con = sqlite3.connect(self.db)
        # Trigger keeps RTree consistent with the wrong, inflated DB bounds.
        # Its LineString is still only from (0,0) to (1,1).
        con.execute("UPDATE road_segments SET min_lon=-0.02,max_lon=1.02")
        con.commit()
        con.close()
        report = audit_candidate(self.db)
        self.assertEqual(report["status"], "REJECTED")
        self.assertTrue(any("geometry" in issue for issue in report["issues"]))

    def test_genuine_sqlite_float32_rtree_rounding_remains_valid(self):
        self.insert_test_only_records()
        con = sqlite3.connect(self.db)
        line = ('{"type":"LineString","coordinates":'
                '[[105.123456789,21.123456789],[105.12398765,21.12398765]]}')
        con.execute(
            "UPDATE road_segments SET geometry_geojson=?,min_lon=?,"
            "max_lon=?,min_lat=?,max_lat=?",
            (line, 105.123456789, 105.12398765, 21.123456789, 21.12398765),
        )
        con.execute("UPDATE traffic_signs SET latitude=?,longitude=?",
                    (21.123456789, 105.123456789))
        con.commit()
        con.close()
        report = audit_candidate(self.db)
        self.assertEqual(report["status"],
                         "CANDIDATE_REQUIRES_INDEPENDENT_FIELD_REVIEW")
        self.assertEqual(report["issues"], [])
        self.assertFalse(report["driver_speed_alerts_allowed"])
        self.assertFalse(report["physical_sign_alerts_allowed"])

    def test_unhashed_wal_is_rejected_and_never_replayed(self):
        sidecar = Path(str(self.db) + "-wal")
        sidecar.write_bytes(b"malformed-unapproved-journal")
        report = audit_candidate(self.db)
        self.assertEqual(report["status"], "REJECTED")
        self.assertTrue(any("sidecar" in issue for issue in report["issues"]))

    def test_corrupt_candidate_and_missing_database_are_rejected(self):
        self.db.write_bytes(b"not sqlite")
        self.assertEqual(audit_candidate(self.db)["status"], "REJECTED")
        self.db.unlink()
        self.assertEqual(audit_candidate(self.db)["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
