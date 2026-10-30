# IPA audit: PJDVM39 0.1.5 (Build 19)

Date: 2026-10-30
Input: `PJDVM39-0.1.5b19-iOS-unsigned.ipa`

## Verified container metadata

- Bundle identifier: `com.local.switchioslab`
- Executable: `PJDVM39`
- CFBundleShortVersionString: `0.1.5`
- CFBundleVersion: `19`
- MinimumOSVersion: `17.0`
- Required device capability: `arm64`
- Main executable: Mach-O 64-bit ARM64, file type `MH_EXECUTE`
- Main executable size: 46,333,392 bytes
- IPA archive size: 47,979,512 bytes

## Verified native dependencies

The executable links Apple platform frameworks including UIKit, Foundation, Metal, MetalKit, MetalFX, QuartzCore, CoreGraphics, CoreVideo, CoreMedia, VideoToolbox, AVFAudio, AudioToolbox, GameController, CoreHaptics, WebKit and Swift runtime libraries.

This confirms that the executable is an iOS application binary, not an Android ELF library. Renaming or repackaging it cannot produce a working Android app.

## Notable executable layout

The Mach-O contains custom sections named `__pjmaint`, `__pjmainp`, `__pjsdkt`, `__pjsdkp`, `__pjsubsdk0t`, `__pjsubsdk0p`, `__pjsubsdk1t`, `__pjsubsdk1p`, and corresponding data sections including `__pjmainr`, `__pjsdkr`, `__pjsubsdk0r`, and `__pjsubsdk1r`. It also contains `swnvn` and `swhle` data sections.

These names are useful reverse-engineering leads, but their exact internal formats and semantics have not yet been established. Do not treat them as proof of a complete, reusable Switch runtime or source code.

## Porting implications

1. Keep the Android ARM64 project as a separate native implementation. Do not attempt to load the Mach-O executable with Android's dynamic linker.
2. Continue extracting and documenting app assets and custom Mach-O sections; determine which are app resources, executable code, SDK payloads, or runtime data.
3. Inventory Objective-C/Swift entry points and imported symbols to identify the iOS-specific shell and services.
4. Determine the actual graphics command path before selecting a translation strategy. The iOS binary links Metal; Android's Vulkan smoke test is only a surface/presentation proof and is not a Metal-to-Vulkan translator.
5. Audio, controller, media, file access, and lifecycle services need Android-native replacements.
6. A playable port requires the relevant implementation/source or a lawful, technically viable reimplementation of the proprietary runtime. This IPA alone does not provide portable Android source.

## Current Android repository status

The repository is an infrastructure skeleton: Java Activity + C++ JNI + ARM64-only Gradle configuration and a Vulkan one-frame clear/present smoke test. It is not yet a game port and has no validated playable APK. CI success, APK artifact creation, and real-device testing remain separate acceptance gates.
