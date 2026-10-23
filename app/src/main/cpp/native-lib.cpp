#include <jni.h>
#include <android/log.h>
#include <string>

#define LOG_TAG "PJDVM39Port"

extern "C" JNIEXPORT jstring JNICALL
Java_com_local_pjdvm39_MainActivity_nativeGetReport(JNIEnv* env, jclass) {
    const std::string report =
        "PJDV M39 Android ARM64 port skeleton\n\n"
        "Status: JNI/build scaffold only. The original game renderer is NOT ported.\n"
        "Target ABI: arm64-v8a\n"
        "Vulkan surface clear/present routine: pending integration.\n"
        "No game data is bundled with this skeleton.\n";
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Native report requested");
    return env->NewStringUTF(report.c_str());
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_local_pjdvm39_MainActivity_nativeRenderFrame(JNIEnv* env, jclass, jobject, jint, jint) {
    const char* message =
        "Vulkan frame test is not implemented in this GitHub scaffold yet. "
        "Integrate and validate the Vulkan surface/swapchain implementation before device testing.";
    return env->NewStringUTF(message);
}
