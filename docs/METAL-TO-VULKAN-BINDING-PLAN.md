# Metal metadata to Vulkan binding plan — Build 19

Input: `PJDVM39-0.1.5b19-iOS-unsigned.ipa`
Scope: read-only aggregation of the shipped shader-map and per-library JSON metadata.
No Metal binaries, executable code, or game archives are copied into this repository.

## Verified coverage

The IPA contains 808 shader-map rows. Each row resolves to a per-library JSON metadata file:

| Stage | Records |
|---|---:|
| Vertex | 404 |
| Fragment/pixel | 404 |
| Total | 808 |
| Missing metadata joins | 0 |

The metadata uses entry point `main0` for all 808 records. This is a metadata observation, not proof that all stages can be compiled by an Android driver.

## Binding inventory

Aggregated from each record's `bindings[].kind`:

| Metadata kind | Count | Candidate Vulkan representation | Confidence |
|---|---:|---|---|
| `tex` | 2,374 | `VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE` | Candidate only |
| `samp_tex` | 2,374 | `VK_DESCRIPTOR_TYPE_SAMPLER` | Candidate only |
| `cbuf` | 2,143 | `VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER` | Candidate only |
| `sbuf` | 6 | `VK_DESCRIPTOR_TYPE_STORAGE_BUFFER` | Candidate only |
| `c1` | 526 | Unresolved constant/bank mapping | Unknown |
| `support` | 51 | Runtime-specific support binding | Unknown |

Counts are occurrences across shader records, not unique descriptor-set bindings and not per-frame descriptor allocation counts. Do not sum them to allocate one global descriptor pool without first grouping by pipeline and reconciling stage visibility and register namespaces.

## Pipeline metadata observations

- Fragment metadata reports 298 records with color target `[0]` and 106 with color targets `[0, 1]`.
- Three records report `raster.depth = true`; the remaining 805 do not.
- Vertex-input array lengths vary: 507 records list zero inputs; 301 list one or more inputs.
- The metadata notes explicitly state that visual and input types still need runtime validation.

## Proposed translation model

For each logical shader package, create a pipeline candidate from its vertex and fragment records. Keep the following as separate unresolved translation steps:

1. **Resource namespaces:** preserve original `kind`, `reg`, `index`, `arg_id`, and MSL argument names in an intermediate representation. Establish whether registers are stage-local or shared before assigning Vulkan set/binding numbers.
2. **Descriptor types:** treat `tex`, `samp_tex`, `cbuf`, and `sbuf` mappings above as hypotheses. Confirm sampled-image/sampler separation, buffer layout, array cardinality, and access flags from actual shader behavior.
3. **Special bindings:** do not silently coerce `c1` or `support` to ordinary descriptors. Trace their producer/consumer semantics first.
4. **Vertex inputs:** reconcile each shader's `vertex_inputs` with the game's vertex stream declarations and formats. An empty metadata list does not prove that the pipeline consumes no vertex data.
5. **Raster/depth/color state:** map target indices, depth behavior, blend state, and attachment formats only after comparing with render-pass/framebuffer setup.
6. **Shader code:** JSON metadata and Metal `.metallib` files do not provide a ready-made Vulkan SPIR-V module. A valid MSL source or a verified translation/decompilation path is still required.

## Recommended first Vulkan proof of concept

Choose one minimal package whose vertex and fragment stages both have simple metadata and few resources. Before implementing it, verify that the pair is used by the same draw path. Then:

- record the exact package/stage/key triplet;
- inspect both JSON metadata records;
- derive a provisional descriptor-set layout without losing original register identity;
- compile or translate shader code through a separately validated route;
- render a known test asset and compare output on-device.

Do not select a shader solely because it has zero bindings; first confirm its actual vertex inputs and draw-state requirements.

## Acceptance criteria

- [ ] Every chosen stage has a traceable source metadata file.
- [ ] Vertex/fragment pairing is confirmed by runtime or package metadata.
- [ ] All resource kinds are understood, including `c1` and `support`.
- [ ] Shader code is converted to valid SPIR-V and passes validation.
- [ ] Descriptor layout and pipeline state match the game's resource/draw path.
- [ ] Visual output is validated on a physical Android ARM64 device.

A complete metadata inventory is not a Vulkan renderer and does not establish that the game can currently run on Android.
