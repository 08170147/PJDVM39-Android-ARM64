#!/usr/bin/env python3
import sys
import zipfile
from pathlib import Path

apk = Path(sys.argv[1] if len(sys.argv) > 1 else "app/build/outputs/apk/debug/app-debug.apk")
expected = (
    "assets/pjdvm39/bc5_sample.vert.spv",
    "assets/pjdvm39/bc5_sample.frag.spv",
)
if not apk.is_file():
    raise SystemExit(f"APK not found: {apk}")
with zipfile.ZipFile(apk) as zf:
    names = set(zf.namelist())
    for name in expected:
        if name not in names:
            raise SystemExit(f"Missing packaged shader asset: {name}")
        data = zf.read(name)
        if len(data) < 20 or data[:4] != bytes((3, 2, 35, 7)):
            raise SystemExit(f"Invalid SPIR-V magic or truncated module: {name}")
        if len(data) % 4:
            raise SystemExit(f"SPIR-V byte length is not word-aligned: {name}")
        print(f"PASS: {name} ({len(data)} bytes, SPIR-V magic OK)")
print("PASS: APK contains both validated BC5 shader modules")
