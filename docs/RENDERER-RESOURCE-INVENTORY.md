# Renderer and resource inventory — IPA 0.1.5 Build 19

Input: `PJDVM39-0.1.5b19-iOS-unsigned.ipa`
Date: 2026-10-30
Method: inspect ZIP entry names/sizes and parse the shipped JSON/TSV metadata. No proprietary binary payloads are copied into this repository.

## Verified bundle inventory

- 2,889 files under `Payload/PJDVM39.app/`.
- Total uncompressed app-bundle file data: 100,472,328 bytes.
- `RendererAssets/`: 2,863 files.
  - 1,433 JSON files.
  - 1,429 `.metallib` files.
  - 1 TSV shader map.
- `ExitMenu/`: five language-specific resource groups (Japanese, English, Korean, Traditional Chinese, Simplified Chinese).
- Each language group includes an approximately 4.51 MB `spr_nswgam_menu.farc` archive.
- `Assets.car`: 2,850,968 bytes.
- `ControllerGlyphs/recipes.json`: 46 atlas entries and 257 edit recipes.
- `ImportCatalog.json`: format `pjdv-dlc-local-v1`, with 27 catalog entries. This is a catalog of referenced package IDs and hashed NCA filenames; the IPA inventory does not show those NCA payloads as bundled files.

## Shader inventory

`RendererAssets/Shaders/shader_map.tsv` contains 808 stage records across 404 package names:

- 404 vertex-stage records.
- 404 pixel/fragment-stage records.
- The package names include effects, particles, graphics utilities, and many HLSL-style material shader variants.

The Metal cache `preparation.json` lists 808 library records. Every record has status `source_ready`; none of these records has a non-empty `translation_notes` or `unfillable_driver_reads` field.

The cache contains 1,429 `.metallib` files, including 808 regular `_b.metallib` files and 621 `_b_sim.metallib` files. Per-library JSON metadata records shader stage, entry point, bindings, vertex inputs, raster state, and notes.

### Important qualification

`source_ready` is the status value recorded in the app's metadata. It does **not** mean Android-ready SPIR-V exists, nor does it prove visual correctness on Vulkan. The shipped `.metallib` files are Metal library binaries. The shader map and per-library JSON files are useful metadata, but the audit did not find a complete set of standalone MSL source files.

The only top-level `Shaders.msl` file is 693 bytes and contains a small rotating-triangle lab shader, not the game's complete shader source collection.

The per-shader JSON notes explicitly leave visual/input validation pending. A working Vulkan renderer still needs compatible shader source or a validated translation/decompilation path, descriptor/binding conversion, vertex input mapping, render-state conversion, and visual tests.

## What can be reused in the Android project

1. Use the 404 package names and 808 stage records to build a shader coverage checklist.
2. Use per-shader JSON binding metadata as a starting point for Vulkan descriptor-set and pipeline-layout mapping, after validating the metadata against actual shader behavior.
3. Use controller glyph recipes as a specification for platform-specific controller icon selection; validate atlas inputs and output rendering before integrating.
4. Treat `ExitMenu` FARC archives as game-format resources requiring a lawful parser/loader; do not assume they are standard ZIP files.
5. Treat the DLC import catalog as a list of references only. The referenced NCA payloads are not established as included in this IPA.

## Next technical milestone

Build a read-only metadata exporter that converts the 808 shader records into a machine-readable Android port checklist (package, stage, library key, entry point, resource bindings, vertex inputs, raster/depth/color state, and validation notes). Then select a small, representative group of shaders (simple copy, basic material, particle, and UI) for a Vulkan proof of concept.

Do not label the result a game port until the renderer, resource loading, input/audio services, and actual gameplay have been validated on an Android device.

## Metadata exporter validation

The repository now includes `tools/export_shader_inventory.py`. It was run against the supplied Build 19 IPA and successfully resolved all 808 shader-map rows to per-shader JSON metadata (808 exported, 0 missing). This confirms the metadata join is complete for this build; it does not validate Metal-to-Vulkan translation or runtime visuals.
