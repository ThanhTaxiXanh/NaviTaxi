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
    SUMS_NAME, EvidenceError, package, verify,
)
from test_road_field_evidence import FieldEvidenceTests, jsonbytes


class PrivateEvidenceBundleTests(unittest.TestCase):
    def setUp(self):
        # Reuse the exact synthetic queue/photo fixture without inheriting tests.
        self.fixture = FieldEvidenceTests(
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
        self.assertEqual(checked["verified_archived_files"], 4)
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
        (self.root / "packet.json").write_bytes(jsonbytes(packet))
        with self.assertRaisesRegex(
                EvidenceError, "BUNDLE_REQUIRES_NONEMPTY_MECHANICALLY_READY_EVIDENCE"):
            self.pack()

    def test_empty_packet_cannot_be_misrepresented_as_ready(self):
        packet = deepcopy(self.fixture.packet)
        packet["sign_evidence"], packet["speed_evidence"] = [], []
        (self.root / "packet.json").write_bytes(jsonbytes(packet))
        with self.assertRaisesRegex(
                EvidenceError, "BUNDLE_REQUIRES_NONEMPTY_MECHANICALLY_READY_EVIDENCE"):
            self.pack()

    def test_source_approval_claim_rejected(self):
        packet = deepcopy(self.fixture.packet)
        packet["driver_alerts_allowed"] = True
        (self.root / "packet.json").write_bytes(jsonbytes(packet))
        with self.assertRaisesRegex(
                EvidenceError, "INPUT_ATTEMPTS_TO_AUTHORIZE_DRIVER_DATA"):
            self.pack()
        self.assertFalse(self.archive.exists())

    def test_absolute_and_parent_photo_paths_rejected(self):
        for bad in ("../escape.jpg", "/tmp/other.jpg", "parent\\test.jpg",
                    "photos/../../fake.jpg", "C:/secret.jpg"):
            with self.subTest(path=bad):
                packet = deepcopy(self.fixture.packet)
                packet["sign_evidence"][0]["photo"]["path"] = bad
                (self.root / "packet.json").write_bytes(jsonbytes(packet))
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
        (self.root / "packet.json").write_bytes(jsonbytes(packet))
        with self.assertRaisesRegex(EvidenceError, "SYMLINK_IN_PHOTO_PATH"):
            self.pack()

    def test_unchanged_existing_archive_is_never_overwritten(self):
        self.archive.write_bytes(b"DO-NOT-OVERWRITE")
        with self.assertRaisesRegex(EvidenceError, "BUNDLE_OUTPUT_ALREADY_EXISTS"):
            self.pack()
        self.assertEqual(self.archive.read_bytes(), b"DO-NOT-OVERWRITE")

    def test_never_put_archive_inside_photo_root(self):
        self.archive = self.fixture.photo_root / "unapproved-evidence.zip"
        with self.assertRaisesRegex(
                EvidenceError, "BUNDLE_MUST_NOT_ENTER_APP_OR_PHOTO_ROOT"):
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


if __name__ == "__main__":
    unittest.main()
