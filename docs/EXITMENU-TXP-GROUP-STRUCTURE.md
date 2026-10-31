# ExitMenu TXP group structure — Build 19

## Newly verified structural pattern

The English Build 19 BIN has 22 literal TXP markers: one TXP03, seven TXP04, and fourteen TXP02 records.

The seven TXP04 markers occur at:

`0x1314, 0x51358, 0x55139C, 0xA513E0, 0xF51424, 0x1451468, 0x19514AC`

Each TXP04 marker is exactly 0x14 bytes before an even-indexed TXP02 record:

| Group candidate | TXP04 offset | Following TXP02 record | Dimensions | Next TXP02 record | Dimensions |
|---:|---:|---:|---:|---:|---:|
| 0 | 0x1314 | 0 @ 0x1328 | 512×512 | 1 @ 0x41340 | 256×256 |
| 1 | 0x51358 | 2 @ 0x5136C | 2048×2048 | 3 @ 0x451384 | 1024×1024 |
| 2 | 0x55139C | 4 @ 0x5513B0 | 2048×2048 | 5 @ 0x9513C8 | 1024×1024 |
| 3 | 0xA513E0 | 6 @ 0xA513F4 | 2048×2048 | 7 @ 0xE5140C | 1024×1024 |
| 4 | 0xF51424 | 8 @ 0xF51438 | 2048×2048 | 9 @ 0x1351450 | 1024×1024 |
| 5 | 0x1451468 | 10 @ 0x145147C | 2048×2048 | 11 @ 0x1851494 | 1024×1024 |
| 6 | 0x19514AC | 12 @ 0x19514C0 | 2048×2048 | 13 @ 0x1D514D8 | 1024×1024 |

This is a strong, repeatable seven-pair grouping pattern in the marker sequence. It aligns in count with the seven ASCII identifiers `MERGE_BC5COMP_0` through `_6` found in the pre-TXP header. However, this count match alone does not prove the identifiers name these exact pairs or define the two records' roles. Keep the mapping provisional.

## TXP04 raw fields

All seven TXP04 headers share the same first 20-byte pattern: tag `0x04`; raw u32 words at relative offsets 0x04, 0x08, 0x0C are `2`, `0x01010102`, `0x14`; the following TXP02 marker begins at TXP04 + 0x14. The next 16 bytes are the TXP02 header, not part of the TXP04 marker header. The two bytes at relative offset 0x12 vary for the first group (`0x0004`) versus the remaining six (`0x0040`). This reports bytes only and does not assign undocumented meanings.

## TXP03 descriptor-like area

The TXP03 marker at `0x12EC` contains a count-like value of 7 and seven 32-bit values at relative offsets `0x10` through `0x28`. Their packed 16-bit patterns form a regular 0x44-byte stride sequence. The area needs schema and cross-reference validation before these values can be called offsets or descriptor pointers.

## Engineering implication

The parser milestone is no longer to treat all 14 textures as an unstructured flat list. Preserve the observed seven groups of two TXP02 records, expose each group's TXP04 bytes, and retain `MERGE_BC5COMP_n` as unverified candidate labels. Next compare the two images within each pair (dimensions, hashes, channel previews, and image correlation) and inspect the corresponding merge-composition data in the header section. This may reveal whether the 2048×2048 and 1024×1024 records are paired source/mask resources, alternate resolutions, or separate inputs to a merge operation.

No sprite UV rectangles, draw order, or final color reconstruction have been recovered yet.
