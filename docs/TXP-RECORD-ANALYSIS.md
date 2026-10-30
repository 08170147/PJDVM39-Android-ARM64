# TXP record boundary analysis — ExitMenu Build 19

Input: extracted `spr_nswgam_menu.bin` from each of the five localized ExitMenu FArC archives.

## Verified cross-locale observations

All five language variants have the same expanded BIN size (31,790,320 bytes), the same 22 literal `TXP` marker offsets, and the same marker type sequence.

The 22 markers comprise:
- one type-3 marker at offset 4,844;
- seven type-4 markers;
- fourteen type-2 markers.

The type-4 markers are immediately followed by a type-2 marker at +20 bytes. The type-2 records expose a 24-byte candidate header. Interpreting the two 16-bit fields at offsets +4 and +8 as width and height yields payload lengths exactly equal to width × height for all fourteen records, when each payload ends at the next TXP marker.

## Type-2 records

| BIN offset | Candidate width × height | Format ID (u32 LE) | Payload bytes |
|---:|---:|---:|---:|
| 4,904 | 512 × 512 | 11 | 262,144 |
| 267,072 | 256 × 256 | 11 | 65,536 |
| 332,652 | 2,048 × 2,048 | 11 | 4,194,304 |
| 4,526,980 | 1,024 × 1,024 | 11 | 1,048,576 |
| 5,575,600 | 2,048 × 2,048 | 11 | 4,194,304 |
| 9,769,928 | 1,024 × 1,024 | 11 | 1,048,576 |
| 10,818,548 | 2,048 × 2,048 | 11 | 4,194,304 |
| 15,012,876 | 1,024 × 1,024 | 11 | 1,048,576 |
| 16,061,496 | 2,048 × 2,048 | 11 | 4,194,304 |
| 20,255,824 | 1,024 × 1,024 | 11 | 1,048,576 |
| 21,304,444 | 2,048 × 2,048 | 11 | 4,194,304 |
| 25,498,772 | 1,024 × 1,024 | 11 | 1,048,576 |
| 26,547,392 | 2,048 × 2,048 | 11 | 4,194,304 |
| 30,741,720 | 1,024 × 1,024 | 11 | 1,048,576 |

The two candidate dimensions and the byte-count relationship are repeatable observations. The field meanings are still provisional; format ID 11 has not been mapped to a documented pixel format.

## Locale comparison

Comparing SHA-256 hashes of each type-2 payload at the same offsets across EN/JP/KR/TW/CN:

- The 512×512 and 256×256 payloads are byte-identical in all five languages.
- The first 2048×2048 / 1024×1024 pair has three distinct payload hashes across the five languages.
- The next pair has three distinct hashes.
- The next pair has five distinct hashes.
- The following pair has one distinct hash.
- The final two pairs have two distinct hashes each.

This is consistent with some shared UI resources and some locale-dependent resources, but does not identify the actual images.

## Critical limitation: layout is not yet decoded

Treating each payload as a row-major 8-bit grayscale image produces regular vertical striping rather than a confirmed usable texture. Therefore the equality `payload_bytes == width * height` is a useful boundary/size invariant, not proof of a linear R8 image. The data may use a tiled/swizzled GPU layout or another format-specific organization.

Do not upload these bytes directly as an Android `R8` texture until the tiling, channel interpretation, row pitch, and format ID are validated. The next milestone is to identify the texture layout and decode one small known resource with a visual reference.

## Reproduce

```sh
python3 tools/inspect_single_entry_farc.py spr_nswgam_menu.farc --extract-to spr_nswgam_menu.bin
python3 tools/inspect_exitmenu_bin.py spr_nswgam_menu.bin --json menu-bin-report.json
python3 tools/inspect_txp_records.py spr_nswgam_menu.bin --json txp-report.json
```

The new inspector reports candidate dimensions, format ID, payload boundary, byte count, and SHA-256. It does not decode or render image pixels.
