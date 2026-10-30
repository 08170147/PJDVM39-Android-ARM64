#version 450
layout(set = 0, binding = 0) uniform sampler2D bc5Texture;
layout(location = 0) in vec2 vUV;
layout(location = 0) out vec4 outColor;

void main() {
    vec2 channels = texture(bc5Texture, vUV).rg;
    // Diagnostic view: BC5's two channels are displayed as red and green.
    outColor = vec4(channels.r, channels.g, 0.0, 1.0);
}
