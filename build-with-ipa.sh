#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
IPA="${1:-}"
if [[ -z "$IPA" || ! -f "$IPA" ]]; then
  echo "Usage: $0 /path/to/PJDVM39-0.1.5b19-iOS-unsigned.ipa" >&2
  exit 2
fi
# Resolve the IPA before changing to the repository root so relative input paths work.
IPA="$(cd "$(dirname "$IPA")" && pwd)/$(basename "$IPA")"
cd "$ROOT"

ASSET="app/src/main/assets/pjdvm39/exitmenu_2048x2048.bc5"
REPORT="exitmenu-bc5-extract.json"
APK="app/build/outputs/apk/debug/app-debug.apk"

python3 tools/extract_exitmenu_bc5_from_ipa.py "$IPA" --out "$ASSET" --report "$REPORT"
python3 - "$ASSET" "$REPORT" <<'PY'
import hashlib, json, pathlib, sys
asset = pathlib.Path(sys.argv[1])
report = json.loads(pathlib.Path(sys.argv[2]).read_text())
digest = hashlib.sha256(asset.read_bytes()).hexdigest()
assert asset.stat().st_size == 4_194_304, "unexpected BC5 payload size"
assert report.get("payload_sha256") == digest, "extract report SHA-256 mismatch"
print(f"Verified local asset: {asset} ({asset.stat().st_size} bytes)")
print(f"SHA-256: {digest}")
PY

gradle :app:assembleDebug
if [[ ! -f "$APK" ]]; then
  echo "APK was not produced: $APK" >&2
  exit 1
fi
unzip -l "$APK" | grep -F "assets/pjdvm39/exitmenu_2048x2048.bc5" >/dev/null || {
  echo "APK does not contain the extracted ExitMenu asset" >&2
  exit 1
}
echo "PASS: built APK contains the real ExitMenu BC5 candidate."
echo "APK: $APK"
