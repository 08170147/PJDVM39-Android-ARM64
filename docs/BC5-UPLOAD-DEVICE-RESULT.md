# BC5 Upload Fixture: Physical Device Result

## Verified device result

A physical-device run of the ARM64 diagnostic APK produced the following report:

- GPU: Qualcomm Adreno (TM) 735
- BC5 optimal tiling: sampled image supported; transfer destination supported
- RG8 optimal tiling: sampled image supported; transfer destination supported
- Vulkan surface clear/present: PASS at 3200x800
- BC5 fixture upload: PASS

The BC5 fixture result was:

```text
PASS: 4x4 BC5 block (16 bytes) staged and uploaded; layout UNDEFINED -> TRANSFER_DST -> SHADER_READ_ONLY
```

## What this proves

On this device, the diagnostic successfully:
1. Created a host-visible staging buffer and copied a 16-byte BC5 block into it.
2. Created a 4x4 `VK_FORMAT_BC5_UNORM_BLOCK` optimal-tiled image.
3. Bound device-local image memory.
4. Recorded an image transition from `UNDEFINED` to `TRANSFER_DST_OPTIMAL`.
5. Copied the BC5 block from the staging buffer to the image.
6. Recorded a transition to `SHADER_READ_ONLY_OPTIMAL`.
7. Submitted the command buffer and waited for its fence successfully.

## What this does not prove

This fixture does not yet create an image view, sampler, descriptor set, or shader pipeline to sample and display the BC5 image. It does not load or upload any game TXP asset. The fixture block is synthetic test data, not extracted game texture content.

## Next implementation milestone

Add a minimal Vulkan sampling pipeline for the uploaded BC5 fixture:
- Create an image view and sampler.
- Create a descriptor set layout/pool/set and bind the image sampler.
- Add a minimal vertex/fragment shader pair with a sampled-image binding.
- Draw a fullscreen triangle into the existing swapchain render pass.
- Verify the expected diagnostic color/pattern on the physical device.

After that pipeline is proven, implement the TXP record reader and upload one extracted game texture using the validated BC5 path. Validate format ID, dimensions, block order, channel interpretation, and image orientation before expanding to larger assets.
