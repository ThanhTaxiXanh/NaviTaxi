"""No network required: bounded downloader unit tests with fake HTTP responses."""
import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from acquire_geofabrik_vietnam import (
    acquire_snapshot, AcquisitionError, SNAPSHOT, SOURCE_URI, MD5_URI
)


class FakeResponse(io.BytesIO):
    def __init__(self, content: bytes, url: str, headers=None):
        super().__init__(content)
        self.url = url
        self.headers = headers or {}

    def geturl(self):
        return self.url


class DownloaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name) / "reference-only"
        self.test_bytes = b"NaviTaxi TEST ONLY, NOT AN OSM PBF"
        self.publisher_md5 = hashlib.md5(
            self.test_bytes, usedforsecurity=False).hexdigest()
        self.sidecar = (self.publisher_md5 + "  " + SNAPSHOT + "\n").encode()

    def opener(self, request, timeout):
        if request.full_url == MD5_URI:
            return FakeResponse(self.sidecar, MD5_URI)
        if request.full_url == SOURCE_URI:
            return FakeResponse(
                self.test_bytes, SOURCE_URI,
                {"Content-Length": str(len(self.test_bytes))})
        raise AssertionError("Unexpected network request")

    def run_acquisition(self, **kwargs):
        return acquire_snapshot(
            self.folder, opener=kwargs.get("opener", self.opener),
            expected_bytes=kwargs.get("size", len(self.test_bytes)))

    def test_fixed_url_receipt_hashes_and_zero_approval(self):
        report = self.run_acquisition()
        self.assertEqual(report["source_uri"], SOURCE_URI)
        self.assertEqual(report["size_bytes"], len(self.test_bytes))
        self.assertEqual(report["sha256"],
                         hashlib.sha256(self.test_bytes).hexdigest())
        self.assertTrue(report["publisher_md5_matches"])
        self.assertFalse(report["driver_alerts_allowed"])
        self.assertFalse(report["sha256_independently_approved"])
        self.assertFalse(report["physical_sign_coordinates_verified"])
        self.assertEqual((self.folder / SNAPSHOT).read_bytes(), self.test_bytes)
        self.assertFalse((self.folder / (SNAPSHOT + ".part")).exists())

    def test_bad_publisher_digest_removes_all_partial_output(self):
        def bad(request, timeout):
            if request.full_url == MD5_URI:
                return FakeResponse(
                    b"f" * 32 + b"  " + SNAPSHOT.encode(), MD5_URI)
            return self.opener(request, timeout)
        with self.assertRaisesRegex(AcquisitionError, "MD5 sidecar"):
            self.run_acquisition(opener=bad)
        self.assertFalse(self.folder.exists())

    def test_wrong_byte_count_or_header_rejected(self):
        with self.assertRaisesRegex(AcquisitionError, "Content-Length"):
            self.run_acquisition(size=len(self.test_bytes) + 1)
        self.assertFalse(self.folder.exists())

        def no_length(request, timeout):
            if request.full_url == SOURCE_URI:
                return FakeResponse(self.test_bytes, SOURCE_URI)
            return self.opener(request, timeout)
        with self.assertRaisesRegex(AcquisitionError, "size differs"):
            self.run_acquisition(opener=no_length, size=len(self.test_bytes) + 1)
        self.assertFalse(self.folder.exists())

    def test_redirect_to_unapproved_host_is_rejected(self):
        def evil(request, timeout):
            if request.full_url == MD5_URI:
                return FakeResponse(self.sidecar, "https://attacker.example/file.md5")
            return self.opener(request, timeout)
        with self.assertRaisesRegex(AcquisitionError, "authorized Geofabrik"):
            self.run_acquisition(opener=evil)
        self.assertFalse(self.folder.exists())

    def test_existing_directory_is_not_replaced(self):
        self.folder.mkdir()
        with self.assertRaises(FileExistsError):
            self.run_acquisition()
        self.assertTrue(self.folder.exists())

    def test_refuse_production_asset_location(self):
        root = Path(self.tmp.name)
        with self.assertRaisesRegex(AcquisitionError, "Android"):
            acquire_snapshot(root / "app/src/main/assets/pbf", self.opener, 30)
        with self.assertRaisesRegex(AcquisitionError, "Android"):
            acquire_snapshot(root / "data/road_intelligence/pbf", self.opener, 30)

    def test_invalid_or_unbounded_size_rejected_before_download(self):
        for length in (0, -1, 350_000_001):
            with self.subTest(length=length):
                with self.assertRaisesRegex(AcquisitionError, "Invalid bounded"):
                    self.run_acquisition(size=length)
        self.assertFalse(self.folder.exists())


if __name__ == "__main__":
    unittest.main()
