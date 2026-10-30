#!/usr/bin/env python3
"""Inspect the single-entry FArC archive layout observed in the Build 19 IPA.

This is a conservative validator for the observed ExitMenu archive variant,
not a general-purpose parser for every FArC file used by the game.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import struct
from pathlib import Path

MAGIC = b"FArC"
FIXED_HEADER_SIZE = 0x30


def u32be(data: bytes, offset: int) -> int:
    if offset + 4 > len(data):
        raise ValueError(f"Truncated 32-bit field at 0x{offset:x}")
    return struct.unpack_from(">I", data, offset)[0]


def inspect(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    if len(raw) < FIXED_HEADER_SIZE:
        raise ValueError("File is shorter than the observed 0x30-byte header")
    if raw[:4] != MAGIC:
        raise ValueError(f"Unexpected magic: {raw[:4]!r}")

    header_size_field = u32be(raw, 0x04)
    name_field_size = u32be(raw, 0x08)
    name_start = 0x0C
    name_end = name_start + name_field_size
    if name_end > FIXED_HEADER_SIZE:
        raise ValueError("Name field extends beyond the observed fixed header")

    embedded_name = raw[name_start:name_end].split(b"\\0", 1)[0].decode("utf-8", "strict")
    data_offset = u32be(raw, 0x20)
    compressed_size = u32be(raw, 0x24)
    expanded_size = u32be(raw, 0x28)

    if data_offset != FIXED_HEADER_SIZE:
        raise ValueError(f"Unsupported data offset 0x{data_offset:x}; expected 0x30")
    if data_offset + compressed_size != len(raw):
        raise ValueError("Compressed-size field does not match file length")
    payload = raw[data_offset:data_offset + compressed_size]
    expanded = gzip.decompress(payload)
    if len(expanded) != expanded_size:
        raise ValueError(
            f"Expanded-size mismatch: header={expanded_size}, actual={len(expanded)}"
        )

    info = {
        "archive": path.name,
        "archive_bytes": len(raw),
        "magic": raw[:4].decode("ascii"),
        "header_size_field": header_size_field,
        "name_field_size": name_field_size,
        "embedded_name": embedded_name,
        "data_offset": data_offset,
        "compressed_size": compressed_size,
        "expanded_size": len(expanded),
        "expanded_sha256": hashlib.sha256(expanded).hexdigest(),
    }
    return info, expanded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument(
        "--extract-to", type=Path,
        help="Optional explicit output path for the decompressed embedded file",
    )
    args = parser.parse_args()

    info, expanded = inspect(args.archive)
    for key, value in info.items():
        print(f"{key}: {value}")

    if args.extract_to:
        args.extract_to.parent.mkdir(parents=True, exist_ok=True)
        args.extract_to.write_bytes(expanded)
        print(f"extracted_to: {args.extract_to}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
