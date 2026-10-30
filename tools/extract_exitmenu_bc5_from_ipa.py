#!/usr/bin/env python3
"""Extract the observed ExitMenu 2048x2048 BC5 candidate from a Build 19 IPA.

This is deliberately conservative: it selects the English ExitMenu FArC entry,
validates the observed single-entry FArC header/gzip size, locates TXP type-2
records by marker boundaries, and exports the selected raw payload. It does not
prove the game's runtime channel swizzle, mip layout, or texture placement.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import struct
import zipfile
from pathlib import Path

ARCHIVE_SUFFIX = "ExitMenu/en/spr_nswgam_menu.farc"
EXPECTED_WIDTH = 2048
EXPECTED_HEIGHT = 2048
EXPECTED_BYTES = EXPECTED_WIDTH * EXPECTED_HEIGHT


def unpack_farc(raw: bytes) -> bytes:
    if len(raw) < 0x30 or raw[:4] != b"FArC":
        raise ValueError("Not the observed 0x30-byte FArC variant")
    offset, compressed, expanded = struct.unpack_from(">III", raw, 0x20)
    if offset != 0x30 or offset + compressed != len(raw):
        raise ValueError("FArC payload bounds do not match observed layout")
    data = gzip.decompress(raw[offset:offset + compressed])
    if len(data) != expanded:
        raise ValueError(f"FArC expanded-size mismatch: {len(data)} != {expanded}")
    return data


def type2_records(data: bytes) -> list[dict]:
    markers = []
    pos = 0
    while True:
        pos = data.find(b"TXP", pos)
        if pos < 0:
            break
        markers.append(pos)
        pos += 1
    result = []
    for i, start in enumerate(markers):
        if start + 4 > len(data) or data[start + 3] != 2:
            continue
        end = markers[i + 1] if i + 1 < len(markers) else len(data)
        if start + 24 > end:
            raise ValueError(f"Truncated TXP header at 0x{start:x}")
        width = struct.unpack_from("<H", data, start + 4)[0]
        height = struct.unpack_from("<H", data, start + 8)[0]
        fmt = struct.unpack_from("<I", data, start + 12)[0]
        payload = data[start + 24:end]
        result.append({
            "offset": start, "width": width, "height": height,
            "format_id": fmt, "payload": payload,
        })
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ipa", type=Path, help="Build 19 unsigned IPA")
    ap.add_argument("--record", type=int, default=2,
                    help="Zero-based TXP type-2 record index (default: 2)")
    ap.add_argument("--out", type=Path,
                    default=Path("app/src/main/assets/pjdvm39/exitmenu_2048x2048.bc5"),
                    help="Output raw BC5 payload path")
    ap.add_argument("--report", type=Path, default=Path("exitmenu-bc5-extract.json"))
    args = ap.parse_args()

    with zipfile.ZipFile(args.ipa) as ipa:
        names = ipa.namelist()
        candidates = [n for n in names if n.endswith(ARCHIVE_SUFFIX)]
        if not candidates:
            raise SystemExit(f"Could not find */{ARCHIVE_SUFFIX} inside IPA")
        archive_name = candidates[0]
        if len(candidates) > 1:
            print(f"Found {len(candidates)} locale archives; using {archive_name}")
        farc = ipa.read(archive_name)

    binary = unpack_farc(farc)
    records = type2_records(binary)
    if not 0 <= args.record < len(records):
        raise SystemExit(f"Record index out of range; found {len(records)} type-2 records")
    record = records[args.record]
    payload = record["payload"]
    if (record["width"], record["height"]) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        raise SystemExit(
            f"Selected record is {record['width']}x{record['height']}, "
            f"not {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}"
        )
    if record["format_id"] != 11:
        raise SystemExit(f"Unexpected observed format ID {record['format_id']}; expected 11")
    if len(payload) != EXPECTED_BYTES:
        raise SystemExit(f"Payload size {len(payload)} != expected {EXPECTED_BYTES}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(payload)
    report = {
        "ipa": args.ipa.name,
        "archive_entry": archive_name,
        "farc_bytes": len(farc),
        "bin_bytes": len(binary),
        "bin_sha256": hashlib.sha256(binary).hexdigest(),
        "type2_record_count": len(records),
        "selected_record_index": args.record,
        "txp_offset": record["offset"],
        "width": record["width"],
        "height": record["height"],
        "format_id_candidate": record["format_id"],
        "payload_bytes": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "output": str(args.out),
        "status": "structurally_validated_candidate_BC5_payload",
        "limitations": [
            "format ID 11 to BC5 remains a candidate mapping",
            "channel swizzle and runtime UV/layout are not validated",
            "no mip chain is extracted",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
