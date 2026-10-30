# PJDV M39 Android ARM64 Port Skeleton

Infrastructure-only Android starter project, not a playable game port.

## Current scope
- Android Java Activity + C++ JNI native library.
- ARM64-only build configuration (`arm64-v8a`).
- One-shot Vulkan Android surface smoke test: create instance/surface, choose a graphics-and-present queue, clear a swapchain image, and present once.
- Vulkan capability / device probe reports in the app UI.
- Shader migration research, audit reports, and helper scripts.

## Build prerequisites
- Android SDK platform 35 and Build Tools 35.0.0
- Android NDK 27.2.12479018 (or another compatible NDK)
- CMake 3.22.1
- Java 17 and Gradle 8.9 (Android Studio can manage Gradle for local builds)

Open this repository root in Android Studio, sync Gradle, then build the `app` debug variant. For CI, the GitHub Actions workflow in `.github/workflows/android-smoke.yml` attempts to build and upload the debug APK artifact.

## Limitations
- The Vulkan path is a one-shot clear/present test, not a game renderer.
- No original game executable is linked or run.
- No complete NVN-to-Vulkan translation or general MSL-to-SPIR-V compiler is implemented.
- No game package, ROMFS, DLC, or save files are included.
- An APK is not considered validated until the CI build succeeds and the artifact is available; a physical-device test is still required to confirm Vulkan presentation on real hardware.

See [`docs/IPA-0.1.5b19-audit.md`](docs/IPA-0.1.5b19-audit.md) for verified findings from the 0.1.5 Build 19 IPA. See `README_WINDOWS.md` for Windows-specific setup and preflight instructions.

## Latest reverse-engineering notes
- [Mach-O custom section inventory](docs/EXECUTABLE-SECTION-INVENTORY.md): verified section names/sizes and porting implications.
- [Renderer/resource inventory](docs/RENDERER-RESOURCE-INVENTORY.md): verified Metal cache, shader-map, controller-glyph, and package-catalog counts.

## Shader metadata export
The metadata-only exporter can turn the IPA's shader map and per-library JSON into a local checklist without copying Metal binaries or game archives:

```bash
python3 tools/export_shader_inventory.py /path/to/PJDVM39-0.1.5b19-iOS-unsigned.ipa --out pjdvm39-shader-inventory.json
```

The exporter was tested against Build 19: 808/808 shader-map records resolved to per-shader metadata (0 missing). This is metadata coverage only, not Vulkan shader compatibility or visual validation.
- [Metal-to-Vulkan binding plan](docs/METAL-TO-VULKAN-BINDING-PLAN.md): verified shader binding counts, candidate Vulkan mappings, and unresolved translation requirements.
- [ExitMenu FArC format notes](docs/EXITMENU-FARC-FORMAT.md) and [local inspector](tools/inspect_single_entry_farc.py): validates the observed single-entry gzip container without bundling game assets.
- [ExitMenu BIN structure notes](docs/EXITMENU-BIN-STRUCTURE.md) and [BIN inspector](tools/inspect_exitmenu_bin.py): inventories resource-name strings and TXP marker offsets without claiming a full decoder.
