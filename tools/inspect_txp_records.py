#!/usr/bin/env python3
"""Inventory TXP type-2 records in an extracted ExitMenu BIN.

This validates observed record boundaries and byte counts only. It does not
unswizzle, decode, or render the texture payload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path, help="Extracted spr_nswgam_menu.bin")
    parser.add_argument("--json", type=Path, help="Optional JSON report path")
    args = parser.parse_args()

    data = args.binary.read_bytes()
    offsets = []
    cursor = 0
    while True:
        pos = data.find(b"TXP", cursor)
        if pos < 0:
            break
        offsets.append(pos)
        cursor = pos + 1

    records = []
    for index, offset in enumerate(offsets):
        next_offset = offsets[index + 1] if index + 1 < len(offsets) else len(data)
        record_type = data[offset + 3] if offset + 3 < len(data) else None
        if record_type != 2:
            continue
        if offset + 24 > next_offset:
            raise ValueError(f"Truncated TXP type-2 header at 0x{offset:x}")

        width = struct.unpack_from("<H", data, offset + 4)[0]
        height = struct.unpack_from("<H", data, offset + 8)[0]
        format_id = struct.unpack_from("<I", data, offset + 12)[0]
        header_flag = struct.unpack_from("<I", data, offset + 16)[0]
        trailing_field = struct.unpack_from("<I", data, offset + 20)[0]
        payload_start = offset + 24
        payload = data[payload_start:next_offset]
        expected = width * height

        records.append({
            "record_offset": offset,
            "next_marker_offset": next_offset,
            "record_type": record_type,
            "header_bytes": 24,
            "width_candidate_u16le": width,
            "height_candidate_u16le": height,
            "format_id_u32le": format_id,
            "header_flag_u32le": header_flag,
            "trailing_field_u32le": trailing_field,
            "payload_offset": payload_start,
            "payload_bytes": len(payload),
            "width_times_height": expected,
            "payload_equals_width_times_height": len(payload) == expected,
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
        })

    report = {
        "file": args.binary.name,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "txp_marker_count": len(offsets),
        "txp_type2_record_count": len(records),
        "records": records,
        "format_status": "candidate_fields_and_boundary_checks_only",
    }

    print(f"file: {args.binary.name}")
    print(f"TXP markers: {len(offsets)}")
    print(f"TXP type-2 records: {len(records)}")
    for record in records:
        status = "MATCH" if record["payload_equals_width_times_height"] else "MISMATCH"
        print(
            f"0x{record['record_offset']:08x}: "
            f"{record['width_candidate_u16le']}x{record['height_candidate_u16le']} "
            f"format={record['format_id_u32le']} "
            f"payload={record['payload_bytes']} "
            f"w*h={record['width_times_height']} [{status}]"
        )
    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"json_report: {args.json}")
    return 0 if all(r["payload_equals_width_times_height"] for r in records) else 2


if __name__ == "__main__":
    raise SystemExit(main())
