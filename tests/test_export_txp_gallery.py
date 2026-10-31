#!/usr/bin/env python3
"""Regression tests for the TXP BC5 gallery exporter (stdlib unittest)."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from decode_txp_bc5 import decode_bc5, find_records  # noqa: E402
from export_txp_gallery import main as gallery_main  # noqa: E402


def make_txp02(width: int, height: int, payload: bytes) -> bytes:
    header = bytearray(24)
    header[0:4] = b"TXP\x02"
    struct.pack_into("<H", header, 4, width)
    struct.pack_into("<H", header, 8, height)
    struct.pack_into("<I", header, 12, 11)
    return bytes(header) + payload


class GalleryExporterTests(unittest.TestCase):
    def test_finds_two_records_and_exact_bc5_payload_sizes(self):
        payload_a = bytes(range(16))  # one 4x4 BC5 block
        payload_b = bytes(range(32))  # two 4x4 blocks
        binary = b"prefix" + make_txp02(4, 4, payload_a) + b"gap" + make_txp02(8, 4, payload_b)
        records = find_records(binary)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["payload"], payload_a)
        self.assertEqual(records[1]["payload"], payload_b)
        self.assertEqual((records[1]["width"], records[1]["height"]), (8, 4))
        self.assertEqual(len(decode_bc5(records[0]["payload"], 4, 4)), 4 * 4 * 3)

    def test_rejects_bad_payload_length(self):
        with self.assertRaises(ValueError):
            decode_bc5(b"short", 4, 4)

    def test_gallery_writes_rg_and_individual_channels(self):
        payload = bytes([255, 0, 0, 0, 0, 0, 0, 0, 0, 255, 0, 0, 0, 0, 0, 0])
        binary = make_txp02(4, 4, payload)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "tiny.bin"
            out_dir = root / "gallery"
            source.write_bytes(binary)
            old_argv = sys.argv
            try:
                sys.argv = ["export_txp_gallery.py", str(source), "--out-dir", str(out_dir)]
                self.assertEqual(gallery_main(), 0)
            finally:
                sys.argv = old_argv
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest), 1)
            for key in ("rg", "r", "g"):
                self.assertTrue((out_dir / manifest[0]["files"][key]).is_file())


if __name__ == "__main__":
    unittest.main()
