import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_synthetic_pmtiles import build
from validate_pmtiles import validate, read_pmtiles

ASSETS = ROOT / "app/src/main/assets/pmtiles"

class PmtilesFixtureTests(unittest.TestCase):
    def test_valid_v3_mvt_grid(self):
        data = validate(ASSETS / "synthetic_test.pmtiles",
                        ASSETS / "synthetic_manifest.json")
        self.assertEqual(data["tile_count"], 1)
        self.assertEqual(data["layer"], "demo_grid")
        self.assertGreater(data["tile_payload_bytes"], 0)
        self.assertIn("SYNTHETIC", data["metadata"]["description"])

    def test_deterministic_rebuild_matches_committed_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "synthetic_test.pmtiles"
            manifest = Path(tmp) / "synthetic_manifest.json"
            build(archive, manifest)
            self.assertEqual(archive.read_bytes(),
                             (ASSETS / "synthetic_test.pmtiles").read_bytes())
            self.assertEqual(manifest.read_bytes(),
                             (ASSETS / "synthetic_manifest.json").read_bytes())

    def test_corrupt_bytes_and_wrong_version_rejected(self):
        original = (ASSETS / "synthetic_test.pmtiles").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "synthetic_test.pmtiles"
            manifest = Path(tmp) / "synthetic_manifest.json"
            manifest.write_bytes((ASSETS / "synthetic_manifest.json").read_bytes())
            archive.write_bytes(original[:-1] + bytes([original[-1] ^ 255]))
            with self.assertRaises(ValueError):
                validate(archive, manifest)
            with self.assertRaises(ValueError):
                read_pmtiles(b"BAD-TILE" + original[8:])
            with self.assertRaises(ValueError):
                read_pmtiles(original[:8] + b"\x00" * (len(original) - 8))

if __name__ == "__main__":
    unittest.main()
