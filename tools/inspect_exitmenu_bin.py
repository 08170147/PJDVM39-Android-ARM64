#!/usr/bin/env python3
"""Report conservative structural clues from an extracted PJDV menu .bin.

The script does not decode texture payloads or claim a complete format parser.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path, help="Extracted spr_nswgam_menu.bin")
    parser.add_argument("--header-limit", type=lambda x: int(x, 0), default=0x12EC)
    parser.add_argument("--json", type=Path, help="Optional JSON report path")
    args = parser.parse_args()

    data = args.binary.read_bytes()
    if len(data) < 8:
        raise ValueError("Input is too short for the observed 8-byte prefix")

    word0, word1 = struct.unpack_from("<II", data, 0)
    if word1 > len(data) or word1 < 8:
        raise ValueError(f"Second little-endian word is not a plausible header boundary: {word1}")

    limit = min(args.header_limit, len(data))
    identifiers = [
        {"offset": match.start(), "value": match.group().decode("ascii")}
        for match in re.finditer(rb"[A-Za-z0-9_]{4,}", data[:limit])
    ]
    txp_offsets = [match.start() for match in re.finditer(b"TXP", data)]

    report = {
        "file": args.binary.name,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "prefix_u32_le": [word0, word1],
        "candidate_header_boundary_from_word1": word1,
        "ascii_identifiers_in_prefix_region": identifiers,
        "ascii_identifier_count": len(identifiers),
        "literal_TXP_marker_count": len(txp_offsets),
        "literal_TXP_marker_offsets": txp_offsets,
        "format_status": "observations_only_not_a_complete_parser",
    }

    print(f"file: {report['file']}")
    print(f"size_bytes: {len(data)}")
    print(f"sha256: {report['sha256']}")
    print(f"prefix_u32_le: {word0}, {word1}")
    print(f"candidate_header_boundary_from_word1: {word1}")
    print(f"ASCII identifiers in first {limit} bytes: {len(identifiers)}")
    for item in identifiers:
        print(f"  0x{item['offset']:04x}  {item['value']}")
    print(f"literal TXP markers: {len(txp_offsets)}")
    print(f"TXP offsets: {txp_offsets}")
    print("NOTE: offsets/signatures are observations, not decoded TXP records.")

    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"json_report: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
