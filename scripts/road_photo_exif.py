#!/usr/bin/env python3
"""Bounded JPEG EXIF time/GPS consistency checks for PRIVATE sign photos.

Parsing self-reported metadata cannot authenticate a camera, location, clock,
photograph or roadside sign. Absent metadata is UNKNOWN, never verified.
Only a few standard TIFF/Exif tags are inspected, with no external libraries.
"""
from __future__ import annotations

from datetime import datetime
import math
import re
import struct


class PhotoExifError(ValueError):
    """Malformed or contradictory metadata in a claimed original JPEG."""


def _need(condition, reason):
    if not condition:
        raise PhotoExifError(reason)


def _tiff_metadata(blob):
    _need(len(blob) >= 8 and blob[:2] in (b"II", b"MM"),
          "PHOTO_EXIF_BAD_TIFF_HEADER")
    endian = "<" if blob[:2] == b"II" else ">"

    def unpack(fmt, offset):
        size = struct.calcsize(fmt)
        _need(0 <= offset <= len(blob) - size, "PHOTO_EXIF_OUT_OF_BOUNDS")
        return struct.unpack_from(endian + fmt, blob, offset)[0]

    _need(unpack("H", 2) == 42, "PHOTO_EXIF_BAD_TIFF_HEADER")

    def directory(offset):
        _need(8 <= offset <= len(blob) - 2, "PHOTO_EXIF_BAD_IFD")
        count = unpack("H", offset)
        _need(count <= 512 and offset + 2 + count * 12 + 4 <= len(blob),
              "PHOTO_EXIF_BAD_IFD")
        result = {}
        for i in range(count):
            start = offset + 2 + i * 12
            tag, kind, n = unpack("H", start), unpack("H", start + 2), unpack("I", start + 4)
            _need(tag not in result, "PHOTO_EXIF_DUPLICATE_TAG")
            result[tag] = (kind, n, start + 8)
        return result

    def payload(directory_entries, tag, kind, n):
        if tag not in directory_entries:
            return None
        actual_kind, count, field = directory_entries[tag]
        _need(actual_kind == kind and count == n, "PHOTO_EXIF_BAD_TAG_TYPE")
        width = {2: 1, 4: 4, 5: 8}[kind]
        size = count * width
        pos = field if size <= 4 else unpack("I", field)
        _need(0 <= pos <= len(blob) - size, "PHOTO_EXIF_OUT_OF_BOUNDS")
        return blob[pos:pos + size]

    def pointer(entries, tag):
        raw = payload(entries, tag, 4, 1)
        return unpack("I", entries[tag][2]) if raw is not None else None

    def ascii_value(entries, tag, limit):
        if tag not in entries:
            return None
        kind, count, _ = entries[tag]
        _need(kind == 2 and 2 <= count <= limit, "PHOTO_EXIF_BAD_ASCII")
        raw = payload(entries, tag, 2, count)
        _need(raw.endswith(b"\x00"), "PHOTO_EXIF_BAD_ASCII")
        try:
            return raw.rstrip(b"\x00").decode("ascii")
        except UnicodeDecodeError as exc:
            raise PhotoExifError("PHOTO_EXIF_BAD_ASCII") from exc

    base = directory(unpack("I", 4))
    exif_at = pointer(base, 0x8769)
    gps_at = pointer(base, 0x8825)
    taken = None
    coords = None
    if exif_at is not None:
        exif = directory(exif_at)
        original = ascii_value(exif, 0x9003, 64)
        offset = ascii_value(exif, 0x9011, 16)
        if original is not None:
            _need(re.fullmatch(r"\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}", original)
                  is not None, "PHOTO_EXIF_BAD_CAPTURE_TIME")
            try:
                parsed = datetime.strptime(original, "%Y:%m:%d %H:%M:%S")
            except ValueError as exc:
                raise PhotoExifError("PHOTO_EXIF_BAD_CAPTURE_TIME") from exc
            if offset is not None:
                _need(re.fullmatch(r"[+-](?:0\d|1[0-4]):[0-5]\d", offset) is not None,
                      "PHOTO_EXIF_BAD_TIME_OFFSET")
                try:
                    taken = datetime.fromisoformat(parsed.isoformat() + offset)
                except ValueError as exc:
                    raise PhotoExifError("PHOTO_EXIF_BAD_TIME_OFFSET") from exc
        else:
            _need(offset is None, "PHOTO_EXIF_OFFSET_WITHOUT_CAPTURE_TIME")

    if gps_at is not None:
        gps = directory(gps_at)
        tags = (1, 2, 3, 4)
        present = [tag in gps for tag in tags]
        if any(present):
            _need(all(present), "PHOTO_EXIF_INCOMPLETE_GPS")
            lat_ref = ascii_value(gps, 1, 4)
            lon_ref = ascii_value(gps, 3, 4)
            _need(lat_ref in ("N", "S") and lon_ref in ("E", "W"),
                  "PHOTO_EXIF_BAD_GPS_REFERENCE")

            def degrees(tag):
                raw = payload(gps, tag, 5, 3)
                values = []
                for i in range(3):
                    numerator, denominator = struct.unpack_from(endian + "II", raw, i * 8)
                    _need(denominator != 0, "PHOTO_EXIF_INVALID_GPS_RATIONAL")
                    values.append(numerator / denominator)
                d, m, s = values
                _need(math.isfinite(d) and 0 <= m < 60 and 0 <= s < 60,
                      "PHOTO_EXIF_INVALID_GPS_RATIONAL")
                return d + m / 60 + s / 3600

            latitude = degrees(2) * (-1 if lat_ref == "S" else 1)
            longitude = degrees(4) * (-1 if lon_ref == "W" else 1)
            _need(-90 <= latitude <= 90 and -180 <= longitude <= 180,
                  "PHOTO_EXIF_INVALID_WGS84")
            coords = (latitude, longitude)
    return taken, coords


