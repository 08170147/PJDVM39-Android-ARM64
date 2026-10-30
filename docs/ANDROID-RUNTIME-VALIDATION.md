# Android ARM64 Runtime Validation

This checklist validates the current smoke-test APK on a physical Android device. A successful CI build proves compilation, JNI packaging, and manifest merge; it does not prove Vulkan runtime behavior or game compatibility.

## 1. Install and launch

Use a physical ARM64 Android device with Vulkan support. Enable USB debugging, connect it to a computer with Android Platform Tools, then run:

```sh
adb devices
adb install -r app-debug.apk
adb shell monkey -p com.local.pjdvm39 1
```

If installing the downloaded artifact directly, use its local filename in the `adb install` command.

## 2. Capture the report

The app displays a native capability report and then appends the Vulkan surface test result. Copy the selectable text from the report view, or capture logs:

```sh
adb logcat -c
adb shell monkey -p com.local.pjdvm39 1
adb logcat -d -s PJDVM39Port:I
```

Record the device model, Android version, GPU name, and the complete on-screen report. Do not report only the final success/failure line.

## 3. Expected smoke-test milestones

The Vulkan surface test should report successful completion of the relevant operations, including instance/surface creation, device and queue selection, swapchain creation, image views/framebuffers, command submission, and presentation. The UI should show the expected dark-blue clear color.

A failure at an early milestone is a platform/device initialization issue. A failure after swapchain creation is likely in render setup, synchronization, or presentation. Preserve the exact `VkResult` integer and preceding lines for diagnosis.

## 4. Texture format capability

The native report also queries optimal-tiling support for:

- `VK_FORMAT_BC5_UNORM_BLOCK`
- `VK_FORMAT_R8G8_UNORM`

For each format, capture sampled-image and transfer-destination support. BC5 support is a prerequisite for the direct compressed-texture path, but does not by itself prove that the extracted TXP payload is correctly decoded, laid out, uploaded, or sampled.

If BC5 is unsupported, RG8 is only a candidate fallback after a verified BC5-to-two-channel decode and upload path. Do not interpret format support as proof that the game's textures render correctly.

## 5. Current scope boundary

This APK is a Vulkan/Surface and GPU-format diagnostic shell. It is not yet a playable Android port: the iOS Metal renderer, complete shader translation, game runtime, input/audio integration, and content loading remain unimplemented or unverified.

## Diagnostic report template

```text
Device model:
Android version/API:
GPU:
Vulkan surface test:
BC5 sampled / transfer-dst:
RG8 sampled / transfer-dst:
Full report or log:
```
