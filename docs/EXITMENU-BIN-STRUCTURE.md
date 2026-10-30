# ExitMenu embedded BIN: first structural observations

Input: the English `spr_nswgam_menu.farc` from IPA 0.1.5 Build 19.
The FArC payload was decompressed using the gzip stream beginning at byte 48.

## Verified observations

- Decompressed file size: **31,790,320 bytes**.
- SHA-256 is emitted by the included inspector for reproducibility.
- First two little-endian 32-bit words: `0` and `4844 (0x12EC)`.
- The region before byte `0x12EC` contains 73 printable ASCII identifier runs of at least four characters.
- Those identifiers include menu-related names such as `CHARA_MAINMENU_01`, `SELECTOR_ARCADE_TXT`, `SELECTOR_OPTION`, `FOOTER_BACK`, and `KEY_MAINMENU_01`.
- The byte sequence `TXP` occurs 22 times in the decompressed file. The first occurrence is at offset 4844.

These facts suggest that the initial region contains resource/index metadata and that `TXP` is a useful marker for further investigation. They do **not** establish the complete header schema, the meaning of the second word, or the internal structure of a TXP record.

## Reproduce locally

First decompress the archive with the existing FArC inspector:

```sh
python3 tools/inspect_single_entry_farc.py spr_nswgam_menu.farc --extract-to spr_nswgam_menu.bin
```

Then inspect the extracted binary:

```sh
python3 tools/inspect_exitmenu_bin.py spr_nswgam_menu.bin --json menu-bin-report.json
```

The script reports the prefix words, ASCII identifiers in the first header-sized region, literal `TXP` marker offsets, file size, and SHA-256. It intentionally does not decode or rewrite any asset payload.

## Next reverse-engineering task

Correlate the identifier table with the TXP marker positions and determine whether each TXP record describes a texture, a compressed texture block, or another resource object. Confirm field widths, endianness, record boundaries, and payload lengths across all five language variants before implementing a loader. Then decode one small, known menu texture and compare its dimensions/pixels with an independently known reference.

No texture decoding or Vulkan rendering is claimed by this inventory.
