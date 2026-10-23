import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "app" / "build" / "intermediates"
ANDROID = "{http://schemas.android.com/apk/res/android}"
checks = []

def check(name, condition, detail=""):
    checks.append((name, bool(condition), detail))

def report():
    passed = sum(ok for _, ok, _ in checks)
    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        if detail:
            print(f"       {detail}")
    print(f"\n結果：{passed}/{len(checks)} 項通過")
    failed = [name for name, ok, _ in checks if not ok]
    if failed:
        print("驗證失敗項目：" + "；".join(failed))
        return 1
    print("合併 Manifest 驗證通過。")
    return 0

def main():
    candidates = []
    for folder_name in ("merged_manifest", "merged_manifests"):
        folder = BUILD / folder_name / "debug"
        if folder.is_dir():
            candidates.extend(folder.rglob("AndroidManifest.xml"))

    candidates = [
        path for path in candidates
        if path.is_file() and "debug" in path.parts
    ]

    if not candidates:
        check(
            "找到建置後合併 Manifest",
            False,
            "未找到 app/build/intermediates/merged_manifest(s)/debug/**/AndroidManifest.xml"
        )
        return report()

    manifest = max(candidates, key=lambda path: path.stat().st_mtime)
    check("找到建置後合併 Manifest", True, str(manifest.relative_to(ROOT)))

    try:
        root = ET.parse(manifest).getroot()
        check("合併 Manifest XML 格式有效", root.tag == "manifest")
    except (ET.ParseError, OSError) as exc:
        check("合併 Manifest XML 格式有效", False, str(exc))
        return report()

    application = root.find("application")
    check("Application 節點存在", application is not None)

    if application is not None:
        check(
            "Application label 存在",
            bool(application.get(ANDROID + "label"))
        )

        activities = application.findall("activity")
        launcher = None
        for activity in activities:
            name = activity.get(ANDROID + "name", "")
            if name not in (
                "com.local.pjdvm39.MainActivity",
                ".MainActivity",
                "MainActivity",
            ):
                continue

            for intent_filter in activity.findall("intent-filter"):
                actions = {
                    item.get(ANDROID + "name")
                    for item in intent_filter.findall("action")
                }
                categories = {
                    item.get(ANDROID + "name")
                    for item in intent_filter.findall("category")
                }
                if (
                    "android.intent.action.MAIN" in actions
                    and "android.intent.category.LAUNCHER" in categories
                ):
                    launcher = activity
                    break
            if launcher is not None:
                break

        check("Launcher MainActivity 已合併", launcher is not None)
        if launcher is not None:
            check(
                "Launcher Activity exported=true",
                launcher.get(ANDROID + "exported") == "true"
            )
        else:
            check("Launcher Activity exported=true", False)

    features = root.findall("uses-feature")
    vulkan = any(
        feature.get(ANDROID + "name") == "android.hardware.vulkan.version"
        and feature.get(ANDROID + "version") == "0x00400000"
        for feature in features
    )
    check("Vulkan 1.0 功能宣告存在", vulkan)

    return report()

if __name__ == "__main__":
    sys.exit(main())
