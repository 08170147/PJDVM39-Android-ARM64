# ExitMenu BC5 channel inspection — Build 19

## Verified extraction target

The local Build 19 IPA contains `Payload/PJDVM39.app/ExitMenu/en/rom_switch/rom/2d/spr_nswgam_menu.farc`.
After unpacking the observed FArC gzip payload, TXP type-2 record index 2 is:

- TXP marker offset: `0x5136C`
- Dimensions: `2048 × 2048`
- Observed format ID: `11`
- Payload length: `4,194,304` bytes
- Payload SHA-256: `f666638311b1ccf0372120212e0fb7ed72157e8d6cbbfaaf25f3a2726ddd733b`

The extractor validates these structural properties. The mapping from format ID 11 to BC5_UNORM remains a candidate interpretation, not a recovered original-engine enum definition.

## Channel observations

The payload was decoded as two BC4 blocks per 4×4 BC5 block and each channel was inspected independently as grayscale:

- **R channel:** contains the detailed grayscale illustration and many UI atlas elements: character artwork, long button frames, text/glyph regions, and smaller icons.
- **G channel:** contains a high-contrast silhouette/coverage-like representation of the large character and selected UI shapes. Many background regions are black while foreground shapes are bright.

This is evidence that the two channels carry different image information. It is **not** proof that G is the game's alpha channel or that R is final color. BC5 has two scalar channels and no alpha channel. The original runtime may combine these values with additional color constants, shader math, vertex tint, or other texture resources.

## Runtime test interpretation

The real-asset Android screenshot showed the expected atlas-like composition with red/green diagnostic channel coloring. It confirms the candidate payload can be uploaded, sampled, and drawn on the Adreno 735 test device. It does not validate the original UI layout, channel swizzle, texture coordinates, blending, or menu composition.

The channel-split diagnostic shader now shows R as grayscale on the left half and G as grayscale on the right half. Use it with the real extracted asset in the same APK. Do not use the synthetic fixture or a CI APK that omits the local IPA asset to infer channel semantics.

## Next reverse-engineering steps

1. Compare the R and G channel previews at full resolution to determine whether G is a binary mask, a soft coverage mask, or an independent grayscale layer.
2. Inspect the seven `MERGE_BC5COMP_0..6` identifiers and TXP03/TXP04 metadata to find the composition records that reference the texture payloads. Keep field names provisional until offsets and record boundaries prove their meaning.
3. Recover the original per-sprite UV rectangles, destination rectangles, layer order, and blend state from the menu resource metadata or executable data.
4. Only after those values are recovered, build a 2D UI compositor and compare a rendered Android menu against a reference image.

A channel preview is an inspection aid, not a final-color reconstruction.

## Follow-up visual comparison (2026-10-31)

The full-resolution side-by-side grayscale previews were inspected. R carries continuous grayscale detail across the large character illustration and the UI atlas. G is much more threshold-like: the large character silhouette and selected UI glyphs are bright against large black regions. The G image also contains soft edge falloff around several shapes, so it should not be described as strictly binary.

A useful **test hypothesis** is that R may be a grayscale/intensity source and G may be a coverage/opacity-like mask, with a shader or material supplying the final tint. This is more plausible than treating R and G as independent red and green display colors, but it is not yet proven. BC5 itself does not identify channel semantics; only the original material/shader or a rendered reference can establish them.

As a diagnostic-only experiment, combining the R grayscale image as RGB with G as the PNG alpha channel produces a visually coherent atlas with transparent black regions. This experiment does not prove that the original game uses G as alpha: the atlas contains broad bright UI regions in G as well, and material tint/blend settings remain unknown.

The character artwork appears upside down within the atlas image as decoded. Do not rotate the entire texture blindly: the correct orientation may be specified per sprite by UV coordinates or transform metadata.

## Updated next step

Prioritize recovering the material/shader convention and sprite rectangles before attempting a full menu composition. Keep three interpretations open until corroborated: (a) R=intensity, G=coverage; (b) R/G are two independent material inputs; (c) the observed BC5 candidate format/layout is only partially decoded. Validate with the original resource metadata and a reference screenshot.
