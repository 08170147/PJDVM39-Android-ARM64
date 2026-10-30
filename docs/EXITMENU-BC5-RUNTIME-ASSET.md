# ExitMenu BC5 runtime asset hook

The Vulkan diagnostic renderer can optionally load a raw BC5 payload from:

`app/src/main/assets/pjdvm39/exitmenu_2048x2048.bc5`

Expected payload:
- 2048 × 2048 texels
- BC5_UNORM block-compressed bytes
- 4 × 4 texels per 16-byte block
- Total size: 4,194,304 bytes
- No TXP header, mip chain, row padding, or container metadata

The payload is currently **not bundled**. The IPA TXP record must first be extracted and validated, then its raw payload copied to the path above. Until then, the app deliberately falls back to a synthetic 4 × 4 BC5 fixture and reports that fallback in the on-device log.

This hook only tests a single-level BC5 upload and sample. It does not yet decode the TXP container, infer channel swizzles, load mip levels, reproduce the ExitMenu layout, or port the game renderer.
