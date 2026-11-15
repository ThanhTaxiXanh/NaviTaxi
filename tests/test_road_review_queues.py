"""Synthetic-only tests for field/legal review queues: NEVER driver approvals."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from extract_osm_road_reference import extract_reference
from audit_osm_reference_quality import AuditError
from build_road_review_queues import (
    build_review_queues, ReviewQueueError, SIGN_FILE, SPEED_FILE,
    SIGN_COLUMNS, SPEED_COLUMNS, _safe_csv,
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ReviewQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.original = ROOT / "tests/fixtures/reference_only_synthetic.osm"
        self.reference = self.home / "reference"
        extract_reference(self.original, sha(self.original.read_bytes()),
                          "https://example.org/test-only/synthetic.osm",
                          self.reference)
        self.output = self.home / "survey-queue"
        self.zip = self.home / "survey-queue.zip"

    def build(self, **overrides):
        return build_review_queues(
            self.reference, overrides.get("output_dir", self.output),
            overrides.get("receipt_path"), overrides.get("archive", self.zip))

    def csv_rows(self, name):
        with (self.output / name).open("r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def test_sign_node_coordinates_are_only_unverified_and_ways_have_none(self):
        result = self.build()
        self.assertEqual(result["review_rows"]["signs"], 4)
        self.assertEqual(result["review_rows"]["speed_ways"], 1)
        self.assertEqual(result["sign_triage"]["NO_VERIFIED_PHYSICAL_POINT"], 2)
        signs = self.csv_rows(SIGN_FILE)
        self.assertEqual(len(signs), 4)
        self.assertEqual(tuple(signs[0]), SIGN_COLUMNS)
        for row in signs:
            self.assertEqual(row["review_status"], "PENDING_INDEPENDENT_REVIEW")
            self.assertEqual(row["independently_verified"], "FALSE")
            self.assertEqual(row["driver_alert_approved"], "FALSE")
            self.assertEqual(row["survey_latitude_BLANK"], "")
            self.assertEqual(row["survey_longitude_BLANK"], "")
            self.assertEqual(row["survey_bearing_degrees_BLANK"], "")
            self.assertEqual(row["photo_sha256_BLANK"], "")
            if row["osm_type"] != "node":
                self.assertEqual(row["osm_latitude_unverified"], "")
                self.assertEqual(row["osm_longitude_unverified"], "")
            else:
                self.assertNotEqual(row["osm_latitude_unverified"], "")
                self.assertNotEqual(row["osm_longitude_unverified"], "")
        self.assertEqual(result["survey_field_entries_present"], 0)
        self.assertFalse(result["driver_alerts_allowed"])

    def test_speed_rows_keep_raw_tags_no_unreviewed_kmh_or_defaults(self):
        result = self.build()
        self.assertEqual(result["speed_triage"],
                         {"CONTEXTUAL_DIRECTIONAL_OR_ADVISORY": 1})
        speed = self.csv_rows(SPEED_FILE)
        self.assertEqual(len(speed), 1)
        self.assertEqual(tuple(speed[0]), SPEED_COLUMNS)
        self.assertEqual(speed[0]["raw_maxspeed"], "30 mph")
        self.assertIn("maxspeed:conditional", speed[0]["raw_osm_tags_json"])
        self.assertNotIn("speed_kmh", speed[0])
        self.assertEqual(speed[0]["legal_source_uri_BLANK"], "")
        self.assertEqual(speed[0]["legal_clause_BLANK"], "")
        self.assertEqual(speed[0]["vehicle_class_reviewed_BLANK"], "")
        self.assertEqual(speed[0]["driver_alert_approved"], "FALSE")
        self.assertEqual(result["independently_approved_speed_records"], 0)

    def test_output_zip_checksums_reproducible_provenance(self):
        result = self.build()
        with zipfile.ZipFile(self.zip) as archive:
            self.assertEqual(set(archive.namelist()), {
                "manifest.json", SIGN_FILE, SPEED_FILE,
                "REVIEW_INSTRUCTIONS.txt", "SHA256SUMS"})
            for line in archive.read("SHA256SUMS").decode().splitlines():
                digest, name = line.split("  ", 1)
                self.assertEqual(digest, sha(archive.read(name)))
            self.assertEqual(json.loads(archive.read("manifest.json")), result)
        self.assertEqual(result["source_snapshot"]["license"], "ODbL-1.0")
        self.assertEqual(result["reference_manifest_sha256"],
                         sha((self.reference / "manifest.json").read_bytes()))
        self.assertTrue(result["review_packets_are_not_production_databases"])

    def test_existing_output_refused_without_overwrite(self):
        self.build()
        with self.assertRaises(FileExistsError):
            self.build()
        self.assertTrue((self.output / "manifest.json").is_file())

    def test_blocked_apk_verified_db_and_existing_archive(self):
        cases = ("app/src/main/assets/reviews", "app/src/main/res/raw/reviews",
                 "data/road_intelligence/reviews")
        for suffix in cases:
            with self.subTest(suffix=suffix):
                with self.assertRaisesRegex(ReviewQueueError, "app or verified"):
                    self.build(output_dir=self.home / suffix)
        self.assertFalse(self.output.exists())

    def test_corrupted_raw_rows_fail_before_emitting_review_queues(self):
        file = self.reference / "speed_way_candidates.jsonl"
        file.write_text(file.read_text().replace("30 mph", "130 mph"))
        with self.assertRaisesRegex(AuditError, "size/SHA256"):
            self.build()
        self.assertFalse(self.output.exists())
        self.assertFalse(self.zip.exists())

    def test_mismatched_acquisition_receipt_rejected(self):
        receipt = self.home / "receipt.json"
        receipt.write_text(json.dumps({
            "sha256": "f" * 64, "driver_alerts_allowed": False,
            "legal_speed_limits_verified": False,
            "physical_sign_coordinates_verified": False,
        }))
        with self.assertRaisesRegex(AuditError, "does not match"):
            self.build(receipt_path=receipt)
        self.assertFalse(self.output.exists())

    def test_spreadsheet_formula_values_are_never_executable(self):
        for raw in ('=HYPERLINK("https://example.org")',
                    '+2+3', '-A1', '@SUM(1,2)', '   =2+2'):
            with self.subTest(raw=raw):
                self.assertTrue(_safe_csv(raw).startswith("'"))
        self.assertEqual(_safe_csv("normal"), "normal")
        self.assertEqual(_safe_csv("a\nb"), "a b")
        self.assertEqual(_safe_csv("a\r\nb"), "a  b")

        # Test real row-level escaping on a legitimate raw reference JSONL.
        file = self.reference / "traffic_sign_candidates.jsonl"
        rows = [json.loads(line) for line in file.read_text().splitlines()]
        rows[0]["tags"]["traffic_sign"] = '=HYPERLINK("https://evil.example")'
        file.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        mfile = self.reference / "manifest.json"
        manifest = json.loads(mfile.read_text())
        manifest["files"][file.name] = {
            "size_bytes": file.stat().st_size, "sha256": sha(file.read_bytes())}
        mfile.write_text(json.dumps(manifest))
        self.build()
        self.assertTrue(self.csv_rows(SIGN_FILE)[0]["raw_traffic_sign"].startswith("'="))

    def test_source_input_overwrite_or_output_inside_reference_prohibited(self):
        with self.assertRaisesRegex(ReviewQueueError, "overwrite source"):
            self.build(output_dir=self.reference / "review-output")
        with self.assertRaisesRegex(ReviewQueueError, "overwrite source"):
            self.build(output_dir=self.reference.parent)


if __name__ == "__main__":
    unittest.main()
