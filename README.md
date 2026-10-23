# PJDV M39 Android ARM64 Port Skeleton

Infrastructure-only Android starter project, not a playable game port.

## Current scope
- Android Java Activity + C++ JNI native library.
- ARM64-only build configuration (`arm64-v8a`).
- Vulkan capability / surface smoke-test scaffolding.
- Shader migration research, audit reports, and helper scripts.

## Build prerequisites
- Android Studio / Android SDK platform 35
- Android NDK
- CMake 3.22.1
- Gradle via Android Studio

Open this repository root in Android Studio, sync Gradle, then build the `app` debug variant.

## Limitations
- No original game executable is linked or run.
- No complete NVN-to-Vulkan translation or general MSL-to-SPIR-V compiler is implemented.
- No game package, ROMFS, DLC, or save files are included.
- No APK has been built or validated on a physical Android device as part of this upload.

See `README_WINDOWS.md` for Windows-specific setup and preflight instructions when available.
