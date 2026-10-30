#include <jni.h>
#include <android/log.h>
#include <android/native_window_jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#define VK_USE_PLATFORM_ANDROID_KHR 1
#include <vulkan/vulkan.h>
#include <vulkan/vulkan_android.h>
#include <algorithm>
#include <cstring>
#include <sstream>
#include <string>
#include <vector>

#define LOG_TAG "PJDVM39Port"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)


static std::string uploadBc5Fixture(VkPhysicalDevice physical, VkDevice device, VkQueue queue, uint32_t family) {
    std::ostringstream out;
    VkFormatProperties fp{};
    vkGetPhysicalDeviceFormatProperties(physical, VK_FORMAT_BC5_UNORM_BLOCK, &fp);
    const auto required = VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT | VK_FORMAT_FEATURE_TRANSFER_DST_BIT;
    if ((fp.optimalTilingFeatures & required) != required) return "BC5 upload fixture: SKIP (format features unavailable)\n";
    VkBuffer buffer = VK_NULL_HANDLE; VkDeviceMemory bufferMem = VK_NULL_HANDLE;
    VkImage image = VK_NULL_HANDLE; VkDeviceMemory imageMem = VK_NULL_HANDLE;
    VkCommandPool pool = VK_NULL_HANDLE; VkFence fence = VK_NULL_HANDLE;
    VkImageView imageView = VK_NULL_HANDLE; VkSampler sampler = VK_NULL_HANDLE;
    VkDescriptorSetLayout descriptorLayout = VK_NULL_HANDLE; VkDescriptorPool descriptorPool = VK_NULL_HANDLE;
    bool passed = false;
    auto memType = [&](uint32_t bits, VkMemoryPropertyFlags flags, uint32_t& index) {
        VkPhysicalDeviceMemoryProperties p{}; vkGetPhysicalDeviceMemoryProperties(physical, &p);
        for (uint32_t i=0;i<p.memoryTypeCount;i++) if ((bits&(1u<<i)) && (p.memoryTypes[i].propertyFlags&flags)==flags) { index=i; return true; }
        return false;
    };
    auto err = [&](const char* op, VkResult r) { out << "BC5 upload fixture: " << op << " failed VkResult=" << int(r) << "\n"; };
    do {
        const uint8_t block[16] = {255,0,0,0,0,0,0,0, 255,0,0,0,0,0,0,0};
        VkBufferCreateInfo b{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO}; b.size=16; b.usage=VK_BUFFER_USAGE_TRANSFER_SRC_BIT; b.sharingMode=VK_SHARING_MODE_EXCLUSIVE;
        VkResult r=vkCreateBuffer(device,&b,nullptr,&buffer); if(r!=VK_SUCCESS){err("vkCreateBuffer",r);break;}
        VkMemoryRequirements br{}; vkGetBufferMemoryRequirements(device,buffer,&br);
        uint32_t mt=0; if(!memType(br.memoryTypeBits,VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,mt)){out<<"BC5 upload fixture: no coherent host memory\n";break;}
        VkMemoryAllocateInfo ma{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO}; ma.allocationSize=br.size; ma.memoryTypeIndex=mt;
        r=vkAllocateMemory(device,&ma,nullptr,&bufferMem); if(r!=VK_SUCCESS){err("staging allocate",r);break;}
        r=vkBindBufferMemory(device,buffer,bufferMem,0); if(r!=VK_SUCCESS){err("bind staging",r);break;}
        void* data=nullptr; r=vkMapMemory(device,bufferMem,0,16,0,&data); if(r!=VK_SUCCESS){err("map staging",r);break;}
        memcpy(data,block,16); vkUnmapMemory(device,bufferMem);

        VkImageCreateInfo ii{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO}; ii.imageType=VK_IMAGE_TYPE_2D; ii.format=VK_FORMAT_BC5_UNORM_BLOCK;
        ii.extent={4,4,1}; ii.mipLevels=1; ii.arrayLayers=1; ii.samples=VK_SAMPLE_COUNT_1_BIT; ii.tiling=VK_IMAGE_TILING_OPTIMAL;
        ii.usage=VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_SAMPLED_BIT; ii.sharingMode=VK_SHARING_MODE_EXCLUSIVE;
        r=vkCreateImage(device,&ii,nullptr,&image); if(r!=VK_SUCCESS){err("vkCreateImage BC5",r);break;}
        VkMemoryRequirements ir{}; vkGetImageMemoryRequirements(device,image,&ir);
        if(!memType(ir.memoryTypeBits,VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,mt)){out<<"BC5 upload fixture: no device-local image memory\n";break;}
        ma.allocationSize=ir.size; ma.memoryTypeIndex=mt;
        r=vkAllocateMemory(device,&ma,nullptr,&imageMem); if(r!=VK_SUCCESS){err("image allocate",r);break;}
        r=vkBindImageMemory(device,image,imageMem,0); if(r!=VK_SUCCESS){err("bind image",r);break;}

        VkCommandPoolCreateInfo pc{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO}; pc.queueFamilyIndex=family;
        r=vkCreateCommandPool(device,&pc,nullptr,&pool); if(r!=VK_SUCCESS){err("command pool",r);break;}
        VkCommandBuffer cmd=VK_NULL_HANDLE; VkCommandBufferAllocateInfo ac{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
        ac.commandPool=pool; ac.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY; ac.commandBufferCount=1;
        r=vkAllocateCommandBuffers(device,&ac,&cmd); if(r!=VK_SUCCESS){err("allocate command buffer",r);break;}
        VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO}; begin.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        r=vkBeginCommandBuffer(cmd,&begin); if(r!=VK_SUCCESS){err("begin command buffer",r);break;}
        VkImageMemoryBarrier toDst{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER}; toDst.dstAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;
        toDst.oldLayout=VK_IMAGE_LAYOUT_UNDEFINED; toDst.newLayout=VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
        toDst.srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED; toDst.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED; toDst.image=image;
        toDst.subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1};
        vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,0,0,nullptr,0,nullptr,1,&toDst);
        VkBufferImageCopy region{}; region.imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0,0,1}; region.imageExtent={4,4,1};
        vkCmdCopyBufferToImage(cmd,buffer,image,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1,&region);
        VkImageMemoryBarrier toRead{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER}; toRead.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;
        toRead.dstAccessMask=VK_ACCESS_SHADER_READ_BIT; toRead.oldLayout=VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
        toRead.newLayout=VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL; toRead.srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;
        toRead.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED; toRead.image=image; toRead.subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1};
        vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,0,0,nullptr,0,nullptr,1,&toRead);
        r=vkEndCommandBuffer(cmd); if(r!=VK_SUCCESS){err("end command buffer",r);break;}
        VkFenceCreateInfo fc{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO}; r=vkCreateFence(device,&fc,nullptr,&fence); if(r!=VK_SUCCESS){err("fence",r);break;}
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO}; si.commandBufferCount=1; si.pCommandBuffers=&cmd;
        r=vkQueueSubmit(queue,1,&si,fence); if(r!=VK_SUCCESS){err("queue submit",r);break;}
        r=vkWaitForFences(device,1,&fence,VK_TRUE,UINT64_MAX); if(r!=VK_SUCCESS){err("wait fence",r);break;}
        VkImageViewCreateInfo viewInfo{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};
        viewInfo.image = image; viewInfo.viewType = VK_IMAGE_VIEW_TYPE_2D; viewInfo.format = VK_FORMAT_BC5_UNORM_BLOCK;
        viewInfo.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
        r = vkCreateImageView(device, &viewInfo, nullptr, &imageView);
        if (r != VK_SUCCESS) { err("vkCreateImageView BC5", r); break; }

        VkSamplerCreateInfo samplerInfo{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};
        samplerInfo.magFilter = VK_FILTER_NEAREST; samplerInfo.minFilter = VK_FILTER_NEAREST;
        samplerInfo.mipmapMode = VK_SAMPLER_MIPMAP_MODE_NEAREST;
        samplerInfo.addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        samplerInfo.addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        samplerInfo.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        samplerInfo.maxAnisotropy = 1.0f; samplerInfo.minLod = 0.0f; samplerInfo.maxLod = 0.0f;
        r = vkCreateSampler(device, &samplerInfo, nullptr, &sampler);
        if (r != VK_SUCCESS) { err("vkCreateSampler BC5", r); break; }

        VkDescriptorSetLayoutBinding binding{};
        binding.binding = 0;
        binding.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
        binding.descriptorCount = 1;
        binding.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
        VkDescriptorSetLayoutCreateInfo layoutInfo{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
        layoutInfo.bindingCount = 1;
        layoutInfo.pBindings = &binding;
        r = vkCreateDescriptorSetLayout(device, &layoutInfo, nullptr, &descriptorLayout);
        if (r != VK_SUCCESS) { err("vkCreateDescriptorSetLayout BC5", r); break; }

        VkDescriptorPoolSize poolSize{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1};
        VkDescriptorPoolCreateInfo poolInfo{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
        poolInfo.maxSets = 1;
        poolInfo.poolSizeCount = 1;
        poolInfo.pPoolSizes = &poolSize;
        r = vkCreateDescriptorPool(device, &poolInfo, nullptr, &descriptorPool);
        if (r != VK_SUCCESS) { err("vkCreateDescriptorPool BC5", r); break; }

        VkDescriptorSet descriptorSet = VK_NULL_HANDLE;
        VkDescriptorSetAllocateInfo setInfo{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
        setInfo.descriptorPool = descriptorPool;
        setInfo.descriptorSetCount = 1;
        setInfo.pSetLayouts = &descriptorLayout;
        r = vkAllocateDescriptorSets(device, &setInfo, &descriptorSet);
        if (r != VK_SUCCESS) { err("vkAllocateDescriptorSets BC5", r); break; }

        VkDescriptorImageInfo imageInfo{};
        imageInfo.sampler = sampler;
        imageInfo.imageView = imageView;
        imageInfo.imageLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
        VkWriteDescriptorSet write{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};
        write.dstSet = descriptorSet;
        write.dstBinding = 0;
        write.descriptorCount = 1;
        write.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
        write.pImageInfo = &imageInfo;
        vkUpdateDescriptorSets(device, 1, &write, 0, nullptr);

        passed=true;
        out<<"PASS: BC5 upload, image view, sampler and combined-image-sampler descriptor set created; shader sampling not yet tested\n";
    } while(false);
    if(device) vkDeviceWaitIdle(device);
    if(descriptorPool) vkDestroyDescriptorPool(device,descriptorPool,nullptr);
    if(descriptorLayout) vkDestroyDescriptorSetLayout(device,descriptorLayout,nullptr);
    if(sampler) vkDestroySampler(device,sampler,nullptr);
    if(imageView) vkDestroyImageView(device,imageView,nullptr);
    if(fence) vkDestroyFence(device,fence,nullptr);
    if(pool) vkDestroyCommandPool(device,pool,nullptr);
    if(image) vkDestroyImage(device,image,nullptr);
    if(imageMem) vkFreeMemory(device,imageMem,nullptr);
    if(buffer) vkDestroyBuffer(device,buffer,nullptr);
    if(bufferMem) vkFreeMemory(device,bufferMem,nullptr);
    if(!passed && out.str().empty()) out<<"BC5 upload fixture: FAILED\n";
    return out.str();
}


static bool readSpirvAsset(AAssetManager* manager, const char* path, std::vector<uint32_t>& words, std::string& error) {
    if (!manager) { error = "AssetManager unavailable"; return false; }
    AAsset* asset = AAssetManager_open(manager, path, AASSET_MODE_BUFFER);
    if (!asset) { error = std::string("asset not found: ") + path; return false; }
    const off_t length = AAsset_getLength(asset);
    if (length < 20 || (length % 4) != 0) {
        AAsset_close(asset); error = std::string("invalid SPIR-V byte length: ") + path; return false;
    }
    words.resize(static_cast<size_t>(length) / sizeof(uint32_t));
    const int bytesRead = AAsset_read(asset, words.data(), static_cast<size_t>(length));
    AAsset_close(asset);
    if (bytesRead != length) { words.clear(); error = std::string("short read: ") + path; return false; }
    if (words[0] != 0x07230203u) { words.clear(); error = std::string("bad SPIR-V magic: ") + path; return false; }
    return true;
}

static std::string renderOneFrame(ANativeWindow* window, uint32_t requestedWidth, uint32_t requestedHeight, AAssetManager* assets) {
    std::ostringstream out;
    if (!window) return "ANativeWindow_fromSurface failed.\n";
    VkInstance instance = VK_NULL_HANDLE;
    VkSurfaceKHR surface = VK_NULL_HANDLE;
    VkDevice device = VK_NULL_HANDLE;
    VkShaderModule vertexShaderModule = VK_NULL_HANDLE, fragmentShaderModule = VK_NULL_HANDLE;
    VkSwapchainKHR swapchain = VK_NULL_HANDLE;
    VkRenderPass renderPass = VK_NULL_HANDLE;
    VkDescriptorSetLayout sampleSetLayout = VK_NULL_HANDLE;
    VkPipelineLayout samplePipelineLayout = VK_NULL_HANDLE;
    VkPipeline samplePipeline = VK_NULL_HANDLE;
    VkCommandPool commandPool = VK_NULL_HANDLE;
    VkSemaphore acquired = VK_NULL_HANDLE, rendered = VK_NULL_HANDLE;
    VkFence fence = VK_NULL_HANDLE;
    std::vector<VkImageView> views;
    std::vector<VkFramebuffer> framebuffers;
    std::vector<VkCommandBuffer> commands;
    VkQueue queue = VK_NULL_HANDLE;
    auto check = [&](VkResult r, const char* label) {
        if (r != VK_SUCCESS) { out << label << " failed: VkResult=" << static_cast<int>(r) << "\n"; return false; }
        out << label << ": OK\n"; return true;
    };
    do {
        uint32_t extCount = 0;
        if (!check(vkEnumerateInstanceExtensionProperties(nullptr, &extCount, nullptr), "instance extension count")) break;
        std::vector<VkExtensionProperties> exts(extCount);
        if (!check(vkEnumerateInstanceExtensionProperties(nullptr, &extCount, exts.data()), "instance extension list")) break;
        bool surfaceExt = false, androidExt = false;
        for (const auto& e : exts) {
            surfaceExt |= std::string(e.extensionName) == VK_KHR_SURFACE_EXTENSION_NAME;
            androidExt |= std::string(e.extensionName) == VK_KHR_ANDROID_SURFACE_EXTENSION_NAME;
        }
        if (!surfaceExt || !androidExt) { out << "Required Android Vulkan surface extensions unavailable.\n"; break; }
        const char* instanceExts[] = { VK_KHR_SURFACE_EXTENSION_NAME, VK_KHR_ANDROID_SURFACE_EXTENSION_NAME };
        VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
        app.pApplicationName = "PJDVM39 Vulkan Clear Test"; app.applicationVersion = 1;
        app.pEngineName = "PJDVM39Port"; app.engineVersion = 1; app.apiVersion = VK_API_VERSION_1_0;
        VkInstanceCreateInfo ici{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
        ici.pApplicationInfo = &app; ici.enabledExtensionCount = 2; ici.ppEnabledExtensionNames = instanceExts;
        if (!check(vkCreateInstance(&ici, nullptr, &instance), "vkCreateInstance")) break;
        VkAndroidSurfaceCreateInfoKHR sci{VK_STRUCTURE_TYPE_ANDROID_SURFACE_CREATE_INFO_KHR}; sci.window = window;
        if (!check(vkCreateAndroidSurfaceKHR(instance, &sci, nullptr, &surface), "vkCreateAndroidSurfaceKHR")) break;
        uint32_t physicalCount = 0;
        if (!check(vkEnumeratePhysicalDevices(instance, &physicalCount, nullptr), "physical device count") || physicalCount == 0) { out << "No Vulkan physical devices.\n"; break; }
        std::vector<VkPhysicalDevice> physicals(physicalCount);
        if (!check(vkEnumeratePhysicalDevices(instance, &physicalCount, physicals.data()), "physical device list")) break;
        VkPhysicalDevice physical = VK_NULL_HANDLE;
        uint32_t family = 0;
        for (auto candidate : physicals) {
            uint32_t qCount = 0; vkGetPhysicalDeviceQueueFamilyProperties(candidate, &qCount, nullptr);
            std::vector<VkQueueFamilyProperties> qs(qCount);
            vkGetPhysicalDeviceQueueFamilyProperties(candidate, &qCount, qs.data());
            for (uint32_t q = 0; q < qCount; ++q) {
                VkBool32 present = VK_FALSE;
                if (vkGetPhysicalDeviceSurfaceSupportKHR(candidate, q, surface, &present) == VK_SUCCESS &&
                    present && (qs[q].queueFlags & VK_QUEUE_GRAPHICS_BIT)) { physical = candidate; family = q; break; }
            }
            if (physical) break;
        }
        if (!physical) { out << "No graphics queue supports presentation to this Android surface.\n"; break; }
        VkPhysicalDeviceProperties props{}; vkGetPhysicalDeviceProperties(physical, &props);
        out << "GPU: " << props.deviceName << "; queue family=" << family << "\n";
        uint32_t devExtCount = 0;
        if (vkEnumerateDeviceExtensionProperties(physical, nullptr, &devExtCount, nullptr) != VK_SUCCESS) { out << "Device extension enumeration failed.\n"; break; }
        std::vector<VkExtensionProperties> devExts(devExtCount);
        if (vkEnumerateDeviceExtensionProperties(physical, nullptr, &devExtCount, devExts.data()) != VK_SUCCESS) { out << "Device extension listing failed.\n"; break; }
        bool swapchainExt = false;
        for (const auto& e : devExts) swapchainExt |= std::string(e.extensionName) == VK_KHR_SWAPCHAIN_EXTENSION_NAME;
        if (!swapchainExt) { out << "VK_KHR_swapchain unavailable.\n"; break; }
        float priority = 1.0f;
        VkDeviceQueueCreateInfo qci{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
        qci.queueFamilyIndex = family; qci.queueCount = 1; qci.pQueuePriorities = &priority;
        const char* deviceExts[] = { VK_KHR_SWAPCHAIN_EXTENSION_NAME };
        VkDeviceCreateInfo dci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
        dci.queueCreateInfoCount = 1; dci.pQueueCreateInfos = &qci; dci.enabledExtensionCount = 1; dci.ppEnabledExtensionNames = deviceExts;
        if (!check(vkCreateDevice(physical, &dci, nullptr, &device), "vkCreateDevice")) break;
        vkGetDeviceQueue(device, family, 0, &queue);
        out << uploadBc5Fixture(physical, device, queue, family);

        std::vector<uint32_t> vertexSpirv, fragmentSpirv;
        std::string assetError;
        const bool vertexLoaded = readSpirvAsset(assets, "pjdvm39/bc5_sample.vert.spv", vertexSpirv, assetError);
        if (!vertexLoaded) out << "Vertex SPIR-V asset: FAIL (" << assetError << ")\\n";
        else out << "Vertex SPIR-V asset: PASS (" << vertexSpirv.size() * 4 << " bytes)\\n";
        assetError.clear();
        const bool fragmentLoaded = readSpirvAsset(assets, "pjdvm39/bc5_sample.frag.spv", fragmentSpirv, assetError);
        if (!fragmentLoaded) out << "Fragment SPIR-V asset: FAIL (" << assetError << ")\\n";
        else out << "Fragment SPIR-V asset: PASS (" << fragmentSpirv.size() * 4 << " bytes)\\n";
        if (vertexLoaded && fragmentLoaded) {
            VkShaderModuleCreateInfo sm{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
            sm.codeSize = vertexSpirv.size() * sizeof(uint32_t); sm.pCode = vertexSpirv.data();
            VkResult shaderResult = vkCreateShaderModule(device, &sm, nullptr, &vertexShaderModule);
            if (shaderResult != VK_SUCCESS) out << "Vertex vkCreateShaderModule: FAIL VkResult=" << int(shaderResult) << "\\n";
            else {
                sm.codeSize = fragmentSpirv.size() * sizeof(uint32_t); sm.pCode = fragmentSpirv.data();
                shaderResult = vkCreateShaderModule(device, &sm, nullptr, &fragmentShaderModule);
                if (shaderResult != VK_SUCCESS) out << "Fragment vkCreateShaderModule: FAIL VkResult=" << int(shaderResult) << "\\n";
                else out << "PASS: both SPIR-V modules accepted by Vulkan vkCreateShaderModule; pipeline/draw not yet tested\\n";
            }
        }
        VkSurfaceCapabilitiesKHR caps{};
        if (!check(vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physical, surface, &caps), "surface capabilities")) break;
        uint32_t formatCount = 0;
        if (!check(vkGetPhysicalDeviceSurfaceFormatsKHR(physical, surface, &formatCount, nullptr), "surface format count") || !formatCount) { out << "No surface formats.\n"; break; }
        std::vector<VkSurfaceFormatKHR> formats(formatCount);
        if (!check(vkGetPhysicalDeviceSurfaceFormatsKHR(physical, surface, &formatCount, formats.data()), "surface formats")) break;
        VkSurfaceFormatKHR chosen = formats[0];
        for (const auto& f : formats) if ((f.format == VK_FORMAT_R8G8B8A8_UNORM || f.format == VK_FORMAT_B8G8R8A8_UNORM) && f.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR) { chosen = f; break; }
        VkExtent2D extent = caps.currentExtent;
        if (extent.width == UINT32_MAX) {
            extent.width = std::max(caps.minImageExtent.width, std::min(caps.maxImageExtent.width, requestedWidth));
            extent.height = std::max(caps.minImageExtent.height, std::min(caps.maxImageExtent.height, requestedHeight));
        }
        if (!extent.width || !extent.height || !(caps.supportedUsageFlags & VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT)) { out << "Surface extent/usage is not renderable.\n"; break; }
        uint32_t imageCount = caps.minImageCount + 1;
        if (caps.maxImageCount && imageCount > caps.maxImageCount) imageCount = caps.maxImageCount;
        VkSwapchainCreateInfoKHR sw{VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR};
        sw.surface = surface; sw.minImageCount = imageCount; sw.imageFormat = chosen.format; sw.imageColorSpace = chosen.colorSpace;
        sw.imageExtent = extent; sw.imageArrayLayers = 1; sw.imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
        sw.imageSharingMode = VK_SHARING_MODE_EXCLUSIVE; sw.preTransform = caps.currentTransform;
        if (caps.supportedCompositeAlpha & VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR) sw.compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR;
        else if (caps.supportedCompositeAlpha & VK_COMPOSITE_ALPHA_INHERIT_BIT_KHR) sw.compositeAlpha = VK_COMPOSITE_ALPHA_INHERIT_BIT_KHR;
        else if (caps.supportedCompositeAlpha & VK_COMPOSITE_ALPHA_PRE_MULTIPLIED_BIT_KHR) sw.compositeAlpha = VK_COMPOSITE_ALPHA_PRE_MULTIPLIED_BIT_KHR;
        else sw.compositeAlpha = VK_COMPOSITE_ALPHA_POST_MULTIPLIED_BIT_KHR;
        sw.presentMode = VK_PRESENT_MODE_FIFO_KHR; sw.clipped = VK_TRUE;
        if (!check(vkCreateSwapchainKHR(device, &sw, nullptr, &swapchain), "vkCreateSwapchainKHR")) break;
        uint32_t n = 0;
        if (!check(vkGetSwapchainImagesKHR(device, swapchain, &n, nullptr), "swapchain image count") || !n) { out << "No swapchain images.\n"; break; }
        std::vector<VkImage> images(n);
        if (!check(vkGetSwapchainImagesKHR(device, swapchain, &n, images.data()), "swapchain images")) break;
        views.resize(n, VK_NULL_HANDLE); framebuffers.resize(n, VK_NULL_HANDLE); commands.resize(n, VK_NULL_HANDLE);
        for (uint32_t i = 0; i < n; ++i) {
            VkImageViewCreateInfo vi{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};
            vi.image = images[i]; vi.viewType = VK_IMAGE_VIEW_TYPE_2D; vi.format = chosen.format;
            vi.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT; vi.subresourceRange.levelCount = 1; vi.subresourceRange.layerCount = 1;
            if (!check(vkCreateImageView(device, &vi, nullptr, &views[i]), "vkCreateImageView")) break;
        }
        bool allViews = std::all_of(views.begin(), views.end(), [](VkImageView v){ return v != VK_NULL_HANDLE; });
        if (!allViews) break;
        VkAttachmentDescription att{}; att.format = chosen.format; att.samples = VK_SAMPLE_COUNT_1_BIT;
        att.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR; att.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
        att.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE; att.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
        att.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED; att.finalLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
        VkAttachmentReference ar{0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL};
        VkSubpassDescription sub{}; sub.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS; sub.colorAttachmentCount = 1; sub.pColorAttachments = &ar;
        VkRenderPassCreateInfo rp{VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO}; rp.attachmentCount = 1; rp.pAttachments = &att; rp.subpassCount = 1; rp.pSubpasses = &sub;
        if (!check(vkCreateRenderPass(device, &rp, nullptr, &renderPass), "vkCreateRenderPass")) break;

        // Match set=0,binding=0 combined sampler declared by bc5_sample.frag.
        VkDescriptorSetLayoutBinding sampleBinding{};
        sampleBinding.binding = 0;
        sampleBinding.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
        sampleBinding.descriptorCount = 1;
        sampleBinding.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
        VkDescriptorSetLayoutCreateInfo sampleSetInfo{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
        sampleSetInfo.bindingCount = 1;
        sampleSetInfo.pBindings = &sampleBinding;
        if (!check(vkCreateDescriptorSetLayout(device, &sampleSetInfo, nullptr, &sampleSetLayout),
                   "vkCreateDescriptorSetLayout sample")) break;

        VkPipelineLayoutCreateInfo pipelineLayoutInfo{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
        pipelineLayoutInfo.setLayoutCount = 1;
        pipelineLayoutInfo.pSetLayouts = &sampleSetLayout;
        if (!check(vkCreatePipelineLayout(device, &pipelineLayoutInfo, nullptr, &samplePipelineLayout),
                   "vkCreatePipelineLayout sample")) break;

        VkPipelineShaderStageCreateInfo shaderStages[2]{};
        shaderStages[0].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        shaderStages[0].stage = VK_SHADER_STAGE_VERTEX_BIT;
        shaderStages[0].module = vertexShaderModule;
        shaderStages[0].pName = "main";
        shaderStages[1].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        shaderStages[1].stage = VK_SHADER_STAGE_FRAGMENT_BIT;
        shaderStages[1].module = fragmentShaderModule;
        shaderStages[1].pName = "main";

        VkPipelineVertexInputStateCreateInfo vertexInput{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
        VkPipelineInputAssemblyStateCreateInfo inputAssembly{VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};
        inputAssembly.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
        VkViewport viewport{};
        viewport.width = static_cast<float>(extent.width);
        viewport.height = static_cast<float>(extent.height);
        viewport.minDepth = 0.0f;
        viewport.maxDepth = 1.0f;
        VkRect2D scissor{{0, 0}, extent};
        VkPipelineViewportStateCreateInfo viewportState{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};
        viewportState.viewportCount = 1;
        viewportState.pViewports = &viewport;
        viewportState.scissorCount = 1;
        viewportState.pScissors = &scissor;
        VkPipelineRasterizationStateCreateInfo raster{VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};
        raster.polygonMode = VK_POLYGON_MODE_FILL;
        raster.cullMode = VK_CULL_MODE_NONE;
        raster.frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE;
        raster.lineWidth = 1.0f;
        VkPipelineMultisampleStateCreateInfo multisample{VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};
        multisample.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
        VkPipelineColorBlendAttachmentState blendAttachment{};
        blendAttachment.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                                          VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;
        VkPipelineColorBlendStateCreateInfo blend{VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};
        blend.attachmentCount = 1;
        blend.pAttachments = &blendAttachment;
        VkGraphicsPipelineCreateInfo pipelineInfo{VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO};
        pipelineInfo.stageCount = 2;
        pipelineInfo.pStages = shaderStages;
        pipelineInfo.pVertexInputState = &vertexInput;
        pipelineInfo.pInputAssemblyState = &inputAssembly;
        pipelineInfo.pViewportState = &viewportState;
        pipelineInfo.pRasterizationState = &raster;
        pipelineInfo.pMultisampleState = &multisample;
        pipelineInfo.pColorBlendState = &blend;
        pipelineInfo.layout = samplePipelineLayout;
        pipelineInfo.renderPass = renderPass;
        pipelineInfo.subpass = 0;
        if (!check(vkCreateGraphicsPipelines(device, VK_NULL_HANDLE, 1, &pipelineInfo, nullptr, &samplePipeline),
                   "vkCreateGraphicsPipelines BC5 sample")) break;
        out << "PASS: graphics pipeline object created; draw and descriptor binding not yet tested\\n";
        bool allFramebuffers = true;
        for (uint32_t i = 0; i < n; ++i) {
            VkFramebufferCreateInfo fb{VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO};
            fb.renderPass = renderPass; fb.attachmentCount = 1; fb.pAttachments = &views[i]; fb.width = extent.width; fb.height = extent.height; fb.layers = 1;
            if (!check(vkCreateFramebuffer(device, &fb, nullptr, &framebuffers[i]), "vkCreateFramebuffer")) { allFramebuffers = false; break; }
        }
        if (!allFramebuffers) break;
        VkCommandPoolCreateInfo cp{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO}; cp.queueFamilyIndex = family; cp.flags = VK_COMMAND_POOL_CREATE_TRANSIENT_BIT;
        if (!check(vkCreateCommandPool(device, &cp, nullptr, &commandPool), "vkCreateCommandPool")) break;
        VkCommandBufferAllocateInfo ca{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO}; ca.commandPool = commandPool; ca.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY; ca.commandBufferCount = n;
        if (!check(vkAllocateCommandBuffers(device, &ca, commands.data()), "vkAllocateCommandBuffers")) break;
        VkSemaphoreCreateInfo si{VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO};
        if (!check(vkCreateSemaphore(device, &si, nullptr, &acquired), "acquire semaphore") || !check(vkCreateSemaphore(device, &si, nullptr, &rendered), "render semaphore")) break;
        VkFenceCreateInfo fi{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
        if (!check(vkCreateFence(device, &fi, nullptr, &fence), "vkCreateFence")) break;
        uint32_t imageIndex = 0;
        VkResult arq = vkAcquireNextImageKHR(device, swapchain, UINT64_MAX, acquired, VK_NULL_HANDLE, &imageIndex);
        if (arq != VK_SUCCESS && arq != VK_SUBOPTIMAL_KHR) { out << "vkAcquireNextImageKHR failed: VkResult=" << static_cast<int>(arq) << "\n"; break; }
        if (imageIndex >= n) { out << "Acquired image index out of range.\n"; break; }
        VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO}; bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        if (!check(vkBeginCommandBuffer(commands[imageIndex], &bi), "vkBeginCommandBuffer")) break;
        VkClearValue clear{}; clear.color.float32[0] = 0.035f; clear.color.float32[1] = 0.12f; clear.color.float32[2] = 0.24f; clear.color.float32[3] = 1.0f;
        VkRenderPassBeginInfo rbi{VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO}; rbi.renderPass = renderPass; rbi.framebuffer = framebuffers[imageIndex];
        rbi.renderArea.extent = extent; rbi.clearValueCount = 1; rbi.pClearValues = &clear;
        vkCmdBeginRenderPass(commands[imageIndex], &rbi, VK_SUBPASS_CONTENTS_INLINE); vkCmdEndRenderPass(commands[imageIndex]);
        if (!check(vkEndCommandBuffer(commands[imageIndex]), "vkEndCommandBuffer")) break;
        VkPipelineStageFlags waitStage = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
        VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO}; submit.waitSemaphoreCount = 1; submit.pWaitSemaphores = &acquired;
        submit.pWaitDstStageMask = &waitStage; submit.commandBufferCount = 1; submit.pCommandBuffers = &commands[imageIndex];
        submit.signalSemaphoreCount = 1; submit.pSignalSemaphores = &rendered;
        if (!check(vkQueueSubmit(queue, 1, &submit, fence), "vkQueueSubmit") || !check(vkWaitForFences(device, 1, &fence, VK_TRUE, UINT64_MAX), "vkWaitForFences")) break;
        VkPresentInfoKHR pi{VK_STRUCTURE_TYPE_PRESENT_INFO_KHR}; pi.waitSemaphoreCount = 1; pi.pWaitSemaphores = &rendered;
        pi.swapchainCount = 1; pi.pSwapchains = &swapchain; pi.pImageIndices = &imageIndex;
        VkResult pr = vkQueuePresentKHR(queue, &pi);
        if (pr == VK_SUCCESS || pr == VK_SUBOPTIMAL_KHR) out << "PASS: Vulkan frame cleared and presented at " << extent.width << "x" << extent.height << (pr == VK_SUBOPTIMAL_KHR || arq == VK_SUBOPTIMAL_KHR ? " (suboptimal swapchain)" : "") << "\n";
        else out << "vkQueuePresentKHR failed: VkResult=" << static_cast<int>(pr) << "\n";
        VkResult idle = vkQueueWaitIdle(queue); if (idle != VK_SUCCESS) out << "vkQueueWaitIdle failed: VkResult=" << static_cast<int>(idle) << "\n";
    } while (false);
    if (device) vkDeviceWaitIdle(device);
    if (samplePipeline && device) vkDestroyPipeline(device, samplePipeline, nullptr);
    if (samplePipelineLayout && device) vkDestroyPipelineLayout(device, samplePipelineLayout, nullptr);
    if (sampleSetLayout && device) vkDestroyDescriptorSetLayout(device, sampleSetLayout, nullptr);
    if (fragmentShaderModule && device) vkDestroyShaderModule(device, fragmentShaderModule, nullptr);
    if (vertexShaderModule && device) vkDestroyShaderModule(device, vertexShaderModule, nullptr);
    if (commandPool && device) vkDestroyCommandPool(device, commandPool, nullptr);
    for (auto fb : framebuffers) if (fb && device) vkDestroyFramebuffer(device, fb, nullptr);
    if (renderPass && device) vkDestroyRenderPass(device, renderPass, nullptr);
    for (auto view : views) if (view && device) vkDestroyImageView(device, view, nullptr);
    if (fence && device) vkDestroyFence(device, fence, nullptr);
    if (acquired && device) vkDestroySemaphore(device, acquired, nullptr);
    if (rendered && device) vkDestroySemaphore(device, rendered, nullptr);
    if (swapchain && device) vkDestroySwapchainKHR(device, swapchain, nullptr);
    if (device) vkDestroyDevice(device, nullptr);
    if (surface && instance) vkDestroySurfaceKHR(instance, surface, nullptr);
    if (instance) vkDestroyInstance(instance, nullptr);
    return out.str();
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_local_pjdvm39_MainActivity_nativeGetReport(JNIEnv* env, jclass) {
    std::ostringstream out;
    out << "PJDV M39 Android ARM64 port skeleton\n";
    out << "Status: Vulkan surface clear/present smoke test; game renderer is NOT ported.\n";
    out << "Target ABI: arm64-v8a\n";
    out << "The test creates a Vulkan instance, chooses a graphics/present queue, clears one swapchain image, and presents once.\n";
    out << "No game data is bundled with this skeleton.\n";

    VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
    app.pApplicationName = "PJDVM39 format capability probe";
    app.applicationVersion = 1;
    app.pEngineName = "PJDVM39Port";
    app.engineVersion = 1;
    app.apiVersion = VK_API_VERSION_1_0;
    VkInstanceCreateInfo createInfo{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
    createInfo.pApplicationInfo = &app;
    VkInstance instance = VK_NULL_HANDLE;
    VkResult result = vkCreateInstance(&createInfo, nullptr, &instance);
    if (result != VK_SUCCESS) {
        out << "Texture format probe: vkCreateInstance failed, VkResult="
            << static_cast<int>(result) << "\n";
        return env->NewStringUTF(out.str().c_str());
    }

    uint32_t count = 0;
    result = vkEnumeratePhysicalDevices(instance, &count, nullptr);
    if (result != VK_SUCCESS || count == 0) {
        out << "Texture format probe: no Vulkan physical devices; VkResult="
            << static_cast<int>(result) << "\n";
    } else {
        std::vector<VkPhysicalDevice> devices(count);
        result = vkEnumeratePhysicalDevices(instance, &count, devices.data());
        if (result != VK_SUCCESS) {
            out << "Texture format probe: device enumeration failed, VkResult="
                << static_cast<int>(result) << "\n";
        } else {
            for (uint32_t i = 0; i < count; ++i) {
                VkPhysicalDeviceProperties properties{};
                vkGetPhysicalDeviceProperties(devices[i], &properties);
                out << "Texture format probe GPU: " << properties.deviceName << "\n";
                const VkFormat candidates[] = {
                    VK_FORMAT_BC5_UNORM_BLOCK,
                    VK_FORMAT_R8G8_UNORM
                };
                const char* names[] = { "BC5_UNORM_BLOCK", "R8G8_UNORM" };
                for (size_t j = 0; j < 2; ++j) {
                    VkFormatProperties formatProperties{};
                    vkGetPhysicalDeviceFormatProperties(devices[i], candidates[j], &formatProperties);
                    const VkFormatFeatureFlags optimal = formatProperties.optimalTilingFeatures;
                    const bool sampled = (optimal & VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT) != 0;
                    const bool transferDst = (optimal & VK_FORMAT_FEATURE_TRANSFER_DST_BIT) != 0;
                    out << "  " << names[j]
                        << ": sampled=" << (sampled ? "yes" : "no")
                        << ", transfer_dst=" << (transferDst ? "yes" : "no")
                        << ", optimal_features=0x" << std::hex << optimal << std::dec << "\n";
                }
            }
        }
    }
    vkDestroyInstance(instance, nullptr);
    out << "Note: format support is device-specific; this probe does not upload or render TXP textures.\n";
    return env->NewStringUTF(out.str().c_str());
}
extern "C" JNIEXPORT jstring JNICALL
Java_com_local_pjdvm39_MainActivity_nativeRenderFrame(JNIEnv* env, jclass, jobject javaSurface, jint width, jint height, jobject javaAssetManager) {
    ANativeWindow* window = ANativeWindow_fromSurface(env, javaSurface);
    AAssetManager* assets = AAssetManager_fromJava(env, javaAssetManager);
    if (!window) return env->NewStringUTF("ANativeWindow_fromSurface failed.");
    const std::string result = renderOneFrame(window, static_cast<uint32_t>(std::max(0, width)), static_cast<uint32_t>(std::max(0, height)), assets);
    ANativeWindow_release(window);
    LOGI("One-frame Vulkan test finished");
    return env->NewStringUTF(result.c_str());
}
