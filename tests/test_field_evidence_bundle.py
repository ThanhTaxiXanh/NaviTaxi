"""Synthetic-only regressions for PRIVATE portable road evidence archives.

No real sign GPS points, photographs, legal speeds or release SHA pins.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from package_field_evidence import (
    EVIDENCE_NAME, FORMAT, META_NAME, REPORT_NAME, SOURCE_NAME, STATUS,
    SUMS_NAME, EvidenceError, canonical_json, digest, package, verify, zip_entry,
)
import test_road_field_evidence as fixture_module


class PrivateEvidenceBundleTests(unittest.TestCase):
    def setUp(self):
        # Reuse the exact synthetic queue/photo fixture without inheriting tests.
        self.fixture = fixture_module.FieldEvidenceTests(
            "test_valid_synthetic_paperwork_still_authorizes_nothing")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.audit()
        self.root = self.fixture.root
        self.archive = self.root / "private-bundle.zip"

    def pack(self):
        return package(self.fixture.queue, self.fixture.queue_sha,
                       self.root / "packet.json", self.fixture.photo_root,
                       self.archive)

    def test_bundle_round_trip_and_zero_authorization(self):
        result = self.pack()
        self.assertEqual(result["status"], STATUS)
        self.assertEqual(result["approved_legal_speeds"], 0)
        self.assertEqual(result["approved_physical_sign_coordinates"], 0)
        self.assertFalse(result["driver_alerts_allowed"])
        checked = verify(self.archive, result["sha256"])
        self.assertEqual(checked["status"], STATUS)
        self.assertEqual(checked["photo_file_count"], 1)
        self.assertEqual(checked["verified_archived_files"], 5)
        self.assertFalse(checked["driver_alerts_allowed"])
        with zipfile.ZipFile(self.archive) as z:
            self.assertEqual(set(z.namelist()), {
                SOURCE_NAME, EVIDENCE_NAME, REPORT_NAME, META_NAME,
                SUMS_NAME, "photos/test.jpg"
            })
            self.assertEqual(z.read("photos/test.jpg"), self.fixture.photo_bytes)
            metadata = json.loads(z.read(META_NAME))
            self.assertEqual(metadata["format"], FORMAT)
            self.assertEqual(metadata["status"], STATUS)
            self.assertFalse(metadata["production_database_authorized"])

    def test_optional_gnss_gpx_bytes_bundle_and_offline_reaudit(self):
        self.fixture.attach_synthetic_gpx()
        self.fixture.audit()
        result = self.pack()
        checked = verify(self.archive, result["sha256"])
        self.assertEqual(result["gps_track_file_count"], 1)
        self.assertEqual(checked["gps_track_file_count"], 1)
        self.assertEqual(checked["verified_archived_files"], 6)
        self.assertEqual(checked["approved_physical_sign_coordinates"], 0)
        with zipfile.ZipFile(self.archive) as archive:
            self.assertIn("tracks/synthetic-track.gpx", archive.namelist())
            self.assertEqual(
                archive.read("tracks/synthetic-track.gpx"),
                (self.fixture.photo_root / "synthetic-track.gpx").read_bytes()
            )
            manifest = json.loads(archive.read(META_NAME))
            self.assertEqual(manifest["gps_track_file_count"], 1)
            self.assertFalse(manifest["production_database_authorized"])

    def test_gps_gpx_sha_mismatch_cannot_be_archived(self):
        packet = self.fixture.attach_synthetic_gpx(deepcopy(self.fixture.packet))
        packet["sign_evidence"][0]["gps_track"]["sha256"] = "f" * 64
        (self.root / "packet.json").write_bytes(fixture_module.jsonbytes(packet))
        with self.assertRaisesRegex(
                EvidenceError, "BUNDLE_REQUIRES_NONEMPTY_MECHANICALLY_READY_EVIDENCE"):
            self.pack()
        self.assertFalse(self.archive.exists())

    def test_gps_gpx_unreferenced_extra_file_cannot_pass_recomputed_checksums(self):
        self.fixture.attach_synthetic_gpx()
        self.fixture.audit()
        self.pack()
        forged, sha = self._repack_with_correct_internal_checksums(
            extra={"tracks/extra-unreferenced.gpx":
                   b'<gpx xmlns="http://www.topografix.com/GPX/1/1"/>'}
        )
        with self.assertRaisesRegex(
                EvidenceError, "UNREFERENCED_OR_MISSING_GPS_TRACK"):
            verify(forged, sha)

    def test_gpx_replaced_but_inner_hashes_recomputed_reaudit_fails(self):
        self.fixture.attach_synthetic_gpx()
        self.fixture.audit()
        self.pack()
        spoofed = (
            b'<gpx xmlns="http://www.topografix.com/GPX/1/1">'
            b'<wpt lat="0.09" lon="0.09">'
            b'<time>2026-11-14T01:00:00Z</time>'
            b'</wpt></gpx>'
        )
        forged, sha = self._repack_with_correct_internal_checksums(
            extra={"tracks/synthetic-track.gpx": spoofed}
        )
        with self.assertRaisesRegex(EvidenceError, "ARCHIVE_REAUDIT_MISMATCH"):
            verify(forged, sha)

    def test_multiple_vehicle_direction_speed_cases_survive_offline_reaudit(self):
        packet = deepcopy(self.fixture.packet)
        first = packet["speed_evidence"][0]
        first["case_id"] = "synthetic:101:taxi:forward"
        backward = deepcopy(first)
        backward["case_id"] = "synthetic:101:taxi:backward"
        backward["direction"] = "backward"
        backward["road_context"]["posted_sign_status"] = "none_confirmed"
        backward["sign_evidence_ids"] = []
        packet["speed_evidence"].append(backward)
        (self.root / "packet.json").write_bytes(fixture_module.jsonbytes(packet))
        info = self.pack()
        checked = verify(self.archive, info["sha256"])
        self.assertFalse(checked["driver_alerts_allowed"])
        self.assertEqual(checked["approved_legal_speeds"], 0)
        with zipfile.ZipFile(self.archive) as z:
            report = json.loads(z.read(REPORT_NAME))
        self.assertEqual(report["ready_for_independent_human_review"], 3)
        self.assertEqual(report["rejected_records"], 0)
        self.assertEqual([x["case_id"] for x in report["results"][1:]],
                         [first["case_id"], backward["case_id"]])
        self.assertFalse(report["production_database_authorized"])

    def test_repeated_packing_is_byte_for_byte_deterministic(self):
        a = self.pack()
        self.archive = self.root / "second-bundle.zip"
        b = self.pack()
        self.assertEqual(a["sha256"], b["sha256"])
        self.assertEqual(self.archive.read_bytes(),
                         (self.root / "private-bundle.zip").read_bytes())

    def test_wrong_original_queue_pin_rejected_before_writing(self):
        with self.assertRaisesRegex(EvidenceError, "REVIEW_ZIP_SHA256_MISMATCH"):
            package(self.fixture.queue, "f" * 64, self.root / "packet.json",
                    self.fixture.photo_root, self.archive)
        self.assertFalse(self.archive.exists())

    def test_missing_packet_or_photo_never_produces_valid_archive(self):
        (self.fixture.photo_root / "test.jpg").unlink()
        with self.assertRaises(EvidenceError):
            self.pack()
        self.assertFalse(self.archive.exists())

    def test_rejected_packets_cannot_enter_bundle(self):
        packet = deepcopy(self.fixture.packet)
        packet["sign_evidence"][0]["gps_accuracy_m"] = 500
        (self.root / "packet.json").write_bytes(fixture_module.jsonbytes(packet))
        with self.assertRaisesRegex(
                EvidenceError, "BUNDLE_REQUIRES_NONEMPTY_MECHANICALLY_READY_EVIDENCE"):
            self.pack()

    def test_empty_packet_cannot_be_misrepresented_as_ready(self):
        packet = deepcopy(self.fixture.packet)
        packet["sign_evidence"], packet["speed_evidence"] = [], []
        (self.root / "packet.json").write_bytes(fixture_module.jsonbytes(packet))
        with self.assertRaisesRegex(
                EvidenceError, "BUNDLE_REQUIRES_NONEMPTY_MECHANICALLY_READY_EVIDENCE"):
            self.pack()

    def test_source_approval_claim_rejected(self):
        packet = deepcopy(self.fixture.packet)
        packet["driver_alerts_allowed"] = True
        (self.root / "packet.json").write_bytes(fixture_module.jsonbytes(packet))
        with self.assertRaisesRegex(
                EvidenceError, "INPUT_ATTEMPTS_TO_AUTHORIZE_DRIVER_DATA"):
            self.pack()
        self.assertFalse(self.archive.exists())

    def test_absolute_and_parent_photo_paths_rejected(self):
        for bad in ("../escape.jpg", "/tmp/other.jpg", "parent\\test.jpg",
                    "photos/../../fake.jpg", "C:/secret.jpg", "bad\nname.jpg"):
            with self.subTest(path=bad):
                packet = deepcopy(self.fixture.packet)
                packet["sign_evidence"][0]["photo"]["path"] = bad
                (self.root / "packet.json").write_bytes(fixture_module.jsonbytes(packet))
                with self.assertRaises(EvidenceError):
                    self.pack()
                self.assertFalse(self.archive.exists())

    def test_photo_parent_symlink_is_rejected(self):
        actual = self.fixture.photo_root / "actual"
        actual.mkdir()
        (actual / "test.jpg").write_bytes(self.fixture.photo_bytes)
        (self.fixture.photo_root / "link").symlink_to(actual, target_is_directory=True)
        packet = deepcopy(self.fixture.packet)
        packet["sign_evidence"][0]["photo"]["path"] = "link/test.jpg"
        (self.root / "packet.json").write_bytes(fixture_module.jsonbytes(packet))
        with self.assertRaisesRegex(EvidenceError,
                                    "BUNDLE_REQUIRES_NONEMPTY_MECHANICALLY_READY_EVIDENCE"):
            self.pack()

    def test_unchanged_existing_archive_is_never_overwritten(self):
        self.archive.write_bytes(b"DO-NOT-OVERWRITE")
        with self.assertRaisesRegex(EvidenceError, "BUNDLE_OUTPUT_ALREADY_EXISTS"):
            self.pack()
        self.assertEqual(self.archive.read_bytes(), b"DO-NOT-OVERWRITE")

    def test_never_put_archive_inside_photo_root(self):
        self.archive = self.fixture.photo_root / "unapproved-evidence.zip"
        with self.assertRaisesRegex(
                EvidenceError, "BUNDLE_MUST_NOT_ENTER_REPO_OR_PHOTO_ROOT"):
            self.pack()
        self.assertFalse(self.archive.exists())

    def test_outer_zip_sha_is_mandatory_and_catches_changed_bytes(self):
        result = self.pack()
        with self.assertRaisesRegex(EvidenceError, "EXTERNAL_ARCHIVE_SHA256_REQUIRED"):
            verify(self.archive, "")
        with self.assertRaisesRegex(EvidenceError, "ARCHIVE_SHA256_MISMATCH"):
            verify(self.archive, "0" * 64)
        self.assertEqual(verify(self.archive, result["sha256"])["status"], STATUS)

    def test_changed_member_with_new_outer_hash_still_rejected(self):
        self.pack()
        corrupted = self.root / "corrupted.zip"
        with zipfile.ZipFile(self.archive) as src, \
                zipfile.ZipFile(corrupted, "w") as dst:
            for info in src.infolist():
                data = src.read(info.filename)
                if info.filename == "photos/test.jpg":
                    data += b"TAMPERED-IMAGE"
                dst.writestr(info, data)
        new_sha = hashlib.sha256(corrupted.read_bytes()).hexdigest()
        with self.assertRaisesRegex(EvidenceError, "ARCHIVE_MEMBER_HASH_MISMATCH"):
            verify(corrupted, new_sha)

    def test_path_traversal_in_archive_never_extracts(self):
        self.pack()
        corrupted = self.root / "traversal.zip"
        with zipfile.ZipFile(self.archive) as src, \
                zipfile.ZipFile(corrupted, "w") as dst:
            for info in src.infolist():
                dst.writestr(info, src.read(info.filename))
            dst.writestr("../not-a-field-photo.txt", "MALICIOUS")
        new_sha = hashlib.sha256(corrupted.read_bytes()).hexdigest()
        with self.assertRaisesRegex(EvidenceError, "UNSAFE_EVIDENCE_PHOTO_PATH"):
            verify(corrupted, new_sha)
        self.assertFalse((self.root / "not-a-field-photo.txt").exists())

    def test_replay_rejects_forged_audit_even_with_recomputed_checksums(self):
        self.pack()
        forged = self.root / "forged.zip"
        with zipfile.ZipFile(self.archive) as src:
            raw = {name: src.read(name) for name in src.namelist()}
        report = json.loads(raw[REPORT_NAME])
        report["ready_for_independent_human_review"] = 999
        raw[REPORT_NAME] = (json.dumps(report, ensure_ascii=False, sort_keys=True,
                                       indent=2) + "\n").encode("utf-8")
        manifest = json.loads(raw[META_NAME])
        report_sha = hashlib.sha256(raw[REPORT_NAME]).hexdigest()
        manifest["audit_report_sha256"] = report_sha
        for item in manifest["entries"]:
            if item["path"] == REPORT_NAME:
                item["size_bytes"] = len(raw[REPORT_NAME])
                item["sha256"] = report_sha
        raw[META_NAME] = (json.dumps(manifest, ensure_ascii=False, sort_keys=True,
                                     indent=2) + "\n").encode("utf-8")
        raw[SUMS_NAME] = "".join(
            hashlib.sha256(blob).hexdigest() + "  " + name + "\n"
            for name, blob in sorted(raw.items()) if name != SUMS_NAME
        ).encode("utf-8")
        with zipfile.ZipFile(self.archive) as original, \
                zipfile.ZipFile(forged, "w") as dst:
            for info in original.infolist():
                dst.writestr(info, raw[info.filename])
        new_sha = hashlib.sha256(forged.read_bytes()).hexdigest()
        with self.assertRaisesRegex(EvidenceError, "ARCHIVE_REAUDIT_MISMATCH"):
            verify(forged, new_sha)

    def test_archive_must_not_be_created_anywhere_in_git_workspace(self):
        # Private GPS/photo evidence in build/, docs/ or any untracked tree
        # can be accidentally committed even though Android has no DB pin.
        for directory in ("build", "docs", "tests"):
            with self.subTest(directory=directory):
                self.archive = ROOT / directory / "private-field-evidence.zip"
                with self.assertRaisesRegex(
                        EvidenceError, "BUNDLE_MUST_NOT_ENTER_REPO_OR_PHOTO_ROOT"):
                    self.pack()
                self.assertFalse(self.archive.exists())

    def _repack_with_correct_internal_checksums(self, extra=None, meta_extra=None):
        """Adversarial archives: attacker can recompute every inner checksum."""
        with zipfile.ZipFile(self.archive) as archive:
            entries = {name: archive.read(name) for name in archive.namelist()}
        if extra is not None:
            entries.update(extra)
        manifest = json.loads(entries[META_NAME])
        manifest["entries"] = [
            {"path": name, "sha256": digest(blob), "size_bytes": len(blob)}
            for name, blob in sorted(entries.items())
            if name not in (META_NAME, SUMS_NAME)
        ]
        manifest["photo_file_count"] = sum(
            name.startswith("photos/") for name in entries
        )
        if meta_extra is not None:
            manifest.update(meta_extra)
        entries[META_NAME] = canonical_json(manifest)
        entries[SUMS_NAME] = "".join(
            digest(blob) + "  " + name + "\n"
            for name, blob in sorted(entries.items()) if name != SUMS_NAME
        ).encode("utf-8")
        forged = self.root / "resigned-private-evidence.zip"
        with zipfile.ZipFile(forged, "w") as destination:
            for name, blob in sorted(entries.items()):
                destination.writestr(zip_entry(name), blob)
        return forged, digest(forged.read_bytes())

    def test_extra_private_photo_rejected_even_if_checksums_are_resigned(self):
        self.pack()
        forged, checksum = self._repack_with_correct_internal_checksums(
            extra={"photos/unreferenced-survey.jpg": b"\xff\xd8PRIVATE-NOT-IN-REVIEW"}
        )
        with self.assertRaisesRegex(
                EvidenceError, "UNREFERENCED_OR_MISSING_SIGN_PHOTO"):
            verify(forged, checksum)

    def test_bundle_manifest_cannot_claim_new_authority_flags(self):
        self.pack()
        forged, checksum = self._repack_with_correct_internal_checksums(
            meta_extra={"approved_new_speed_alerts": True}
        )
        with self.assertRaisesRegex(
                EvidenceError, "BUNDLE_CANNOT_CLAIM_PRODUCTION_APPROVAL"):
            verify(forged, checksum)



if __name__ == "__main__":
    unittest.main()
