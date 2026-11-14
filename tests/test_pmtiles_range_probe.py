import http.server
from pathlib import Path
import socketserver
import sys
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from pmtiles_range_probe import probe

DATA = (ROOT / "app/src/main/assets/pmtiles/synthetic_test.pmtiles").read_bytes()

class RangeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_GET(self):
        if self.headers.get("Range") == "bytes=0-126":
            self.send_response(206)
            self.send_header("Content-Type", "application/vnd.pmtiles")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes 0-126/{len(DATA)}")
            self.send_header("Content-Length", "127")
            self.end_headers()
            self.wfile.write(DATA[:127])
        else:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{len(DATA)}")
            self.end_headers()

class RangeTests(unittest.TestCase):
    def test_range_206_and_correct_header(self):
        server = http.server.HTTPServer(("127.0.0.1", 0), RangeHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            self.assertEqual(probe(f"http://127.0.0.1:{server.server_port}/test.pmtiles"),
                             len(DATA))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_prohibits_unencrypted_remote_connections(self):
        with self.assertRaises(ValueError):
            probe("http://example.org/test.pmtiles")

if __name__ == "__main__":
    unittest.main()
