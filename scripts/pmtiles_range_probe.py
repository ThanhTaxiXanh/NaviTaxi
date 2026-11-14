#!/usr/bin/env python3
"""Probe HTTP Range support for an owner-operated PMTiles server.

This does NOT download a full map, and is not meant for OSM public tile hosts.
For remote archives MapLibre Native accepts pmtiles://https://file.pmtiles.
"""
import argparse
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen

def probe(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}
    ):
        raise ValueError("Only HTTPS or loopback testing is allowed")
    request = Request(url, headers={"Range": "bytes=0-126",
                                    "User-Agent": "NaviTaxi-PMTiles-RangeProbe/0.3"})
    with urlopen(request, timeout=15) as response:
        if response.status != 206:
            raise ValueError("HTTP server ignored range; expected 206")
        content_range = response.headers.get("Content-Range", "")
        match = re.fullmatch(r"bytes 0-126/([0-9]+)", content_range)
        if not match or int(match.group(1)) < 127:
            raise ValueError("Content-Range missing or invalid")
        if response.headers.get("Accept-Ranges", "").lower() != "bytes":
            raise ValueError("Server must advertise Accept-Ranges: bytes")
        header = response.read(128)
        if len(header) != 127 or header[:8] != b"PMTiles\x03":
            raise ValueError("Invalid PMTiles v3 header")
        return int(match.group(1))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="HTTPS archive URL with byte-range support")
    args = ap.parse_args()
    print(f"PMTiles v3 HTTP Range supported, total bytes: {probe(args.url)}")
