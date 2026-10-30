# Mach-O executable section inventory — IPA 0.1.5 Build 19

Input: `PJDVM39-0.1.5b19-iOS-unsigned.ipa`
Executable: `Payload/PJDVM39.app/PJDVM39`
Architecture: ARM64 / Mach-O 64-bit / `MH_EXECUTE`
Analysis date: 2026-10-30

## Verified custom section sizes

Sizes below are from the Mach-O load-command section metadata, not estimates from filenames.

| Segment | Section | Size (bytes) | Size (MiB) |
|---|---|---:|---:|
| `__TEXT` | `__pjmaint` | 10,469,376 | 9.98 |
| `__TEXT` | `__pjmainp` | 180,224 | 0.17 |
| `__TEXT` | `__pjsdkt` | 5,521,408 | 5.27 |
| `__TEXT` | `__pjsdkp` | 458,752 | 0.44 |
| `__TEXT` | `__pjsubsdk0t` | 5,718,016 | 5.45 |
| `__TEXT` | `__pjsubsdk0p` | 131,072 | 0.13 |
| `__TEXT` | `__pjsubsdk1t` | 3,604,480 | 3.44 |
| `__TEXT` | `__pjsubsdk1p` | 442,368 | 0.42 |
| `__DATA` | `__pjmainr` | 3,063,808 | 2.92 |
| `__DATA` | `__pjsdkr` | 7,323,648 | 6.98 |
| `__DATA` | `__pjsubsdk0r` | 3,997,696 | 3.81 |
| `__DATA` | `__pjsubsdk1r` | 2,670,592 | 2.55 |
| `__DATA` | `swnvn` | 3,824 | 0.004 |
| `__DATA` | `swhle` | 1,040 | 0.001 |

## What this establishes

- The executable embeds several sizeable custom code/data sections. They are not ordinary loose resource files in the IPA.
- The `t`, `p`, and `r` suffixes and names are observed labels only. Their exact encoding, ownership, and semantics have not been decoded.
- The presence of a section named `swnvn` is a reverse-engineering clue, not proof that a complete Nintendo NVN runtime is embedded or that it can be reused on Android.
- The executable imports Apple frameworks including Metal/MetalKit/MetalFX, UIKit, GameController, AVFAudio/AudioToolbox, CoreMedia/CoreVideo/VideoToolbox, CoreHaptics, WebKit, and Swift runtime libraries. Android cannot resolve these imports.

## Porting implications

1. Do not load this Mach-O from Android JNI. It is an iOS executable with Apple framework dependencies, not an Android ELF shared object.
2. Preserve the original IPA as an analysis input. Any decoded section dumps should be treated as proprietary binary data and should not be committed to a public repository.
3. Next reverse-engineering work should identify section boundaries, inspect strings and Objective-C/Swift metadata, and map imported symbols to Android service replacements.
4. The existing Android Vulkan code only validates surface creation and a clear/present path. It is not a renderer for these custom sections and does not translate Metal or NVN commands.
5. A playable port still requires an authorized, technically viable implementation of the game/runtime. This IPA alone does not provide source code or a ready-to-link Android library.

## Current acceptance gates

- [ ] Android ARM64 debug APK builds in CI.
- [ ] APK installs on an ARM64 Android device.
- [ ] Vulkan surface smoke test presents successfully on-device.
- [ ] Game-specific runtime and asset loading are implemented.
- [ ] Audio/controller/input and lifecycle replacements are implemented.
- [ ] Game content renders and gameplay is validated.

A successful smoke-test APK is not a playable game port.
