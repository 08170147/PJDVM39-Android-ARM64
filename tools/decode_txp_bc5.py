#!/usr/bin/env python3
"""Decode the Build 19 TXP type-2 payloads as candidate BC5 blocks.

The decoder writes an RG debug visualization (R channel in red, G in green,
blue set to zero). It is not a reconstruction of the original full-color UI.
"""
from __future__ import annotations

import argparse
import json
import struct
import zlib
from pathlib import Path


def decode_bc4_block(block: bytes) -> list[int]:
    if len(block) != 8:
        raise ValueError("BC4 channel block must be exactly 8 bytes")
    endpoint0, endpoint1 = block[0], block[1]
    indices = int.from_bytes(block[2:8], "little")
    if endpoint0 > endpoint1:
        palette = [endpoint0, endpoint1]
        palette.extend(((7 - i) * endpoint0 + i * endpoint1) // 7 for i in range(1, 7))
    else:
        palette = [endpoint0, endpoint1]
        palette.extend(((5 - i) * endpoint0 + i * endpoint1) // 5 for i in range(1, 5))
        palette.extend((0, 255))
    return [palette[(indices >> (3 * pixel)) & 7] for pixel in range(16)]


def decode_bc5(payload: bytes, width: int, height: int) -> bytes:
    if width % 4 or height % 4:
        raise ValueError("BC5 dimensions must be multiples of 4")
    expected = (width // 4) * (height // 4) * 16
    if len(payload) != expected:
        raise ValueError(f"BC5 payload size mismatch: expected {expected}, got {len(payload)}")
    rgb = bytearray(width * height * 3)
    blocks_x = width // 4
    for block_y in range(height // 4):
        for block_x in range(blocks_x):
            start = (block_y * blocks_x + block_x) * 16
            red = decode_bc4_block(payload[start:start + 8])
            green = decode_bc4_block(payload[start + 8:start + 16])
            for py in range(4):
                for px in range(4):
                    local = py * 4 + px
                    pixel = ((block_y * 4 + py) * width + block_x * 4 + px) * 3
                    rgb[pixel] = red[local]
                    rgb[pixel + 1] = green[local]
                    rgb[pixel + 2] = 0
    return bytes(rgb)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xffffffff)


def write_png_rgb(path: Path, width: int, height: int, rgb: bytes) -> None:
    if len(rgb) != width * height * 3:
        raise ValueError("RGB buffer size mismatch")
    raw = b"".join(b"\x00" + rgb[y * width * 3:(y + 1) * width * 3] for y in range(height))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def find_records(data: bytes) -> list[dict]:
    offsets = []
    cursor = 0
    while True:
        pos = data.find(b"TXP", cursor)
        if pos < 0:
            break
        offsets.append(pos)
        cursor = pos + 1
    records = []
    for i, offset in enumerate(offsets):
        if offset + 4 > len(data) or data[offset + 3] != 2:
            continue
        end = offsets[i + 1] if i + 1 < len(offsets) else len(data)
        if offset + 24 > end:
            raise ValueError(f"Truncated TXP type-2 header at 0x{offset:x}")
        width = struct.unpack_from("<H", data, offset + 4)[0]
        height = struct.unpack_from("<H", data, offset + 8)[0]
        format_id = struct.unpack_from("<I", data, offset + 12)[0]
        records.append({"offset": offset, "width": width, "height": height,
                        "format_id": format_id, "payload": data[offset + 24:end]})
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path, help="Extracted spr_nswgam_menu.bin")
    parser.add_argument("--record", type=int, default=2,
                        help="Zero-based TXP type-2 record index (default: 2)")
    parser.add_argument("--out", type=Path, default=Path("txp_record_02_rg.png"))
    parser.add_argument("--channels", action="store_true",
                        help="Also write separate grayscale R and G channel previews")
    args = parser.parse_args()
    records = find_records(args.binary.read_bytes())
    if not 0 <= args.record < len(records):
        raise SystemExit(f"Record index out of range; found {len(records)} type-2 records")
    record = records[args.record]
    if record["format_id"] != 11:
        raise SystemExit(f"Unsupported observed format ID {record['format_id']}; expected 11")
    rgb = decode_bc5(record["payload"], record["width"], record["height"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_png_rgb(args.out, record["width"], record["height"], rgb)
    channel_paths = {}
    if args.channels:
        red = bytearray(len(rgb))
        green = bytearray(len(rgb))
        for pixel in range(record["width"] * record["height"]):
            r, g = rgb[pixel * 3], rgb[pixel * 3 + 1]
            red[pixel * 3:pixel * 3 + 3] = bytes((r, r, r))
            green[pixel * 3:pixel * 3 + 3] = bytes((g, g, g))
        red_path = args.out.with_name(args.out.stem + "_r.png")
        green_path = args.out.with_name(args.out.stem + "_g.png")
        write_png_rgb(red_path, record["width"], record["height"], bytes(red))
        write_png_rgb(green_path, record["width"], record["height"], bytes(green))
        channel_paths = {"r": str(red_path), "g": str(green_path)}
    print(json.dumps({
        "record_index": args.record, "record_offset": record["offset"],
        "width": record["width"], "height": record["height"],
        "format_id": record["format_id"], "payload_bytes": len(record["payload"]),
        "decoder": "BC5_UNORM_candidate", "preview": str(args.out),
        "preview_channels": "R shown as red; G shown as green; B set to zero",
        "separate_channel_previews": channel_paths,
        "warning": "Candidate BC5 decode; validate format/layout against runtime reference before shipping."
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
