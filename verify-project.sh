#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
fail=0
for path in settings.gradle build.gradle gradle.properties app/build.gradle app/src/main/AndroidManifest.xml app/src/main/java/com/local/pjdvm39/MainActivity.java app/src/main/cpp/CMakeLists.txt app/src/main/cpp/native-lib.cpp; do
  if [[ ! -f "$ROOT/$path" ]]; then echo "MISSING: $path"; fail=1; fi
done
grep -q "arm64-v8a" "$ROOT/app/build.gradle" || { echo "Missing arm64-v8a ABI filter"; fail=1; }
grep -q "nativeGetReport" "$ROOT/app/src/main/java/com/local/pjdvm39/MainActivity.java" || { echo "Missing JNI report method"; fail=1; }
grep -q "nativeRenderFrame" "$ROOT/app/src/main/java/com/local/pjdvm39/MainActivity.java" || { echo "Missing JNI render method"; fail=1; }
if [[ "$fail" -ne 0 ]]; then exit 1; fi
echo "Project structure checks passed."
echo "Project structure checks passed. Build is handled by the dedicated CI build step."
