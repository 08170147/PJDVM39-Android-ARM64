# Windows / Android Studio setup

This is a native Android ARM64 starter project, not a completed game port. It does not load or execute the iOS Mach-O binary, implement a complete NVN renderer, or include game packages.

## Install prerequisites
1. Install Android Studio.
2. In SDK Manager, install Android SDK Platform 35, Build-Tools 35.0.0, Platform-Tools, Command-line Tools, NDK 27.2.12479018, and CMake 3.22.1.
3. Use JDK 17 (Android Studio's bundled JBR is often sufficient).
4. Install Gradle 8.9 and ensure `gradle` is available in PowerShell PATH, or use Android Studio to sync/build.
5. Install the LunarG Vulkan SDK for Windows and add its `Bin` directory to PATH. The IPA build helper requires both `glslangValidator.exe` and `spirv-val.exe`.
6. Set `ANDROID_HOME` or `ANDROID_SDK_ROOT` to the SDK directory if building from a terminal.

## Build a diagnostic APK without the IPA
Open the repository root (the folder containing `settings.gradle`) in Android Studio, complete Gradle sync, and build the `app` debug variant. The result is `app/build/outputs/apk/debug/app-debug.apk`. This APK uses the synthetic 4x4 BC5 fallback unless the real asset has already been extracted locally.

## Build with the real ExitMenu asset and channel-split shader
Keep the Build 19 IPA on your own computer. From PowerShell in the repository root, run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\\build-with-ipa.ps1 "C:\\path\\to\\PJDVM39-0.1.5b19-iOS-unsigned.ipa"
```

The helper extracts the observed 2048x2048 BC5 candidate locally, verifies its 4,194,304-byte length and SHA-256, compiles and validates both current shaders, builds the ARM64 debug APK, and checks that the APK contains the texture and both SPIR-V modules. Output:

`PJDVM39-Android-ARM64-ExitMenu-ChannelSplit.apk`

The IPA, extracted game asset, and hash report stay local; they are not uploaded by this script.

## Device smoke test
Connect an ARM64 Android device with USB debugging enabled, then run:

```powershell
adb devices
adb install -r .\\PJDVM39-Android-ARM64-ExitMenu-ChannelSplit.apk
adb logcat -s PJDVM39Port
```

If Android reports a signature mismatch, uninstall the previously installed diagnostic build before installing this locally signed build.

## Limitations
The Vulkan path is a one-shot BC5 diagnostic draw/present test, not a game renderer. No original game executable is linked or run. No complete NVN-to-Vulkan translation or general MSL-to-SPIR-V compiler is implemented. No game package, ROMFS, DLC, or save files are included. A successful APK build is not proof of a playable port; physical-device validation is still required.
