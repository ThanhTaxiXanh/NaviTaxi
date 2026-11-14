import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
STYLE_DIR = ROOT / "app" / "src" / "main" / "assets" / "map_styles"

class MapStylePolicyTests(unittest.TestCase):
    def test_osm_raster_only_for_interactive_viewport(self):
        doc = json.loads((STYLE_DIR / "osm_streets_experimental.json").read_text())
        self.assertEqual(doc["version"], 8)
        self.assertEqual(len(doc["sources"]), 1)
        source = doc["sources"]["osm-standard"]
        self.assertEqual(source["type"], "raster")
        self.assertEqual(source["tiles"], ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"])
        self.assertIn("OpenStreetMap contributors", source["attribution"])
        self.assertFalse(any("prefetch" in k.lower() for k in doc))

    def test_offline_style_cannot_fake_map_data(self):
        doc = json.loads((STYLE_DIR / "offline_empty.json").read_text())
        self.assertEqual(doc["sources"], {})
        self.assertEqual(doc["layers"][0]["type"], "background")
        self.assertFalse(any("speed" in k for k in doc["sources"]))

if __name__ == "__main__":
    unittest.main()
