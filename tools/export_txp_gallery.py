#!/usr/bin/env python3
"""Export every observed TXP02 record as candidate BC5 RGB and R/G grayscale PNGs.

Requires Pillow only for PNG encoding? No: uses the repository's stdlib PNG writer.
The output is diagnostic and does not infer original channel semantics.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from decode_txp_bc5 import decode_bc5, find_records, write_png_rgb


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path, help="Extracted spr_nswgam_menu.bin")
    parser.add_argument("--out-dir", type=Path, default=Path("txp_gallery"))
    args = parser.parse_args()

    records = find_records(args.binary.read_bytes())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for index, record in enumerate(records):
        if record["format_id"] != 11:
            manifest.append({"index": index, "offset": hex(record["offset"]),
                             "format_id": record["format_id"], "status": "skipped-unknown-format"})
            continue
        width, height = record["width"], record["height"]
        rgb = decode_bc5(record["payload"], width, height)
        r = bytearray(width * height * 3)
        g = bytearray(width * height * 3)
        for pixel in range(width * height):
            rv, gv = rgb[pixel * 3], rgb[pixel * 3 + 1]
            p = pixel * 3
            r[p:p + 3] = bytes((rv, rv, rv))
            g[p:p + 3] = bytes((gv, gv, gv))
        stem = f"txp02_{index:02d}_{width}x{height}"
        paths = {}
        for suffix, pixels in (("rg", rgb), ("r", r), ("g", g)):
            name = f"{stem}_{suffix}.png"
            write_png_rgb(args.out_dir / name, width, height, bytes(pixels))
            paths[suffix] = name
        manifest.append({
            "index": index, "offset": hex(record["offset"]),
            "width": width, "height": height,
            "format_id": record["format_id"],
            "payload_bytes": len(record["payload"]),
            "files": paths,
            "interpretation": "candidate BC5 decode; channel semantics unverified"
        })

    (args.out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"records": len(records), "output_dir": str(args.out_dir),
                      "manifest": "manifest.json"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
