"""Synthetic-only regression tests: even complete packets NEVER approve driving data."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
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

    def attach_synthetic_gpx(self, packet=None, data=None):
        """Synthetic GPX never represents a real measured roadside sign."""
        if packet is None:
            packet = self.packet
        if data is None:
            data = (
                b'<?xml version="1.0" encoding="UTF-8"?>'
                b'<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">'
                b'<trk><trkseg><trkpt lat="0.0" lon="0.0">'
                b'<time>2026-11-14T01:00:00Z</time>'
                b'</trkpt></trkseg></trk></gpx>'
            )
        (self.photo_root / "synthetic-track.gpx").write_bytes(data)
        packet["sign_evidence"][0]["gps_track"] = {
            "path": "synthetic-track.gpx", "sha256": digest(data),
            "mime_type": "application/gpx+xml", "license": "TEST-ONLY",
            "source_uri": "https://survey.example.org/independent-gps/11"
        }
        return packet

    def test_optional_original_gnss_file_matches_sign_coordinates_and_time(self):
        packet = self.attach_synthetic_gpx(deepcopy(self.packet))
        report = self.audit(packet)
        self.assertEqual(report["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(report["ready_for_independent_human_review"], 2)
        self.assertEqual(report["approved_physical_sign_coordinates"], 0)
        self.assertFalse(report["driver_alerts_allowed"])

    def test_gnss_track_invalid_point_or_time_is_rejected_not_approved(self):
        changes = {
            "far position": b'<trkpt lat="0.05" lon="0"><time>2026-11-14T01:00:00Z</time></trkpt>',
            "wrong time": b'<trkpt lat="0" lon="0"><time>2026-11-14T04:00:00Z</time></trkpt>',
            "no time": b'<trkpt lat="0" lon="0" />',
            "invalid latitude": b'<trkpt lat="not-a-coordinate" lon="0"><time>2026-11-14T01:00:00Z</time></trkpt>',
            "longitude out of range": b'<trkpt lat="0" lon="200"><time>2026-11-14T01:00:00Z</time></trkpt>',
        }
        for label, point in changes.items():
            with self.subTest(label=label):
                source = (b'<gpx xmlns="http://www.topografix.com/GPX/1/1">'
                          b'<trk><trkseg>' + point +
                          b'</trkseg></trk></gpx>')
                packet = self.attach_synthetic_gpx(deepcopy(self.packet), source)
                report = self.audit(packet)
                self.assertEqual(report["results"][0]["status"], "REJECTED")
                self.assertEqual(report["approved_physical_sign_coordinates"], 0)
                self.assertFalse(report["driver_alerts_allowed"])

    def test_gnss_track_actual_bytes_and_source_uri_required(self):
        for change in ("wrong_sha", "missing_file", "osm_uri", "fake_mime"):
            with self.subTest(change=change):
                packet = self.attach_synthetic_gpx(deepcopy(self.packet))
                gps = packet["sign_evidence"][0]["gps_track"]
                if change == "wrong_sha":
                    gps["sha256"] = "f" * 64
                elif change == "missing_file":
                    gps["path"] = "nonexistent.gpx"
                elif change == "osm_uri":
                    gps["source_uri"] = "https://www.openstreetmap.org/node/11"
                else:
                    gps["mime_type"] = "text/plain"
                report = self.audit(packet)
                self.assertEqual(report["results"][0]["status"], "REJECTED")
                self.assertEqual(report["approved_physical_sign_coordinates"], 0)

    def test_gnss_track_malicious_xml_doctype_refused(self):
        fake = (
            b'<!DOCTYPE gpx [<!ENTITY location SYSTEM "file:///etc/passwd">]>'
            b'<gpx xmlns="http://www.topografix.com/GPX/1/1">'
            b'<wpt lat="0" lon="0"><time>2026-11-14T01:00:00Z</time></wpt>'
            b'</gpx>'
        )
        report = self.audit(self.attach_synthetic_gpx(deepcopy(self.packet), fake))
        self.assertIn("GPS_TRACK_XML_DTD_NOT_ALLOWED",
                      report["results"][0]["reasons"])

    def test_symlinked_photo_parent_rejected_before_human_review(self):
        actual = self.photo_root / "originals"
        actual.mkdir()
        (actual / "real.jpg").write_bytes(self.photo_bytes)
        (self.photo_root / "shortcut").symlink_to(actual, target_is_directory=True)
        packet = deepcopy(self.packet)
        packet["sign_evidence"][0]["photo"]["path"] = "shortcut/real.jpg"
        report = self.audit(packet)
        self.assertIn("SYMLINKED_PRIVATE_EVIDENCE_PATH",
                      report["results"][0]["reasons"])
        self.assertEqual(report["approved_physical_sign_coordinates"], 0)

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
        # Both duplicate records AND the speed citing the sign are quarantined.
        self.assertEqual(result["rejected_records"], 3)
        self.assertEqual(result["ready_for_independent_human_review"], 0)
        self.assertTrue(all(x["status"] == "REJECTED" for x in result["results"]))
        self.assertFalse(result["driver_alerts_allowed"])

    def test_duplicated_sign_position_and_code_are_flagged(self):
        packet = deepcopy(self.packet)
        second = deepcopy(packet["sign_evidence"][0])
        second["review_id"] = "osm:node:12@1"
        packet["sign_evidence"].append(second)
        result = self.audit(packet)
        self.assertIn("POSSIBLE_DUPLICATE_PHYSICAL_SIGN",
                      result["results"][1]["reasons"])
        self.assertIn("POSSIBLE_DUPLICATE_PHYSICAL_SIGN",
                      result["results"][0]["reasons"])
        self.assertEqual(result["rejected_records"], 3)

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


    def test_reused_photo_on_distant_signs_quarantines_all(self):
        packet = deepcopy(self.packet)
        other = deepcopy(packet["sign_evidence"][0])
        other["review_id"] = "osm:node:12@1"
        other["latitude"], other["longitude"] = 1.0, 1.0
        other["road_geometry"] = {
            "type": "LineString",
            "coordinates": [[1.0, 1.0], [1.001, 1.0]]
        }
        other["road_geometry_sha256"] = geometry_digest(other["road_geometry"])
        packet["sign_evidence"].append(other)
        report = self.audit(packet)
        self.assertEqual(report["rejected_records"], 3)
        self.assertEqual(report["ready_for_independent_human_review"], 0)
        for result in report["results"][:2]:
            self.assertIn("REUSED_SIGN_PHOTO_SHA256", result["reasons"])
        self.assertIn("SIGN_EVIDENCE_MISSING_REJECTED_OR_WRONG_ROAD_DIRECTION",
                      report["results"][-1]["reasons"])

    def test_mismatched_sign_and_speed_road_geometry_rejected(self):
        packet = deepcopy(self.packet)
        shape = {
            "type": "LineString",
            "coordinates": [[0.0, 0.0], [0.002, 0.001]]
        }
        packet["sign_evidence"][0]["road_geometry"] = shape
        packet["sign_evidence"][0]["road_geometry_sha256"] = geometry_digest(shape)
        report = self.audit(packet)
        self.assertEqual(report["ready_for_independent_human_review"], 1)
        self.assertEqual(report["rejected_records"], 1)
        self.assertIn("SIGN_AND_SPEED_ROAD_GEOMETRY_DISAGREE",
                      report["results"][-1]["reasons"])

    def test_sign_survey_after_speed_observation_cannot_backfill(self):
        packet = deepcopy(self.packet)
        packet["sign_evidence"][0]["observed_at"] = "2026-11-14T09:00:00+07:00"
        report = self.audit(packet)
        self.assertIn("SIGN_SURVEY_POSTDATES_SPEED_OBSERVATION",
                      report["results"][-1]["reasons"])
        self.assertEqual(report["rejected_records"], 1)
        self.assertFalse(report["driver_alerts_allowed"])

    def test_law_cannot_be_checked_before_road_observation(self):
        packet = deepcopy(self.packet)
        packet["speed_evidence"][0]["legal"]["checked_at"] = (
            "2026-11-14T07:00:00+07:00")
        report = self.audit(packet)
        self.assertIn("LEGAL_CHECK_MUST_FOLLOW_OBSERVATION_AND_PRECEDE_REVIEW",
                      report["results"][-1]["reasons"])
        self.assertEqual(report["rejected_records"], 1)

    def test_expired_legal_rule_is_rejected(self):
        packet = deepcopy(self.packet)
        packet["speed_evidence"][0]["legal"]["effective_to"] = "2026-11-13"
        report = self.audit(packet)
        self.assertIn("LAW_EXPIRED_AT_OBSERVATION",
                      report["results"][-1]["reasons"])

    def test_untrusted_authorization_claims_rejected_at_every_level(self):
        def inject_root(p):
            p["driver_alerts_allowed"] = True
        def inject_sign(p):
            p["sign_evidence"][0]["independently_verified"] = True
        def inject_speed(p):
            p["speed_evidence"][0]["legal"]["production_database_authorized"] = True
        for change in (inject_root, inject_sign, inject_speed):
            with self.subTest(changer=change.__name__):
                packet = deepcopy(self.packet)
                change(packet)
                with self.assertRaisesRegex(
                        EvidenceError, "INPUT_ATTEMPTS_TO_AUTHORIZE_DRIVER_DATA"):
                    self.audit(packet)

    def test_empty_packet_reports_no_evidence_not_ready(self):
        packet = deepcopy(self.packet)
        packet["sign_evidence"] = []
        packet["speed_evidence"] = []
        report = self.audit(packet)
        self.assertEqual(report["status"], "NO_EVIDENCE_TO_REVIEW")
        self.assertEqual(report["ready_for_independent_human_review"], 0)
        self.assertEqual(report["approved_legal_speeds"], 0)

    def test_duplicate_speed_scope_quarantines_both_source_cases(self):
        packet = deepcopy(self.packet)
        first = packet["speed_evidence"][0]
        first["case_id"] = "osm:way:101:taxi:forward:case-a"
        second = deepcopy(first)
        second["case_id"] = "osm:way:101:taxi:forward:case-b"
        second["speed_kmh"] = 50  # contradictory synthetic legal opinions
        packet["speed_evidence"].append(second)
        report = self.audit(packet)
        self.assertEqual(report["rejected_records"], 2)
        self.assertEqual(report["ready_for_independent_human_review"], 1)
        self.assertEqual([row["case_id"] for row in report["results"][1:]],
                         [first["case_id"], second["case_id"]])
        self.assertTrue(all("CONFLICTING_SPEED_SCOPE" in row["reasons"]
                            for row in report["results"][1:]))
        self.assertEqual(report["approved_legal_speeds"], 0)
        self.assertFalse(report["driver_alerts_allowed"])

    def test_opposite_directions_on_same_way_require_distinct_cases(self):
        packet = deepcopy(self.packet)
        first = packet["speed_evidence"][0]
        first["case_id"] = "synthetic-101-forward-taxi"
        opposite = deepcopy(first)
        opposite["case_id"] = "synthetic-101-backward-taxi"
        opposite["direction"] = "backward"
        # The observed forward-facing sign does not establish applicability
        # for opposite-direction travel. No sign is claimed in this test.
        opposite["road_context"]["posted_sign_status"] = "none_confirmed"
        opposite["sign_evidence_ids"] = []
        opposite["sign_applicability_note"] = (
            "Synthetic independent opposite-direction sign absence check.")
        packet["speed_evidence"].append(opposite)
        report = self.audit(packet)
        self.assertEqual(report["ready_for_independent_human_review"], 3)
        self.assertEqual(report["rejected_records"], 0)
        self.assertEqual(report["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(report["results"][1]["case_id"], first["case_id"])
        self.assertEqual(report["results"][2]["case_id"], opposite["case_id"])
        self.assertEqual(report["approved_legal_speeds"], 0)
        self.assertEqual(report["approved_physical_sign_coordinates"], 0)
        self.assertFalse(report["driver_alerts_allowed"])

    def test_vehicle_specific_speed_papers_share_raw_way_not_legal_values(self):
        packet = deepcopy(self.packet)
        first = packet["speed_evidence"][0]
        first["case_id"] = "synthetic-101-taxi"
        other = deepcopy(first)
        other["case_id"] = "synthetic-101-hgv"
        other["vehicle_class"] = "hgv"
        other["speed_kmh"] = 45  # deliberately invented legal-review value
        other["legal"]["clause"] = "SYNTHETIC-HGV-DIFFERENT-CLAUSE"
        packet["speed_evidence"].append(other)
        report = self.audit(packet)
        self.assertEqual(report["ready_for_independent_human_review"], 3)
        self.assertEqual(report["rejected_records"], 0)
        self.assertEqual([x["case_id"] for x in report["results"][1:]],
                         [first["case_id"], other["case_id"]])
        self.assertEqual(report["approved_legal_speeds"], 0)

    def test_repeated_source_without_explicit_case_ids_quarantines_all(self):
        packet = deepcopy(self.packet)
        other = deepcopy(packet["speed_evidence"][0])
        other["direction"] = "backward"
        other["road_context"]["posted_sign_status"] = "none_confirmed"
        other["sign_evidence_ids"] = []
        packet["speed_evidence"].append(other)
        report = self.audit(packet)
        self.assertEqual(report["rejected_records"], 2)
        self.assertTrue(all(
            "REPEATED_SPEED_SOURCE_REQUIRES_CASE_ID" in row["reasons"]
            for row in report["results"][1:]))

    def test_duplicate_speed_case_id_across_classes_quarantines_all(self):
        packet = deepcopy(self.packet)
        first = packet["speed_evidence"][0]
        first["case_id"] = "synthetic-one-id"
        other = deepcopy(first)
        other["vehicle_class"] = "motorcar"
        packet["speed_evidence"].append(other)
        report = self.audit(packet)
        self.assertEqual(report["rejected_records"], 2)
        self.assertTrue(all("DUPLICATE_SPEED_CASE_ID" in row["reasons"]
                            for row in report["results"][1:]))
        self.assertEqual(report["approved_legal_speeds"], 0)

    def test_speed_case_id_cannot_contain_path_or_authorization_injection(self):
        for invalid in ("../unreviewed", "has space", "bad\ncase",
                        "é", "", None, 15, "x" * 129):
            with self.subTest(invalid=invalid):
                packet = deepcopy(self.packet)
                packet["speed_evidence"][0]["case_id"] = invalid
                report = self.audit(packet)
                self.assertEqual(report["rejected_records"], 1)
                self.assertIn("INVALID_SPEED_CASE_ID",
                              report["results"][-1]["reasons"])
                self.assertFalse(report["driver_alerts_allowed"])

    def test_per_way_speed_scope_packet_size_is_bounded(self):
        packet = deepcopy(self.packet)
        first = packet["speed_evidence"][0]
        packet["speed_evidence"] = []
        for i in range(13):
            case = deepcopy(first)
            case["case_id"] = f"synthetic-speed-case-{i}"
            case["vehicle_class"] = (
                "taxi", "motorcar", "hgv", "bus", "motorcycle", "special_vehicle"
            )[i % 6]
            case["direction"] = "forward" if i < 6 else "backward"
            packet["speed_evidence"].append(case)
        with self.assertRaisesRegex(
                EvidenceError, "EVIDENCE_ARRAY_EXCEEDS_SOURCE_QUEUE"):
            self.audit(packet)


    def test_future_physical_sign_and_speed_claims_are_rejected(self):
        # A form cannot assert photographs, speed observations or legal
        # review already occurred an hour into the future.
        future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        for kind, key in (("sign", "sign_evidence"), ("speed", "speed_evidence")):
            with self.subTest(kind=kind):
                packet = deepcopy(self.packet)
                packet["sign_evidence"] = (
                    packet["sign_evidence"] if kind == "sign" else [])
                packet["speed_evidence"] = (
                    packet["speed_evidence"] if kind == "speed" else [])
                item = packet[key][0]
                item["observed_at"] = future
                item["reviewed_at"] = future
                if kind == "speed":
                    item["legal"]["checked_at"] = future
                result = self.audit(packet)
                self.assertEqual(result["rejected_records"], 1)
                self.assertIn("TIMESTAMP_OUT_OF_RANGE",
                              result["results"][0]["reasons"])
                self.assertFalse(result["driver_alerts_allowed"])



if __name__ == "__main__":
    unittest.main()
