#!/usr/bin/env bash
set -euo pipefail
command -v glslangValidator >/dev/null || { echo "glslangValidator is required" >&2; exit 2; }
command -v spirv-val >/dev/null || { echo "spirv-val is required" >&2; exit 2; }
out="app/build/generated/assets/pjdvm39"
mkdir -p "$out"
glslangValidator -V --target-env vulkan1.0 -S vert shaders/bc5_sample.vert -o "$out/bc5_sample.vert.spv"
glslangValidator -V --target-env vulkan1.0 -S frag shaders/bc5_sample.frag -o "$out/bc5_sample.frag.spv"
spirv-val --target-env vulkan1.0 "$out/bc5_sample.vert.spv"
spirv-val --target-env vulkan1.0 "$out/bc5_sample.frag.spv"
echo "PASS: BC5 diagnostic shaders compiled, validated and staged as Android assets"