def read_jpeg_photo_exif(raw: bytes):
    """Return (timezone-aware capture datetime | None, (lat,lon) | None).

    Exif timestamps without OffsetTimeOriginal cannot be compared to a
    timezone-aware survey timestamp; they are not silently treated as UTC.
    PNG and other formats are explicitly outside this JPEG-only parser.
    """
    _need(raw.startswith(b"\xff\xd8"), "PHOTO_EXIF_NOT_JPEG")
    position, exif = 2, None
    segment_count = 0
    while position < len(raw):
        _need(raw[position] == 0xff, "PHOTO_EXIF_MALFORMED_JPEG_MARKER")
        while position < len(raw) and raw[position] == 0xff:
            position += 1
        _need(position < len(raw), "PHOTO_EXIF_TRUNCATED_JPEG")
        marker = raw[position]
        position += 1
        if marker in (0xd9, 0xda):
            break  # end of image or start of compressed scan
        _need(marker not in (0x00, 0xd8), "PHOTO_EXIF_MALFORMED_JPEG_MARKER")
        if marker == 0x01 or 0xd0 <= marker <= 0xd7:
            continue
        _need(position + 2 <= len(raw), "PHOTO_EXIF_TRUNCATED_JPEG")
        segment_size = int.from_bytes(raw[position:position + 2], "big")
        _need(segment_size >= 2 and position + segment_size <= len(raw),
              "PHOTO_EXIF_TRUNCATED_JPEG")
        segment = raw[position + 2:position + segment_size]
        if marker == 0xe1 and segment.startswith(b"Exif\x00\x00"):
            _need(exif is None, "PHOTO_EXIF_AMBIGUOUS_MULTIPLE_SEGMENTS")
            exif = segment[6:]
        position += segment_size
        segment_count += 1
        _need(segment_count <= 2048, "PHOTO_EXIF_TOO_MANY_JPEG_SEGMENTS")
    return (None, None) if exif is None else _tiff_metadata(exif)
