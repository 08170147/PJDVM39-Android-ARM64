#version 450
layout(set = 0, binding = 0) uniform sampler2D bc5Texture;
layout(location = 0) in vec2 vUV;
layout(location = 0) out vec4 outColor;

void main() {
    vec2 channels = texture(bc5Texture, vUV).rg;
    // Diagnostic layout: inspect each BC5 channel independently.
    // Left half = R channel in grayscale; right half = G channel in grayscale.
    float value = (vUV.x < 0.5) ? channels.r : channels.g;
    outColor = vec4(value, value, value, 1.0);
}
