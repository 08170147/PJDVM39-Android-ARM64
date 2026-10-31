# TXP04 paired-record relationship test

## Scope and method

This note tests whether the two TXP02 records following each TXP04 are a conventional 2:1 mip pair. The seven TXP04 groups contain one 512x512 + 256x256 pair and six 2048x2048 + 1024x1024 pairs.

The English Build 19 IPA's `spr_nswgam_menu.farc` was decompressed to the 31,790,320-byte BIN. Each BC5 payload was decoded as two BC4 scalar channels. For each larger record, a simple 2x2 box average was calculated per channel and compared pixelwise with the paired smaller record.

## Result

The smaller records are **not validated as ordinary box-filter mipmaps** by this test.

| TXP04 group | Dimensions | R correlation | G correlation | R MAE | G MAE |
|---:|---|---:|---:|---:|---:|
| 0 | 512→256 | undefined* | undefined* | 26.15 | 64.00 |
| 1 | 2048→1024 | -0.0493 | 0.4198 | 53.87 | 34.15 |
| 2 | 2048→1024 | -0.0577 | 0.4843 | 58.93 | 31.70 |
| 3 | 2048→1024 | -0.0917 | 0.3589 | 51.54 | 29.46 |
| 4 | 2048→1024 | 0.0122 | 0.4503 | 40.93 | 25.60 |
| 5 | 2048→1024 | 0.0019 | 0.5678 | 34.36 | 16.29 |
| 6 | 2048→1024 | 0.0358 | 0.5571 | 30.67 | 18.86 |

*Group 0's decoded larger-record channel variance was zero, so Pearson correlation is undefined.

R correlation is near zero or slightly negative in groups 1–6. G correlation is moderate, but not high enough to establish a normal mipmap relationship. The paired smaller record may be a related mask, companion texture, alternate representation, or a mip generated with a different operation. None of those interpretations is proven.

## TXP04 header observations

The 20-byte TXP04 headers are identical in their first 18 bytes except for the final 16-bit field:

- Group 0: `545850040200000002010101140000002c000400`
- Groups 1–6: `545850040200000002010101140000002c004000`

Observed constants include `0x14` and `0x2c`; their semantics remain unknown. The final field is `0x0004` for group 0 and `0x0040` for groups 1–6. Do not label these as flags, dimensions, or formats without corroboration.

## Next tests

1. Render both records of each group independently on device using the same channel-split diagnostic.
2. Compare shape masks with multiple spatial transforms and filtering methods, not only box-average mip reduction.
3. Inspect the seven MERGE_BC5COMP names and TXP03 descriptors against these group boundaries.
4. Recover sprite rectangles and blending only after a descriptor-to-record mapping is demonstrated.

This is a negative/limiting result: record pairing is confirmed structurally, but mipmap semantics are not.
