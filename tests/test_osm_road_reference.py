"""The staging extractor must never manufacture legal speeds or sign coordinates."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from extract_osm_road_reference import ReferenceError, extract_reference

# Deliberately artificial OSM fixture. IDs/positions/speeds are NOT Vietnam
# observations and MUST NEVER enter APK assets or the trusted road SQLite DB.
FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6" generator="NaviTaxi synthetic unit fixture">
  <node id="11" lat="0" lon="0" version="3" timestamp="2026-11-01T00:00:00Z">
    <tag k="traffic_sign" v="maxspeed"/>
    <tag k="maxspeed" v="50"/>
    <tag k="direction" v="forward"/>
  </node>
  <node id="12" lat="91" lon="1" version="1">
    <tag k="traffic_sign:backward" v="stop"/>
  </node>
  <node id="13" lat="0.5" lon="0.5" version="1">
    <tag k="name" v="not a sign"/>
  </node>
  <way id="101" version="4">
    <nd ref="11"/><nd ref="13"/>
    <tag k="highway" v="primary"/>
    <tag k="maxspeed" v="30 mph"/>
    <tag k="maxspeed:conditional" v="20 @ (Mo-Fr 07:00-09:00)"/>
    <tag k="maxspeed:forward" v="signals"/>
    <tag k="source:maxspeed" v="survey"/>
    <tag k="traffic_sign" v="maxspeed"/>
  </way>
  <way id="102" version="1">
    <nd ref="11"/><nd ref="13"/>
    <tag k="highway" v="residential"/>
    <tag k="maxspeed:advisory" v="30"/>
  </way>
  <way id="103" version="1">
    <nd ref="11"/><nd ref="13"/>
    <tag k="railway" v="rail"/>
    <tag k="maxspeed" v="160"/>
  </way>
  <relation id="201" version="1">
    <member type="way" ref="101" role=""/>
    <tag k="traffic_sign" v="end_of_maxspeed"/>
  </relation>
</osm>
"""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class OsmRoadReferenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "synthetic.osm"
        self.source.write_text(FIXTURE, encoding="utf-8")
        self.pin = digest(self.source.read_bytes())
        self.uri = "https://example.org/synthetic-unit-test.osm"

    def extract(self, **kwargs):
        return extract_reference(
            kwargs.get("snapshot", self.source),
            kwargs.get("expected_sha256", self.pin),
            kwargs.get("source_uri", self.uri),
            kwargs.get("output_dir", self.root / "reference"),
            kwargs.get("max_candidates", 100),
            kwargs.get("archive", self.root / "reference.zip"),
        )

    def records(self, name):
        return [json.loads(row) for row in
                (self.root / "reference" / name).read_text("utf-8").splitlines()]

    def test_preserves_raw_tags_without_inventing_legal_speed_or_sign_locations(self):
        result = self.extract()
        self.assertEqual(result["status"], "UNVERIFIED_OSM_REFERENCE_ONLY")
        self.assertEqual(result["counts"], {
            "speed_way_candidates": 2, "sign_node_candidates": 2,
            "sign_way_candidates": 1, "sign_relation_candidates": 1,
            "sign_nodes_without_usable_point": 1,
        })
        self.assertFalse(any(result["prohibitions"].values()))
        self.assertEqual(result["source_snapshot"]["sha256"], self.pin)
        self.assertEqual(result["source_snapshot"]["license"], "ODbL-1.0")
        ways = self.records("speed_way_candidates.jsonl")
        self.assertEqual([r["osm"]["id"] for r in ways], [101, 102])
        self.assertEqual(ways[0]["tags"]["maxspeed"], "30 mph")
        self.assertEqual(ways[0]["tags"]["maxspeed:forward"], "signals")
        self.assertEqual(ways[0]["tags"]["maxspeed:conditional"],
                         "20 @ (Mo-Fr 07:00-09:00)")
        self.assertIsNone(ways[0]["osm_node_coordinate"])
        self.assertFalse(ways[0]["approved_for_driver_alert"])
        self.assertNotIn("speed_kmh", ways[0])

        signs = self.records("traffic_sign_candidates.jsonl")
        self.assertEqual([(r["osm"]["type"], r["osm"]["id"]) for r in signs],
                         [("node", 11), ("node", 12),
                          ("way", 101), ("relation", 201)])
        self.assertEqual(signs[0]["osm_node_coordinate"],
                         {"latitude": 0.0, "longitude": 0.0})
        self.assertEqual(signs[0]["tags"]["maxspeed"], "50")
        self.assertIsNone(signs[1]["osm_node_coordinate"])
        self.assertIsNone(signs[2]["osm_node_coordinate"])
        self.assertIsNone(signs[3]["osm_node_coordinate"])
        for item in signs:
            self.assertFalse(item["independently_verified_physical_sign"])
            self.assertFalse(item["approved_for_driver_alert"])

    def test_archive_has_exact_source_checksum_and_entry_checksums(self):
        manifest = self.extract()
        archive = self.root / "reference.zip"
        with zipfile.ZipFile(archive) as zipf:
            lines = zipf.read("SHA256SUMS").decode().strip().splitlines()
            for line in lines:
                checksum, name = line.split("  ", 1)
                self.assertEqual(digest(zipf.read(name)), checksum)
            self.assertEqual(json.loads(zipf.read("manifest.json")),
                             manifest)
            self.assertNotIn("road_intelligence.db", zipf.namelist())

    def test_modified_snapshot_does_not_create_reference_directory(self):
        with self.assertRaisesRegex(ReferenceError, "does not match"):
            self.extract(expected_sha256="0" * 64)
        self.assertFalse((self.root / "reference").exists())
        self.assertFalse((self.root / "reference.zip").exists())

    def test_bad_source_url_and_output_into_android_assets_are_blocked(self):
        for url in ("http://example.org/data.osm", "https://tile.openstreetmap.org/a.osm",
                    "https://example.org/a.osm?token=123"):
            with self.subTest(url=url), self.assertRaises(ReferenceError):
                self.extract(source_uri=url)
        self.assertFalse((self.root / "reference").exists())
        with self.assertRaises(ReferenceError):
            self.extract(output_dir=self.root / "app/src/main/assets/road_intelligence")

    def test_exceeded_candidate_limit_leaves_no_partial_release(self):
        with self.assertRaisesRegex(ReferenceError, "limit exceeded"):
            self.extract(max_candidates=1)
        self.assertFalse((self.root / "reference").exists())
        self.assertFalse((self.root / "reference.zip").exists())

    def test_existing_output_is_never_silently_overwritten(self):
        self.extract()
        with self.assertRaises((FileExistsError, ReferenceError)):
            self.extract()
        self.assertTrue((self.root / "reference" / "manifest.json").exists())

    @unittest.skipUnless(importlib.util.find_spec("osmium"), "pyosmium required for real PBF reader")
    def test_pbf_streamer_matches_xml_reference_candidate_semantics(self):
        import osmium
        # Same synthetic test fixture re-encoded in PBF; no real road observations.
        pbf = self.root / "synthetic.osm.pbf"
        with osmium.SimpleWriter(str(pbf)) as writer:
            for obj in osmium.FileProcessor(str(self.source)):
                writer.add(obj)
        result = self.extract(snapshot=pbf, expected_sha256=digest(pbf.read_bytes()))
        self.assertEqual(result["counts"]["speed_way_candidates"], 2)
        self.assertEqual(result["counts"]["sign_node_candidates"], 2)
        self.assertEqual(result["counts"]["sign_way_candidates"], 1)
        self.assertEqual(result["counts"]["sign_relation_candidates"], 1)
        self.assertEqual(self.records("speed_way_candidates.jsonl")[0]["tags"]["maxspeed"],
                         "30 mph")
        self.assertIsNone(self.records("traffic_sign_candidates.jsonl")[2]
                          ["osm_node_coordinate"])


if __name__ == "__main__":
    unittest.main()
