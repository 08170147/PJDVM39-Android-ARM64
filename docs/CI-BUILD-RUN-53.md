# Android ARM64 CI build record — Run 53

- Workflow: Android ARM64 smoke checks
- Run: 53
- Commit: `42a7d46b17f23512c49fccf43e13c32f862c214a`
- Result: `success`
- Job: `android-build`
- Build step: `gradle :app:assembleDebug` — success
- Manifest verification: success
- Uploaded artifact: `pjdvm39-arm64-debug-apk`
- Artifact ID: `12981519804`
- Artifact SHA-256 (ZIP): `0a80822e2f990aadcb94d2b1da5d60982a0f6cc2da870cb015998106f4fa345c`

## Downloaded artifact inspection

The workflow artifact was downloaded and its ZIP contents inspected:

- APK: `app-debug.apk`
- APK size: 1,074,727 bytes
- APK SHA-256: `4f9a054bdadba6e3bc2c69e861ddc417c1a8796f97b4835187a15d30209a1a30`
- Native library entry: `lib/arm64-v8a/libpjdvm39_port.so`
- Native library: ELF64 shared object, AArch64, Android API 24 / NDK r27
- JNI exports verified: `nativeGetReport`, `nativeRenderFrame`

This verifies a signed debug APK was produced and contains the expected ARM64 JNI library.
It does not verify installation or runtime behavior on a physical Android device, Vulkan
format support on that device, or game rendering/playability.
