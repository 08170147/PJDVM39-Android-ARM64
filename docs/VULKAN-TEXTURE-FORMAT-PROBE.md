# Vulkan texture format capability probe

The Android native status report now enumerates Vulkan physical devices and queries
format properties for two candidate texture paths:

- `VK_FORMAT_BC5_UNORM_BLOCK`: direct sampling of the candidate two-channel block-compressed TXP payloads.
- `VK_FORMAT_R8G8_UNORM`: an uncompressed two-channel fallback format, if the source data can be decoded and uploaded in that representation.

For each format the report prints whether optimal tiling supports sampled-image use
and transfer-destination use, plus the raw `optimalTilingFeatures` bit mask.

## Interpretation

A result of `sampled=yes` and `transfer_dst=yes` is a necessary capability signal
for the proposed upload-and-sample path, not proof that the game's TXP payload can
be uploaded unchanged. Before using the BC5 path, the port still needs to validate:

1. the mapping from TXP format ID 11 to BC5 UNORM against a runtime/reference;
2. block order, row/level layout, and any platform-specific swizzle;
3. channel interpretation and shader reconstruction;
4. image creation, memory allocation, staging upload, image barriers, sampler and descriptor binding.

If BC5 sampling is unavailable, RG8 is only a possible fallback after a correct offline
or runtime BC5-to-RG8 decode. The probe does not perform either upload path and does
not render game textures.

## How to inspect

Build and install the Android ARM64 smoke-test APK, launch it on the target device,
and read the native status report below the SurfaceView. The report lists each Vulkan
GPU and both format capability results. Device-specific results must be collected on
the actual target phone; desktop CI cannot establish the phone GPU's format support.
