#!/usr/bin/env python3
"""Export a conservative JSON inventory of TXP type-2 records and header strings.

This deliberately reports byte offsets and hashes without guessing which
resource-name entry maps to which texture record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path


def find_txp_records(data: bytes) -> list[dict]:
    markers = []
    cursor = 0
    while True:
        pos = data.find(b"TXP", cursor)
        if pos < 0:
            break
        markers.append(pos)
        cursor = pos + 1

    records = []
    for marker_index, offset in enumerate(markers):
        if offset + 4 > len(data) or data[offset + 3] != 2:
            continue
        next_marker = markers[marker_index + 1] if marker_index + 1 < len(markers) else len(data)
        if offset + 24 > next_marker:
            raise ValueError(f"Truncated TXP type-2 header at 0x{offset:x}")
        width = struct.unpack_from("<H", data, offset + 4)[0]
        height = struct.unpack_from("<H", data, offset + 8)[0]
        format_id = struct.unpack_from("<I", data, offset + 12)[0]
        payload = data[offset + 24:next_marker]
        expected_bc5 = ((width + 3) // 4) * ((height + 3) // 4) * 16
        records.append({
            "index": len(records),
            "marker_offset": offset,
            "width": width,
            "height": height,
            "format_id": format_id,
            "payload_offset": offset + 24,
            "payload_bytes": len(payload),
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
            "bc5_size_match": len(payload) == expected_bc5,
            "next_txp_marker_offset": next_marker if next_marker < len(data) else None,
        })
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path, help="Extracted resource BIN")
    parser.add_argument("--out", type=Path, default=Path("txp_index.json"))
    args = parser.parse_args()

    data = args.binary.read_bytes()
    records = find_txp_records(data)
    first_record = min((r["marker_offset"] for r in records), default=len(data))
    header = data[:first_record]
    strings = [
        {"offset": match.start(), "value": match.group().decode("ascii")}
        for match in re.finditer(rb"[A-Za-z0-9_]{3,}", header)
    ]
    header_u32 = [
        {"offset": offset, "value": struct.unpack_from("<I", header, offset)[0]}
        for offset in range(0, min(len(header), 256) - 3, 4)
    ]

    result = {
        "source_file": args.binary.name,
        "source_bytes": len(data),
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "observed_header_bytes_before_first_type2_txp": first_record,
        "header_u32_le_first_256_bytes": header_u32,
        "header_ascii_identifiers": strings,
        "txp_type2_record_count": len(records),
        "txp_type2_records": records,
        "interpretation_notes": [
            "Header strings are listed at their observed byte offsets only.",
            "No resource-name-to-texture mapping is inferred.",
            "format_id and BC5 size match are observations, not proof of runtime semantics.",
            "Payload boundaries use the next literal TXP marker; validate if the container format evolves."
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.out),
        "source_bytes": len(data),
        "header_bytes": first_record,
        "header_identifiers": len(strings),
        "txp_type2_records": len(records),
        "all_payloads_match_bc5_size": all(r["bc5_size_match"] for r in records),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
