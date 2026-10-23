# Windows / Android Studio setup

This is a native Android ARM64 starter project, not a completed game port. It does not load or execute the iOS Mach-O binary, implement a complete NVN renderer, or include game packages.

## Install prerequisites
1. Install Android Studio.
2. In SDK Manager, install Android SDK Platform 35, Build-Tools, Platform-Tools, Command-line Tools, NDK (Side by side), and CMake 3.22.1.
3. Use JDK 17 (Android Studio's bundled JBR is often sufficient).
4. Set ANDROID_HOME or ANDROID_SDK_ROOT to the SDK directory if building from a terminal.

## Open and build
1. Open the repository root (the folder containing settings.gradle) in Android Studio.
2. Complete Gradle sync.
3. Build the app debug variant for arm64-v8a.
4. Expected APK path: app/build/outputs/apk/debug/app-debug.apk.

## Device smoke test
Connect an ARM64 Android device with USB debugging enabled, then run:
```powershell
adb devices
adb install -r .\app\build\outputs\apk\debug\app-debug.apk
adb logcat -s PJDVM39Port
```

## Limitations
No APK build or physical-device runtime validation is claimed. The starter project does not include the game executable, ROMFS, DLC, saves, a complete NVN-to-Vulkan translator, or a general MSL-to-SPIR-V compiler.
