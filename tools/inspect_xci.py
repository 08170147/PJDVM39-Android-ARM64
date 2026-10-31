#!/usr/bin/env python3
"""Read-only structural inventory for a Nintendo Switch XCI image.

This tool reads the public XCI/HFS0 container structure only. It does not
decrypt NCA files, access console keys, modify the image, or extract content.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

CARD_HEADER_OFFSET = 0x1000
CARD_MAGIC_OFFSET = CARD_HEADER_OFFSET + 0x100
ROOT_HFS0_OFFSET = 0x10000
HFS0_MAGIC = b"HFS0"
HFS0_ENTRY_SIZE = 0x40


def read_exact(file, offset: int, size: int) -> bytes:
    file.seek(offset)
    data = file.read(size)
    if len(data) != size:
        raise ValueError(f"Truncated input at 0x{offset:x}: wanted {size} bytes")
    return data


def parse_hfs0(file, offset: int, limit: int) -> list[dict]:
    header = read_exact(file, offset, 0x10)
    if header[:4] != HFS0_MAGIC:
        raise ValueError(f"Expected HFS0 at 0x{offset:x}, found {header[:4]!r}")

    count, string_size = struct.unpack_from("<II", header, 4)
    if count > 100000:
        raise ValueError(f"Implausible HFS0 entry count: {count}")

    table_size = count * HFS0_ENTRY_SIZE
    strings_offset = offset + 0x10 + table_size
    data_offset = strings_offset + string_size
    if data_offset > limit:
        raise ValueError("HFS0 tables extend beyond the containing file/partition")

    entries_raw = read_exact(file, offset + 0x10, table_size)
    strings = read_exact(file, strings_offset, string_size)
    entries = []

    for index in range(count):
        pos = index * HFS0_ENTRY_SIZE
        relative_offset, size, name_offset, hashed_size = struct.unpack_from(
            "<QQII", entries_raw, pos
        )
        if name_offset >= len(strings):
            raise ValueError(f"Entry {index} has an invalid name offset")
        end = strings.find(b"\0", name_offset)
        if end < 0:
            raise ValueError(f"Entry {index} has an unterminated filename")
        name = strings[name_offset:end].decode("utf-8", "replace")
        absolute_offset = data_offset + relative_offset
        if absolute_offset < data_offset or absolute_offset + size > limit:
            raise ValueError(f"Entry {name!r} extends beyond its containing region")
        entries.append({
            "name": name,
            "offset": absolute_offset,
            "size_bytes": size,
            "hashed_region_bytes": hashed_size,
        })
    return entries


def inspect(path: Path) -> dict:
    with path.open("rb") as file:
        file_size = path.stat().st_size
        if file_size <= ROOT_HFS0_OFFSET:
            raise ValueError("File is too small to contain the documented XCI layout")

        magic = read_exact(file, CARD_MAGIC_OFFSET, 4)
        if magic != b"HEAD":
            raise ValueError(
                f"XCI card-header magic not found at 0x{CARD_MAGIC_OFFSET:x}: {magic!r}"
            )

        root_entries = parse_hfs0(file, ROOT_HFS0_OFFSET, file_size)
        partitions = []
        for item in root_entries:
            partition = dict(item)
            partition["files"] = []
            if item["name"] in {"secure", "normal", "update", "logo"}:
                partition["files"] = parse_hfs0(
                    file, item["offset"], item["offset"] + item["size_bytes"]
                )
            partitions.append(partition)

    secure_files = next(
        (p["files"] for p in partitions if p["name"] == "secure"), []
    )
    nca_files = [
        {"name": item["name"], "size_bytes": item["size_bytes"]}
        for item in secure_files if item["name"].lower().endswith(".nca")
    ]
    return {
        "file": path.name,
        "file_size_bytes": file_size,
        "card_header_offset": CARD_HEADER_OFFSET,
        "card_header_magic": magic.decode("ascii"),
        "root_hfs0_offset": ROOT_HFS0_OFFSET,
        "root_partitions": partitions,
        "secure_nca_inventory": nca_files,
        "nca_count": len(nca_files),
        "status": "container_metadata_only_no_decryption_or_extraction",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xci", type=Path, help="Locally owned XCI image")
    parser.add_argument("--json", type=Path, help="Optional JSON report path")
    args = parser.parse_args()

    report = inspect(args.xci)
    print(f"file: {report['file']}")
    print(f"file_size_bytes: {report['file_size_bytes']}")
    print(f"card_header_magic: {report['card_header_magic']}")
    print(f"root_hfs0_offset: 0x{report['root_hfs0_offset']:x}")
    print("partitions:")
    for partition in report["root_partitions"]:
        print(f"  {partition['name']}: {partition['size_bytes']} bytes")
        for item in partition["files"]:
            print(f"    {item['name']}: {item['size_bytes']} bytes")
    print(f"secure_nca_count: {report['nca_count']}")
    print("NOTE: NCA contents remain encrypted and are not opened or extracted.")

    if args.json:
        args.json.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"json_report: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
