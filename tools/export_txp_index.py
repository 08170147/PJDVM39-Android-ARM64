#!/usr/bin/env python3
"""Export observed TXP markers, payload hashes, and header string offsets.

The exporter records raw fields and does not infer undocumented resource links.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def find_markers(data: bytes) -> list[dict]:
    offsets = []
    cursor = 0
    while True:
        pos = data.find(b"TXP", cursor)
        if pos < 0:
            break
        offsets.append(pos)
        cursor = pos + 1

    markers = []
    for i, offset in enumerate(offsets):
        next_offset = offsets[i + 1] if i + 1 < len(offsets) else len(data)
        tag = data[offset + 3] if offset + 3 < len(data) else None
        entry = {
            "marker_offset": offset,
            "tag": tag,
            "tag_hex": f"0x{tag:02x}" if tag is not None else None,
            "next_marker_offset": next_offset if next_offset < len(data) else None,
            "bytes_until_next_marker": next_offset - offset,
        }
        if tag in (2, 3, 4) and offset + 4 <= next_offset:
            entry["raw_header_u32_le"] = [
                {"relative_offset": rel, "value": u32(data, offset + rel)}
                for rel in range(4, min(24, next_offset - offset - 3), 4)
            ]
        markers.append(entry)
    return markers


def find_type2_payloads(data: bytes, markers: list[dict]) -> list[dict]:
    type2 = [m for m in markers if m["tag"] == 2]
    records = []
    for i, marker in enumerate(type2):
        offset = marker["marker_offset"]
        next_offset = marker["next_marker_offset"] or len(data)
        if offset + 24 > next_offset:
            raise ValueError(f"Truncated TXP type-2 header at 0x{offset:x}")
        width = struct.unpack_from("<H", data, offset + 4)[0]
        height = struct.unpack_from("<H", data, offset + 8)[0]
        format_id = u32(data, offset + 12)
        payload = data[offset + 24:next_offset]
        expected_bc5 = ((width + 3) // 4) * ((height + 3) // 4) * 16
        records.append({
            "index": i,
            "marker_offset": offset,
            "width": width,
            "height": height,
            "format_id": format_id,
            "payload_offset": offset + 24,
            "payload_bytes": len(payload),
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
            "bc5_size_match": len(payload) == expected_bc5,
            "next_marker_offset": marker["next_marker_offset"],
        })
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path, help="Extracted resource BIN")
    parser.add_argument("--out", type=Path, default=Path("txp_index.json"))
    args = parser.parse_args()

    data = args.binary.read_bytes()
    markers = find_markers(data)
    first_marker = markers[0]["marker_offset"] if markers else len(data)
    header = data[:first_marker]
    strings = [
        {"offset": match.start(), "value": match.group().decode("ascii")}
        for match in re.finditer(rb"[A-Za-z0-9_]{3,}", header)
    ]
    header_u32 = [
        {"offset": offset, "value": u32(header, offset)}
        for offset in range(0, min(len(header), 256) - 3, 4)
    ]
    type2_records = find_type2_payloads(data, markers)
    # Preserve the observed seven TXP04 + two TXP02 sequence groups without
    # assigning undocumented semantic names to any fields.
    type2_by_offset = {r["marker_offset"]: r for r in type2_records}
    type2_offsets = [r["marker_offset"] for r in type2_records]
    txp4_groups = []
    for marker in markers:
        if marker["tag"] != 4:
            continue
        txp4_offset = marker["marker_offset"]
        following = [p for p in type2_offsets if p > txp4_offset]
        pair = following[:2]
        txp4_groups.append({
            "group_index": len(txp4_groups),
            "txp4_marker_offset": txp4_offset,
            "txp4_bytes_before_next_marker": marker["bytes_until_next_marker"],
            "txp4_raw_bytes_hex": data[txp4_offset:txp4_offset + 20].hex(),
            "following_type2_records": [
                {k: type2_by_offset[p][k] for k in
                 ("index", "marker_offset", "width", "height", "format_id",
                  "payload_bytes", "payload_sha256")}
                for p in pair
            ],
            "note": "Sequence grouping only; semantic relationship is unverified."
        })

    result = {
        "source_file": args.binary.name,
        "source_bytes": len(data),
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "bytes_before_first_txp_marker": first_marker,
        "header_u32_le_first_256_bytes": header_u32,
        "header_ascii_identifiers": strings,
        "txp_marker_count": len(markers),
        "txp_markers": markers,
        "txp_type2_record_count": len(type2_records),\n        "txp04_sequence_groups": txp4_groups,
        "txp_type2_records": type2_records,
        "interpretation_notes": [
            "TXP tag values are reported as observed; undocumented tag semantics are not assumed.",
            "TXP marker headers are exposed as raw little-endian words for further reverse engineering.",
            "Header strings are listed at their observed byte offsets only; no name-to-texture mapping is inferred.",
            "Type-2 payload boundaries end at the next literal TXP marker.",
            "BC5 size match and format_id are observations, not proof of runtime semantics.",\n            "TXP04 groups list the next two TXP2 records by sequence only; semantic pairing is unverified."
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "output": str(args.out),
        "source_bytes": len(data),
        "bytes_before_first_marker": first_marker,
        "header_identifiers": len(strings),
        "txp_marker_count": len(markers),
        "txp_tag_counts": {f"0x{tag:02x}": sum(m["tag"] == tag for m in markers)
                           for tag in sorted({m["tag"] for m in markers if m["tag"] is not None})},
        "txp_type2_records": len(type2_records),
        "all_type2_payloads_match_bc5_size": all(r["bc5_size_match"] for r in type2_records),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
