# PJDV M39 Android ARM64 Port Skeleton

Infrastructure-only Android starter project, not a playable game port.

## Current scope
- Android Java Activity + C++ JNI native library.
- ARM64-only build configuration (`arm64-v8a`).
- One-shot Vulkan Android surface test: upload an optional 2048x2048 BC5 ExitMenu candidate (or a 4x4 synthetic fallback), sample it through a descriptor-backed graphics pipeline, draw a fullscreen triangle, and present one swapchain image.
- Vulkan capability / device probe reports in the app UI.
- BC5 image upload, image view, sampler, descriptor binding, shader sampling, and fullscreen draw are exercised by the one-frame diagnostic path.
- Shader migration research, audit reports, and helper scripts.

## Build prerequisites
- Android SDK platform 35 and Build Tools 35.0.0
- Android NDK 27.2.12479018 (or another compatible NDK)
- CMake 3.22.1
- Java 17 and Gradle 8.9 (Android Studio can manage Gradle for local builds)

Open this repository root in Android Studio, sync Gradle, then build the `app` debug variant. For CI, the GitHub Actions workflow in `.github/workflows/android-smoke.yml` attempts to build and upload the debug APK artifact.

## Limitations
- The Vulkan path is a one-shot BC5 diagnostic draw/present test, not a game renderer.
- No original game executable is linked or run.
- No complete NVN-to-Vulkan translation or general MSL-to-SPIR-V compiler is implemented.
- No game package, ROMFS, DLC, or save files are included.
- An APK is not considered validated until the CI build succeeds and the artifact is available; a physical-device test is still required to confirm Vulkan presentation on real hardware.

See [`docs/IPA-0.1.5b19-audit.md`](docs/IPA-0.1.5b19-audit.md) for verified findings from the 0.1.5 Build 19 IPA. See `README_WINDOWS.md` for Windows-specific setup and preflight instructions.

## Latest reverse-engineering notes
- [Mach-O custom section inventory](docs/EXECUTABLE-SECTION-INVENTORY.md): verified section names/sizes and porting implications.
- [Renderer/resource inventory](docs/RENDERER-RESOURCE-INVENTORY.md): verified Metal cache, shader-map, controller-glyph, and package-catalog counts.
- [ExitMenu BC5 channel analysis](docs/EXITMENU-CHANNEL-ANALYSIS.md): candidate R/G channel interpretation and unresolved material behavior.
- [ExitMenu localization comparison](docs/EXITMENU-LOCALIZATION-COMPARISON.md): shared TXP structure and language-specific payload hashes across five locales.

## ExitMenu BC5 extraction (Build 19)

With the original Build 19 IPA available locally, extract the observed 2048x2048
ExitMenu texture candidate directly into the Android assets directory:

```bash
python3 tools/extract_exitmenu_bc5_from_ipa.py /path/to/PJDVM39-0.1.5b19-iOS-unsigned.ipa
```

The helper validates the observed English FArC gzip container, TXP record
boundaries, candidate dimensions/format ID, and exact 4,194,304-byte payload.
It writes `app/src/main/assets/pjdvm39/exitmenu_2048x2048.bc5` and a JSON
hash report. The format-ID-to-BC5 mapping, channel swizzle, UV/layout, and
mipmap behavior remain hypotheses requiring runtime validation. The extracted
asset is not included in this repository; users must provide their own IPA.

For a one-command local extraction, validation, ARM64 debug build, and APK
asset-presence check, use:

```bash
bash ./build-with-ipa.sh /path/to/PJDVM39-0.1.5b19-iOS-unsigned.ipa
```

This convenience script keeps the IPA, extracted texture, and extraction report
local. It does not upload game data to GitHub. The CI workflow syntax-checks
this helper; the actual IPA-based build must be run locally with the Android
SDK/NDK and Gradle prerequisites installed.

## Compare localized ExitMenu texture payloads

Build 19 contains Chinese, Traditional Chinese, Korean, Japanese, and English
ExitMenu resource folders. Compare their TXP2 records locally:

```bash
python3 tools/compare_exitmenu_locales.py /path/to/PJDVM39-0.1.5b19-iOS-unsigned.ipa --out exitmenu_locale_comparison.json
```

The comparison checks record counts, offsets, dimensions, format IDs, and
payload hashes. See [the localization findings](docs/EXITMENU-LOCALIZATION-COMPARISON.md).
It reports byte differences only; it does not assume that every changed texture
is translated text.

## Shader metadata export
The metadata-only exporter can turn the IPA's shader map and per-library JSON into a local checklist without copying Metal binaries or game archives:

```bash
python3 tools/export_shader_inventory.py /path/to/PJDVM39-0.1.5b19-iOS-unsigned.ipa --out pjdvm39-shader-inventory.json
```

The exporter was tested against Build 19: 808/808 shader-map records resolved to per-shader metadata (0 missing). This is metadata coverage only, not Vulkan shader compatibility or visual validation.
- [Metal-to-Vulkan binding plan](docs/METAL-TO-VULKAN-BINDING-PLAN.md): verified shader binding counts, candidate Vulkan mappings, and unresolved translation requirements.
- [ExitMenu FArC format notes](docs/EXITMENU-FARC-FORMAT.md) and [local inspector](tools/inspect_single_entry_farc.py): validates the observed single-entry gzip container without bundling game assets.
- [ExitMenu BIN structure notes](docs/EXITMENU-BIN-STRUCTURE.md) and [BIN inspector](tools/inspect_exitmenu_bin.py): inventories resource-name strings and TXP marker offsets without claiming a full decoder.
