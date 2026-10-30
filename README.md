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
