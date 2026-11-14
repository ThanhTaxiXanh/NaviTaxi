"""Release-catalog gates never create real speed or traffic-sign claims."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_offline_catalog import CatalogError, classify_release, validate_catalog


def package():
    return {
        "id": "vn-example-fixture", "version": "2026.11.14",
        "release_sequence": 11,
        "url": "https://example.org/private/test.pmtiles",
        "size_bytes": 462,
        "sha256": "a" * 64,
        "license": "NaviTaxi test fixture only",
        "source_uri": "https://example.org/source-license",
        "is_real_map": False, "has_verified_speed_limits": False,
        "has_verified_signs": False,
    }


def catalog(packages=None):
    return {"format": "navitaxi-offline-catalog/v1",
            "published_at": "2026-11-14T15:00:00Z",
            "packages": packages if packages is not None else [package()]}


def encoded(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return raw, hashlib.sha256(raw).hexdigest()


class OfflineCatalogTests(unittest.TestCase):
    def test_independently_pinned_catalog_is_structure_validated(self):
        raw, pin = encoded(catalog())
        validated = validate_catalog(raw, pin)
        self.assertEqual(validated["sha256"], pin)
        self.assertEqual(len(validated["packages"]), 1)
        self.assertFalse(validated["packages"][0]["has_verified_signs"])
        self.assertEqual(validate_catalog(*encoded(catalog([])))["packages"], [])

    def test_absent_or_wrong_pin_rejected_even_if_json_parses(self):
        raw, _ = encoded(catalog())
        for pin in ("", "a" * 64, "0" * 63, "A" * 64):
            with self.subTest(pin=pin), self.assertRaises(CatalogError):
                validate_catalog(raw, pin)

    def test_modified_or_duplicate_json_is_rejected(self):
        raw, pin = encoded(catalog())
        with self.assertRaises(CatalogError):
            validate_catalog(raw + b" ", pin)
        duplicated = (b'{"format":"navitaxi-offline-catalog/v1",'
                      b'"format":"navitaxi-offline-catalog/v1",'
                      b'"published_at":"2026-11-14T15:00:00Z","packages":[]}')
        with self.assertRaises(CatalogError):
            validate_catalog(duplicated, hashlib.sha256(duplicated).hexdigest())

    def test_refuse_fake_verified_road_intelligence_flags(self):
        for field in ("has_verified_speed_limits", "has_verified_signs"):
            bad = catalog()
            bad["packages"][0][field] = True
            with self.subTest(field=field), self.assertRaises(CatalogError):
                validate_catalog(*encoded(bad))

    def test_reject_untrusted_origins_and_unsafe_metadata(self):
        alterations = [
            ("url", "http://example.org/a.pmtiles"),
            ("url", "https://tile.openstreetmap.org/a.pmtiles"),
            ("url", "https://example.org/a.pmtiles?token=private"),
            ("url", "https://other@example.org/a.pmtiles"),
            ("url", "https://example.org/a.mbtiles"),
            ("source_uri", "file:///etc/passwd"),
            ("source_uri", "https://example.org/license?key=secret"),
            ("id", "../unsafe"),
            ("version", "../unsafe"),
            ("sha256", "ABC"),
            ("size_bytes", 0),
            ("release_sequence", True),
            ("release_sequence", 0),
            ("has_verified_signs", "false"),
            ("license", ""),
        ]
        for key, value in alterations:
            bad = catalog()
            bad["packages"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(CatalogError):
                validate_catalog(*encoded(bad))

    def test_reject_duplicate_packages_and_unknown_properties(self):
        with self.assertRaises(CatalogError):
            validate_catalog(*encoded(catalog([package(), package()])))
        bad = catalog()
        bad["packages"][0]["unsigned_speed_kmh"] = 80
        with self.assertRaises(CatalogError):
            validate_catalog(*encoded(bad))

    def test_release_decisions_use_sequence_and_identity(self):
        current = package()
        installed = copy.deepcopy(current)
        self.assertEqual(classify_release(current, None), "NOT_INSTALLED")
        self.assertEqual(classify_release(current, installed), "CURRENT")
        newer = dict(current, release_sequence=12, version="2026.2")
        self.assertEqual(classify_release(newer, installed), "UPDATE_AVAILABLE")
        older = dict(current, release_sequence=10, version="2026.12")
        self.assertEqual(classify_release(older, installed), "ROLLBACK_REJECTED")
        conflict = dict(current, sha256="b" * 64)
        self.assertEqual(classify_release(conflict, installed), "SAME_SEQUENCE_CONFLICT")
        with self.assertRaises(CatalogError):
            classify_release(current, dict(installed, id="different"))
        with self.assertRaises(CatalogError):
            classify_release(current, dict(installed, release_sequence=None))

    def test_valid_dates_and_bounded_catalog(self):
        for published in ("2026-02-30T10:00:00Z", "not-a-date"):
            bad = catalog()
            bad["published_at"] = published
            with self.assertRaises(CatalogError):
                validate_catalog(*encoded(bad))
        huge = catalog([dict(package(), id=f"test-{n}") for n in range(501)])
        with self.assertRaises(CatalogError):
            validate_catalog(*encoded(huge))


if __name__ == "__main__":
    unittest.main()
