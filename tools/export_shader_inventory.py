#!/usr/bin/env python3
"""Export shader mapping and non-binary pipeline metadata from a PJDVM39 IPA.

This script does not extract or redistribute executable code, Metal libraries,
or game archives. It writes a JSON checklist from the IPA's TSV/JSON metadata.
"""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import PurePosixPath


def find_member(names: set[str], suffix: str) -> str:
    matches = [name for name in names if name.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one {suffix!r}, found {len(matches)}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ipa", help="Path to PJDVM39 .ipa file")
    parser.add_argument("--out", default="pjdvm39-shader-inventory.json")
    args = parser.parse_args()

    with zipfile.ZipFile(args.ipa) as archive:
        names = set(archive.namelist())
        shader_map_path = find_member(names, "RendererAssets/Shaders/shader_map.tsv")
        preparation_path = find_member(names, "RendererAssets/MetalCache/preparation.json")
        cache_dir = str(PurePosixPath(preparation_path).parent)

        rows = archive.read(shader_map_path).decode("utf-8-sig").splitlines()
        if not rows:
            raise RuntimeError("Shader map is empty")
        header = rows[0].split("\t")
        expected = ["package", "index", "stage", "dm_ctl_sha16"]
        if header[:4] != expected:
            raise RuntimeError(f"Unexpected shader-map header: {header}")

        records = []
        missing = []
        for line_number, line in enumerate(rows[1:], start=2):
            if not line.strip():
                continue
            fields = line.split("\t")
            if len(fields) < 4:
                raise RuntimeError(f"Malformed shader map line {line_number}")
            package, index, stage_label, shader_key = fields[:4]
            stage = {"頂點": "vs", "像素": "ps"}.get(stage_label, stage_label)
            metadata_path = f"{cache_dir}/{shader_key}_b.json"
            if metadata_path not in names:
                metadata_path = f"{cache_dir}/{shader_key}_b_sim.json"
            if metadata_path not in names:
                missing.append({"line": line_number, "package": package,
                                "stage": stage, "shader_key": shader_key})
                continue

            metadata = json.loads(archive.read(metadata_path))
            records.append({
                "package": package,
                "index": int(index),
                "stage": stage,
                "shader_key": shader_key,
                "metadata_file": PurePosixPath(metadata_path).name,
                "source": metadata.get("source"),
                "entry": metadata.get("entry"),
                "entry_kind": metadata.get("msl_entry_kind"),
                "threadgroup_size": metadata.get("threadgroup_size"),
                "bindings": metadata.get("bindings", []),
                "vertex_inputs": metadata.get("vertex_inputs", []),
                "raster": metadata.get("raster", {}),
                "notes": metadata.get("notes", []),
                "driver_unfillable": metadata.get("drv_unfillable", []),
            })

    result = {
        "format": "pjdvm39-shader-inventory-v1",
        "source_ipa": PurePosixPath(args.ipa).name,
        "shader_map_records": len(rows) - 1,
        "exported_records": len(records),
        "missing_metadata_records": missing,
        "records": records,
    }
    with open(args.out, "w", encoding="utf-8") as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.write("\n")

    print(f"Exported {len(records)} shader metadata records.")
    print(f"Missing metadata records: {len(missing)}.")
    print(f"Output: {args.out}")
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
