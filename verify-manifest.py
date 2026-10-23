import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
JAVA = ROOT / "app/src/main/java/com/local/pjdvm39/MainActivity.java"
GRADLE = ROOT / "app/build.gradle"

ANDROID = "{http://schemas.android.com/apk/res/android}"
checks = []

def check(name, condition, detail=""):
    checks.append((name, bool(condition), detail))

def main():
    for path in (MANIFEST, JAVA, GRADLE):
        check(
            f"檔案存在：{path.relative_to(ROOT).as_posix()}",
            path.is_file()
        )

    if not all(ok for _, ok, _ in checks):
        return report()

    try:
        tree = ET.parse(MANIFEST)
        root = tree.getroot()
        check("Manifest XML 格式有效", root.tag == "manifest")
    except (ET.ParseError, OSError) as exc:
        check("Manifest XML 格式有效", False, str(exc))
        return report()

    application = root.find("application")
    check("Application 節點存在", application is not None)

    if application is not None:
        check(
            "Application label 存在",
            bool(application.get(ANDROID + "label"))
        )

        activities = application.findall("activity")
        main_activity = next(
            (
                activity for activity in activities
                if activity.get(ANDROID + "name")
                in ("com.local.pjdvm39.MainActivity", ".MainActivity")
            ),
            None
        )
        check("MainActivity 已宣告", main_activity is not None)

        if main_activity is not None:
            check(
                "Activity exported=true",
                main_activity.get(ANDROID + "exported") == "true"
            )
            intent_filters = main_activity.findall("intent-filter")
            has_main = any(
                any(
                    action.get(ANDROID + "name")
                    == "android.intent.action.MAIN"
                    for action in item.findall("action")
                )
                for item in intent_filters
            )
            has_launcher = any(
                any(
                    category.get(ANDROID + "name")
                    == "android.intent.category.LAUNCHER"
                    for category in item.findall("category")
                )
                for item in intent_filters
            )
            check("MAIN 啟動 Action 存在", has_main)
            check("LAUNCHER Category 存在", has_launcher)

    features = root.findall("uses-feature")
    vulkan_feature = any(
        feature.get(ANDROID + "name")
        == "android.hardware.vulkan.version"
        and feature.get(ANDROID + "version")
        == "0x00400000"
        for feature in features
    )
    check("Vulkan 1.0 功能宣告存在", vulkan_feature)

    java_source = JAVA.read_text(encoding="utf-8")
    check(
        "JNI nativeGetReport 宣告存在",
        "nativeGetReport" in java_source
        and "native String nativeGetReport(" in java_source
    )
    check(
        "JNI nativeRenderFrame 宣告存在",
        "nativeRenderFrame" in java_source
        and "native String nativeRenderFrame(" in java_source
    )

    gradle_source = GRADLE.read_text(encoding="utf-8")
    check("ARM64 ABI filter 存在", "arm64-v8a" in gradle_source)

    return report()

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
    print("所有目前定義的靜態檢查均通過。")
    return 0

if __name__ == "__main__":
    sys.exit(main())
