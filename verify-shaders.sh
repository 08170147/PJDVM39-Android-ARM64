#!/usr/bin/env bash
set -euo pipefail
command -v glslangValidator >/dev/null || { echo "glslangValidator is required" >&2; exit 2; }
command -v spirv-val >/dev/null || { echo "spirv-val is required" >&2; exit 2; }
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
glslangValidator -V --target-env vulkan1.0 -S vert shaders/bc5_sample.vert -o "$tmp/bc5_sample.vert.spv"
glslangValidator -V --target-env vulkan1.0 -S frag shaders/bc5_sample.frag -o "$tmp/bc5_sample.frag.spv"
spirv-val --target-env vulkan1.0 "$tmp/bc5_sample.vert.spv"
spirv-val --target-env vulkan1.0 "$tmp/bc5_sample.frag.spv"
echo "PASS: BC5 diagnostic vertex/fragment shaders compile and validate for Vulkan 1.0"
