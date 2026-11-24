#!/usr/bin/env python3
"""Validate entry.png as a whole PNG and copy it to the output directory.

Standard library only. Validation rules:
  - file size at most 1048576 bytes
  - exact 8-byte PNG signature
  - first chunk is a 13-byte IHDR
  - image width and height each at most 1024 px (and non-zero)
  - every chunk has a correct CRC-32
  - an IEND chunk is present and nothing follows it
On success the file is copied byte-for-byte to
$MAKEFUN_OUTPUT_DIR/entry.png (or /output/entry.png when unset).
On any validation failure, exit non-zero with a clear message.
"""

import os
import struct
import sys
import zlib
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1048576
MAX_SIDE = 1024


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def validate_png(data):
    if len(data) == 0:
        fail("entry.png is empty")
    if len(data) > MAX_BYTES:
        fail(f"entry.png is {len(data)} bytes, over the {MAX_BYTES}-byte limit")
    if data[:8] != PNG_SIGNATURE:
        fail("entry.png does not start with the PNG signature")

    offset = 8
    first_chunk = True
    seen_iend = False

    while offset < len(data):
        # Each chunk needs at least length(4) + type(4) + CRC(4).
        if offset + 12 > len(data):
            fail(f"truncated chunk header at offset {offset}")
        (length,) = struct.unpack(">I", data[offset:offset + 4])
        chunk_type = data[offset + 4:offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(data):
            fail(f"truncated chunk {chunk_type!r} at offset {offset}")
        chunk_data = data[data_start:data_end]
        (stored_crc,) = struct.unpack(">I", data[data_end:crc_end])
        computed_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if stored_crc != computed_crc:
            fail(
                f"bad CRC in chunk {chunk_type.decode('latin-1')}: "
                f"stored {stored_crc:#010x}, computed {computed_crc:#010x}"
            )

        if first_chunk:
            if chunk_type != b"IHDR":
                fail(f"first chunk must be IHDR, got {chunk_type!r}")
            if length != 13:
                fail(f"IHDR must be 13 bytes, got {length}")
            width, height = struct.unpack(">II", chunk_data[0:8])
            if width == 0 or height == 0:
                fail(f"IHDR dimensions must be non-zero, got {width}x{height}")
            if width > MAX_SIDE or height > MAX_SIDE:
                fail(
                    f"image is {width}x{height}, exceeding the "
                    f"{MAX_SIDE}px-per-side limit"
                )
            first_chunk = False

        offset = crc_end

        if chunk_type == b"IEND":
            if length != 0:
                fail(f"IEND must be empty, got {length} bytes")
            seen_iend = True
            if offset != len(data):
                fail(f"{len(data) - offset} trailing byte(s) after IEND")
            break

    if first_chunk:
        fail("no chunks found after the PNG signature")
    if not seen_iend:
        fail("no IEND chunk found")


def main():
    here = Path(__file__).resolve().parent
    source = here / "entry.png"
    if not source.is_file():
        fail(f"entry.png not found next to main.py (expected at {source})")

    data = source.read_bytes()
    validate_png(data)

    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / "entry.png"
        destination.write_bytes(data)
    except OSError as exc:
        fail(f"could not write output: {exc}")

    print(f"OK: entry.png validated ({len(data)} bytes) and copied to {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
