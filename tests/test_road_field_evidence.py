"""Synthetic-only regression tests: even complete packets NEVER approve driving data."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from extract_osm_road_reference import extract_reference
from build_road_review_queues import build_review_queues
from review_road_field_evidence import (
    EvidenceError, audit_evidence, digest, geometry_digest, read_queue,
)


def jsonbytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False).encode()


class FieldEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        fixture = ROOT / "tests/fixtures/reference_only_synthetic.osm"
        reference = self.root / "reference"
        extract_reference(fixture, digest(fixture.read_bytes()),
                          "https://example.org/test-only/synthetic.osm", reference)
        self.queue = self.root / "queues.zip"
        build_review_queues(reference, self.root / "queues", archive=self.queue)
        self.queue_sha = digest(self.queue.read_bytes())
        self.manifest_sha = read_queue(self.queue, self.queue_sha)[1]
        self.photo_root = self.root / "photos"
        self.photo_root.mkdir()
        self.photo_bytes = b"\xff\xd8\xff\xe0NAVITAXI-SYNTHETIC-TEST-ONLY"
        (self.photo_root / "test.jpg").write_bytes(self.photo_bytes)
        self.geometry = {"type": "LineString", "coordinates": [[0, 0], [0.001, 0]]}
        self.packet = {
            "format": "navitaxi-independent-road-evidence/v1",
            "source_review_manifest_sha256": self.manifest_sha,
            "sign_evidence": [{
                "review_id": "osm:node:11@1",
                "evidence_uri": "https://survey.example.org/sign/11",
                "surveyor": "synthetic-surveyor",
                "reviewer": "synthetic-independent-reviewer",
                "observed_at": "2026-11-14T08:00:00+07:00",
                "reviewed_at": "2026-11-14T10:00:00+07:00",
                "sign_code": "P.127",
                "latitude": 0.0, "longitude": 0.0,
                "gps_accuracy_m": 4.0, "bearing_degrees": 90.0,
                "direction": "forward", "related_osm_way_id": 101,
                "road_geometry": self.geometry,
                "road_geometry_sha256": geometry_digest(self.geometry),
                "road_geometry_evidence_uri": "https://survey.example.org/road/101",
                "road_direction_evidence_note": "Synthetic bearing check only",
                "photo": {
                    "path": "test.jpg", "sha256": digest(self.photo_bytes),
                    "mime_type": "image/jpeg", "license": "TEST-ONLY"
                },
            }],
            "speed_evidence": [{
                "review_id": "osm:way:101@1", "osm_way_id": 101,
                "evidence_uri": "https://survey.example.org/road/101",
                "inspector": "synthetic-surveyor",
                "reviewer": "synthetic-independent-reviewer",
                "observed_at": "2026-11-14T08:00:00+07:00",
                "reviewed_at": "2026-11-14T10:00:00+07:00",
                "direction": "forward", "vehicle_class": "taxi",
                "speed_kmh": 60,  # deliberately NOT from the synthetic 30 mph OSM tag
                "road_geometry": self.geometry,
                "road_geometry_sha256": geometry_digest(self.geometry),
                "road_geometry_evidence_uri": "https://survey.example.org/road/101",
                "road_context": {
                    "inside_built_up_area": False,
                    "carriageway_type": "undivided",
                    "posted_sign_status": "observed"
                },
                "sign_evidence_ids": ["osm:node:11@1"],
                "sign_applicability_note": "Synthetic roadway relevance only",
                "legal": {
                    "official_uri": "https://congbao.chinhphu.vn/van-ban/example",
                    "document_id": "SYNTHETIC-NOT-LAW",
                    "clause": "SYNTHETIC",
                    "effective_from": "2025-01-01",
                    "checked_at": "2026-11-14T09:00:00+07:00",
                    "applicability_note": "Only synthetic test legal text; never authoritative."
                },
            }],
        }

    def audit(self, packet=None, sha=None):
        packet_path = self.root / "packet.json"
        packet_path.write_bytes(jsonbytes(self.packet if packet is None else packet))
        return audit_evidence(self.queue, sha or self.queue_sha, packet_path,
                              self.photo_root)

    def test_valid_synthetic_paperwork_still_authorizes_nothing(self):
        result = self.audit()
        self.assertEqual(result["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(result["ready_for_independent_human_review"], 2)
        self.assertEqual(result["rejected_records"], 0)
        self.assertEqual(result["queue_records"]["signs"], 4)
        self.assertEqual(result["queue_records"]["speed_ways"], 1)
        self.assertEqual(result["approved_legal_speeds"], 0)
        self.assertEqual(result["approved_physical_sign_coordinates"], 0)
        self.assertFalse(result["driver_alerts_allowed"])
        self.assertFalse(result["production_database_authorized"])
        self.assertTrue(all(not x["legally_or_physically_verified"]
                            for x in result["results"]))

    def test_reference_zip_must_match_independently_pinned_digest(self):
        with self.assertRaisesRegex(EvidenceError, "REVIEW_ZIP_SHA256_MISMATCH"):
            self.audit(sha="f" * 64)

    def test_reference_manifest_must_bind_evidence(self):
        packet = deepcopy(self.packet)
        packet["source_review_manifest_sha256"] = "0" * 64
        with self.assertRaisesRegex(EvidenceError, "UNBOUND_EVIDENCE_PACKET"):
            self.audit(packet)

    def test_sign_is_never_inferred_from_osm_way_point(self):
        packet = deepcopy(self.packet)
        packet["sign_evidence"][0]["review_id"] = "osm:way:101@1"
        packet["speed_evidence"] = []  # isolate source-object type from linked speed
        result = self.audit(packet)
        # Even a manually claimed point cannot be treated as a surveyed approval.
        self.assertEqual(result["approved_physical_sign_coordinates"], 0)
        self.assertEqual(result["ready_for_independent_human_review"], 1)
        self.assertFalse(result["driver_alerts_allowed"])

    def test_malformed_or_unknown_sign_code_is_rejected(self):
        for code in ("yes", "maxspeed", "P.127;DROP", "", "127"):
            with self.subTest(code=code):
                packet = deepcopy(self.packet)
                packet["sign_evidence"][0]["sign_code"] = code
                packet["speed_evidence"] = []
                self.assertEqual(self.audit(packet)["rejected_records"], 1)

    def test_gps_accuracy_bearing_and_wgs84_are_mandatory(self):
        for field, value in (("latitude", 95), ("longitude", -181),
                             ("gps_accuracy_m", 0), ("gps_accuracy_m", 60),
                             ("bearing_degrees", 360)):
            with self.subTest(field=field, value=value):
                packet = deepcopy(self.packet)
                packet["sign_evidence"][0][field] = value
                packet["speed_evidence"] = []
                self.assertEqual(self.audit(packet)["rejected_records"], 1)

    def test_photo_bytes_must_match_sha256_and_license(self):
        for key, value in (("sha256", "0" * 64),
                           ("path", "../secrets.jpg"),
                           ("license", "unknown")):
            with self.subTest(key=key):
                packet = deepcopy(self.packet)
                packet["sign_evidence"][0]["photo"][key] = value
                packet["speed_evidence"] = []
                self.assertEqual(self.audit(packet)["rejected_records"], 1)

    def test_sign_must_be_close_to_independently_supplied_geometry(self):
        packet = deepcopy(self.packet)
        packet["sign_evidence"][0]["latitude"] = 1.0
        self.assertIn("SURVEY_POINT_NOT_NEAR_RELATED_ROAD",
                      self.audit(packet)["results"][0]["reasons"])

    def test_only_official_legal_citations_are_structurally_accepted(self):
        for url in ("https://wiki.openstreetmap.org/wiki/Speed_limits",
                    "http://congbao.chinhphu.vn/van-ban/demo",
                    "https://someblog.example.com/guess"):
            with self.subTest(url=url):
                packet = deepcopy(self.packet)
                packet["speed_evidence"][0]["legal"]["official_uri"] = url
                self.assertEqual(self.audit(packet)["rejected_records"], 1)

    def test_legal_effective_dates_and_vehicle_direction_must_match(self):
        changes = [
            ("legal", "effective_from", "2026-11-15"),
            ("road_context", "posted_sign_status", "unknown"),
            (None, "vehicle_class", ""),
            (None, "direction", "both"),
            (None, "speed_kmh", 0),
            (None, "osm_way_id", 100),
        ]
        for parent, key, value in changes:
            with self.subTest(key=key, value=value):
                packet = deepcopy(self.packet)
                target = packet["speed_evidence"][0]
                (target[parent] if parent else target)[key] = value
                self.assertEqual(self.audit(packet)["rejected_records"], 1)

    def test_untrusted_reviewer_self_attestation_rejected(self):
        packet = deepcopy(self.packet)
        packet["sign_evidence"][0]["reviewer"] = "synthetic-surveyor"
        packet["speed_evidence"] = []
        self.assertEqual(self.audit(packet)["rejected_records"], 1)

    def test_duplicate_evidence_ids_do_not_silently_authorize(self):
        packet = deepcopy(self.packet)
        packet["sign_evidence"].append(deepcopy(packet["sign_evidence"][0]))
        result = self.audit(packet)
        self.assertEqual(result["rejected_records"], 1)
        self.assertFalse(result["driver_alerts_allowed"])

    def test_duplicated_sign_position_and_code_are_flagged(self):
        packet = deepcopy(self.packet)
        second = deepcopy(packet["sign_evidence"][0])
        second["review_id"] = "osm:node:12@1"
        packet["sign_evidence"].append(second)
        result = self.audit(packet)
        self.assertIn("POSSIBLE_DUPLICATE_PHYSICAL_SIGN",
                      result["results"][1]["reasons"])
        self.assertEqual(result["rejected_records"], 1)

    def test_wrong_geometry_digest_rejected(self):
        packet = deepcopy(self.packet)
        packet["speed_evidence"][0]["road_geometry_sha256"] = "f" * 64
        self.assertEqual(self.audit(packet)["rejected_records"], 1)

    def test_no_real_evidence_is_not_approval(self):
        packet = deepcopy(self.packet)
        packet["sign_evidence"] = []
        packet["speed_evidence"] = []
        result = self.audit(packet)
        self.assertEqual(result["ready_for_independent_human_review"], 0)
        self.assertFalse(result["driver_alerts_allowed"])
        self.assertEqual(result["approved_legal_speeds"], 0)

    def test_osm_raw_speed_does_not_populate_legal_speed(self):
        _, _, (_, speeds) = read_queue(self.queue, self.queue_sha)
        self.assertEqual(speeds["osm:way:101@1"]["raw_maxspeed"], "30 mph")
        packet = deepcopy(self.packet)
        packet["speed_evidence"][0].pop("speed_kmh")
        result = self.audit(packet)
        self.assertEqual(result["rejected_records"], 1)
        self.assertEqual(result["approved_legal_speeds"], 0)

    def test_observed_speed_sign_must_exist_and_match_direction_and_way(self):
        scenarios = (
            ("unknown id", lambda p: p["speed_evidence"][0].update(
                sign_evidence_ids=["osm:node:999999@1"])),
            ("wrong road", lambda p: p["sign_evidence"][0].update(
                related_osm_way_id=202)),
            ("wrong direction", lambda p: p["sign_evidence"][0].update(
                direction="backward")),
            ("missing sign", lambda p: p.update(sign_evidence=[])),
            ("rejected sign", lambda p: p["sign_evidence"][0]["photo"].update(
                sha256="0" * 64)),
        )
        for label, change in scenarios:
            with self.subTest(label=label):
                packet = deepcopy(self.packet)
                change(packet)
                report = self.audit(packet)
                speed_result = [x for x in report["results"]
                                if x["kind"] == "speed"][0]
                self.assertEqual(speed_result["status"], "REJECTED")
                self.assertIn("SIGN_EVIDENCE_MISSING_REJECTED_OR_WRONG_ROAD_DIRECTION",
                              speed_result["reasons"])
                self.assertEqual(report["approved_legal_speeds"], 0)

    def test_none_confirmed_sign_status_cannot_include_sign_ids(self):
        packet = deepcopy(self.packet)
        packet["speed_evidence"][0]["road_context"]["posted_sign_status"] = "none_confirmed"
        result = self.audit(packet)
        self.assertIn("NO_POSTED_SIGN_BUT_SIGN_IDS_PRESENT",
                      result["results"][-1]["reasons"])
        self.assertEqual(result["rejected_records"], 1)



if __name__ == "__main__":
    unittest.main()
