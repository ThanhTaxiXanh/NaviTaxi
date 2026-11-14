"""Raw speed/sign quality inventory guards; all fixtures synthetic, never road law."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from extract_osm_road_reference import extract_reference
from audit_osm_reference_quality import audit_reference, AuditError


class QualityAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = ROOT / "tests/fixtures/reference_only_synthetic.osm"
        self.reference = self.root / "reference"
        sha = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.manifest = extract_reference(
            self.source, sha, "https://example.org/synthetic-only.osm",
            self.reference)

    def write_row_and_rehash(self, name, transform):
        file = self.reference / name
        rows = [json.loads(s) for s in file.read_text().splitlines()]
        transform(rows)
        content = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
        file.write_text(content, encoding="utf-8")
        mfile = self.reference / "manifest.json"
        manifest = json.loads(mfile.read_text())
        manifest["files"][name]["sha256"] = hashlib.sha256(file.read_bytes()).hexdigest()
        manifest["files"][name]["size_bytes"] = file.stat().st_size
        mfile.write_text(json.dumps(manifest), encoding="utf-8")

    def test_reference_quality_counts_and_no_driver_alerts(self):
        result = audit_reference(self.reference)
        self.assertEqual(result["counts"]["speed_way_candidates"], 1)
        self.assertEqual(result["counts"]["sign_node_candidates"], 2)
        self.assertEqual(result["counts"]["sign_way_candidates"], 1)
        self.assertEqual(result["counts"]["sign_relation_candidates"], 1)
        self.assertEqual(result["unverified_osm_sign_node_coordinate_count"], 2)
        self.assertEqual(result["raw_speed_semantics"]["conditional"], 1)
        self.assertEqual(result["raw_speed_semantics"]["mph"], 1)
        self.assertFalse(result["driver_speed_alerts_enabled"])
        self.assertFalse(result["physical_sign_alerts_enabled"])
        self.assertEqual(result["verified_legal_speed_records"], 0)
        self.assertEqual(result["verified_physical_sign_coordinates"], 0)

    def test_corrupted_unpinned_source_rows_rejected(self):
        file = self.reference / "speed_way_candidates.jsonl"
        file.write_text(file.read_text().replace("30 mph", "100 mph"), encoding="utf-8")
        with self.assertRaisesRegex(AuditError, "size/SHA256"):
            audit_reference(self.reference)

    def test_injected_numeric_legal_speed_field_rejected_even_with_updated_hash(self):
        self.write_row_and_rehash("speed_way_candidates.jsonl",
                                  lambda rows: rows[0].update(speed_kmh=50))
        with self.assertRaisesRegex(AuditError, "Unexpected fields"):
            audit_reference(self.reference)

    def test_fake_survey_approval_rejected_even_with_updated_checksum(self):
        self.write_row_and_rehash("traffic_sign_candidates.jsonl",
                                  lambda rows: rows[0].update(
                                      independently_verified_physical_sign=True))
        with self.assertRaisesRegex(AuditError, "falsely claims"):
            audit_reference(self.reference)

    def test_way_coordinate_fabrication_rejected_even_if_tagged(self):
        def fake_point(rows):
            for row in rows:
                if row["osm"]["type"] == "way":
                    row["osm_node_coordinate"] = {"latitude": 21.0, "longitude": 106.0}
                    row["position_type"] = "osm_node_point_unverified"
        self.write_row_and_rehash("traffic_sign_candidates.jsonl", fake_point)
        with self.assertRaisesRegex(AuditError, "fabricates"):
            audit_reference(self.reference)

    def test_source_receipt_matches_complete_snapshot_and_rejects_bad_hash(self):
        receipt = self.root / "receipt.json"
        details = self.manifest["source_snapshot"]
        valid = {
            "sha256": details["sha256"],
            "size_bytes": details["size_bytes"],
            "source_uri": details["source_uri"],
            "filename": details["filename"],
            "driver_alerts_allowed": False,
            "legal_speed_limits_verified": False,
            "physical_sign_coordinates_verified": False,
        }
        receipt.write_text(json.dumps(valid))
        self.assertEqual(audit_reference(self.reference, receipt)["counts"][
            "speed_way_candidates"], 1)
        valid["sha256"] = "f" * 64
        receipt.write_text(json.dumps(valid))
        with self.assertRaisesRegex(AuditError, "does not match source"):
            audit_reference(self.reference, receipt)

    def test_existing_unverified_manifest_does_not_allow_modified_counts(self):
        mfile = self.reference / "manifest.json"
        manifest = json.loads(mfile.read_text())
        manifest["counts"]["speed_way_candidates"] = 9
        mfile.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(AuditError, "count mismatch"):
            audit_reference(self.reference)

    def test_source_duplicate_identifiers_rejected(self):
        def duplicate(rows):
            rows.append(dict(rows[0]))
        self.write_row_and_rehash("speed_way_candidates.jsonl", duplicate)
        with self.assertRaisesRegex(AuditError, "Duplicate speed source"):
            audit_reference(self.reference)


if __name__ == "__main__":
    unittest.main()
